import streamlit as st
from styles import load_styles
import utils
import pandas as pd
import firebase_admin
from firebase_admin import firestore
from urllib.parse import quote 

# 1. Configuración
load_styles()
st.set_page_config(page_title="Resultados y Ranking", layout="wide")
db = firestore.client()

# --- CSS MODERNO PARA TARJETAS Y BOTONES ---
st.markdown("""
<style>
    /* Estilo de Tarjetas */
    .modern-card {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .card-header {
        font-size: 18px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 15px;
        border-bottom: 2px solid #F3F4F6;
        padding-bottom: 10px;
    }
    .step-badge {
        background-color: #E0F2FE;
        color: #0284C7;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 8px;
    }
    /* Ajustes para pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F9FAFB;
        border-radius: 8px 8px 0 0;
        padding: 0 20px;
        border: 1px solid #E5E7EB;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-top: 3px solid #2563EB;
        color: #2563EB;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <h1 class="header-title">🏆 Resultados y Ranking Oficial</h1>
    <p class="header-subtitle">Monitoreo de puntajes, puestos y estadísticas en tiempo real.</p>
</div>
""", unsafe_allow_html=True)

# 2. Cargar Datos
try:
    raw_data = utils.load_data() 
    participantes = raw_data.get("participants", [])
    
    try:
        df_directorio = utils.cargar_directorio_csv()
        total_inscritos = len(df_directorio)
    except:
        df_directorio = pd.DataFrame()
        total_inscritos = 0
        
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    participantes = []
    total_inscritos = 0

# Convertir a DataFrame
if participantes:
    data_list = []
    for p in participantes:
        metricas = p.get("metricas", {})
        hora_entrega = p.get("info_registro", {}).get("hora_entrega", "23:59:59")
        
        data_list.append({
            "DNI": str(p.get("dni", "")).strip(),
            "Estudiante": p.get("nombre"),
            "Colegio": p.get("colegio"), 
            "Grado": p.get("grado"),
            "Categoría": p.get("categoria"),
            "UGEL": p.get("ugel", ""),
            "Gestión": p.get("gestion", ""),
            "Puntaje": metricas.get("total_puntos", 0),
            "Correctas": metricas.get("correctas", 0),
            "Incorrectas": metricas.get("incorrectas", 0),
            "En Blanco": metricas.get("en_blanco", 0),
            "Hora": hora_entrega
        })
    df_resultados = pd.DataFrame(data_list)

    # Cruce de Docentes
    if not df_resultados.empty and not df_directorio.empty and 'docente' in df_directorio.columns:
        df_directorio['dni_key'] = df_directorio['dni'].astype(str).str.strip()
        mapa_docentes = dict(zip(df_directorio['dni_key'], df_directorio['docente']))
        df_resultados['Docente'] = df_resultados['DNI'].map(mapa_docentes).fillna("No registrado")
    elif not df_resultados.empty:
        df_resultados['Docente'] = "No registrado"
        
else:
    df_resultados = pd.DataFrame()

# 3. Métricas Generales
col1, col2, col3, col4 = st.columns(4)
total_evaluados = len(df_resultados)
promedio = df_resultados["Puntaje"].mean() if not df_resultados.empty else 0
max_puntaje = df_resultados["Puntaje"].max() if not df_resultados.empty else 0
avance = (total_evaluados / total_inscritos * 100) if total_inscritos > 0 else 0

with col1:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{total_evaluados}</div><div class="metric-label">Exámenes Procesados</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{promedio:.1f}</div><div class="metric-label">Promedio General</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{max_puntaje}</div><div class="metric-label">Puntaje Más Alto</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{avance:.1f}%</div><div class="metric-label">Avance de Asistencia</div></div>""", unsafe_allow_html=True)

st.write("")

# 4. Tabla y Filtros
st.markdown("### 🥇 Ranking de Mérito")

c_filtro1, c_filtro2, c_export = st.columns([2, 2, 2])

with c_filtro1:
    lista_grados = ["Todos"] + sorted(df_resultados["Grado"].unique().tolist()) if not df_resultados.empty else ["Todos"]
    filtro_grado = st.selectbox("Filtrar por Grado:", lista_grados)

with c_filtro2:
    filtro_cat = st.selectbox("Filtrar por Categoría:", ["Todos", "CAT 1", "CAT 2", "CAT 3"])

# Aplicar Filtros
df_view = df_resultados.copy()
if not df_view.empty:
    if filtro_grado != "Todos":
        df_view = df_view[df_view["Grado"] == filtro_grado]
    if filtro_cat != "Todos":
        df_view = df_view[df_view["Categoría"] == filtro_cat]
    
    # Ordenamiento
    df_view = df_view.sort_values(
        by=["Puntaje", "Correctas", "Hora"], 
        ascending=[False, False, True]
    ).reset_index(drop=True)
    df_view.index += 1 

    cols_mostrar = ["DNI", "Estudiante", "Puntaje", "Correctas", "Incorrectas", "En Blanco", "Hora", "Grado", "Categoría", "Colegio", "Docente"]
    cols_finales = [c for c in cols_mostrar if c in df_view.columns]
    
    st.dataframe(
        df_view[cols_finales], 
        use_container_width=True,
        column_config={
            "Puntaje": st.column_config.ProgressColumn("Puntaje", format="%d pts", min_value=0, max_value=100),
            "Hora": st.column_config.TextColumn("Hora de Entrega", help="Hora de finalización del examen (criterio de desempate)"),
            "Docente": st.column_config.TextColumn("Docente Asesor"),
            "Incorrectas": st.column_config.NumberColumn("Erradas", help="Respuestas incorrectas")
        }
    )
else:
    st.info("Aún no hay resultados registrados para mostrar.")


# ==============================================================================
# 5. ZONA DE EXPORTACIÓN Y COMPARTIR (WORKFLOW PROFESIONAL)
# ==============================================================================
st.markdown("---")
st.markdown("### 🚀 Centro de Exportación Digital")

# --- PASO 1: DESCARGA ---
st.markdown("""
<div class="modern-card">
    <div class="card-header"><span class="step-badge">PASO 1</span>Generar Documento PDF</div>
    <p style="color: #6B7280; font-size: 14px;">Primero debes descargar el reporte oficial a tu dispositivo para poder adjuntarlo luego.</p>
</div>
""", unsafe_allow_html=True)

# Botón de descarga fuera del HTML para que funcione la lógica de Streamlit
col_dl_btn, col_dl_dummy = st.columns([1, 3])
archivo_pdf_path = None
if not df_view.empty:
    archivo_pdf_path = utils.generar_reporte_pdf(df_view)
    with col_dl_btn:
        with open(archivo_pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Descargar Reporte PDF", 
                f, 
                "Ranking_Oficial_CERM.pdf", 
                "application/pdf", 
                type="primary", 
                use_container_width=True
            )
else:
    st.warning("⚠️ No hay datos disponibles para generar el reporte.")

st.write("")

# --- PASO 2 Y 3: SELECCIÓN DE CANAL Y ENVÍO ---
st.markdown("""
<div class="modern-card">
    <div class="card-header"><span class="step-badge">PASO 2</span>Seleccionar Canal de Envío</div>
    <p style="color: #6B7280; font-size: 14px; margin-bottom: 20px;">Elige por dónde deseas enviar el reporte. Los campos cambiarán según tu elección.</p>
""", unsafe_allow_html=True)

# Pestañas para elegir el medio
tab_wa, tab_email = st.tabs(["💚 Enviar por WhatsApp", "✉️ Enviar por Correo Electrónico"])

# --- PESTAÑA WHATSAPP ---
with tab_wa:
    c_wa_form, c_wa_preview = st.columns([1, 1])
    
    with c_wa_form:
        st.write("#### 📱 Datos del Destinatario")
        dest_wa = st.text_input(
            "Número de Celular (9 dígitos)", 
            placeholder="Ej: 987654321", 
            max_chars=9,
            key="input_wa_num",
            help="Ingresa solo el número. El código +51 se agrega automáticamente."
        )
        mensaje_wa = st.text_area(
            "Mensaje Personalizado", 
            value="Hola, te adjunto el Reporte Oficial de Resultados del Concurso CERM 2025. ¡Saludos!",
            height=120,
            key="input_wa_msg"
        )
        
    with c_wa_preview:
        st.info("ℹ️ **Instrucciones:**\n1. Haz clic en el botón de abajo.\n2. Se abrirá WhatsApp Web o la App.\n3. **Importante:** Arrastra el PDF descargado al chat y envíalo.")
        
        # Generar enlace
        numero_final = f"51{dest_wa}" if dest_wa and len(dest_wa) == 9 else ""
        msg_enc = quote(mensaje_wa)
        link_whatsapp = f"https://api.whatsapp.com/send?phone={numero_final}&text={msg_enc}"
        
        st.write("")
        if dest_wa and len(dest_wa) == 9:
            st.link_button("🚀 Abrir WhatsApp y Enviar", link_whatsapp, type="primary", use_container_width=True)
        else:
            st.button("🚫 Ingresa un número válido para continuar", disabled=True, use_container_width=True)

# --- PESTAÑA CORREO (GMAIL / OUTLOOK) ---
with tab_email:
    c_mail_form, c_mail_btns = st.columns([1.2, 1])
    
    with c_mail_form:
        st.write("#### 📧 Redacción del Correo")
        dest_email = st.text_input("Correo Destino", placeholder="director@colegio.edu.pe", key="input_mail_to")
        asunto_email = st.text_input("Asunto", value="Resultados Oficiales CERM 2025", key="input_mail_sub")
        cuerpo_email = st.text_area(
            "Cuerpo del Correo", 
            value="Estimado(a),\n\nAdjunto sírvase encontrar el Reporte Oficial de Resultados del Concurso de Matemáticas CERM 2025.\n\nAtentamente,\nLa Comisión Organizadora.", 
            height=150,
            key="input_mail_body"
        )

    with c_mail_btns:
        st.info("ℹ️ **Instrucciones:**\nElige tu proveedor de correo. Se abrirá una nueva ventana con el mensaje listo. **No olvides adjuntar el PDF manualmente.**")
        
        # Codificar
        su_enc = quote(asunto_email)
        bo_enc = quote(cuerpo_email)
        
        # Enlaces
        link_gmail = f"https://mail.google.com/mail/?view=cm&fs=1&to={dest_email}&su={su_enc}&body={bo_enc}"
        link_outlook = f"https://outlook.live.com/owa/?path=/mail/action/compose&to={dest_email}&subject={su_enc}&body={bo_enc}"
        link_mailto = f"mailto:{dest_email}?subject={su_enc}&body={bo_enc}"
        
        st.write("")
        col_btn_g, col_btn_o = st.columns(2)
        with col_btn_g:
            st.link_button("🔴 Gmail", link_gmail, use_container_width=True)
        with col_btn_o:
            st.link_button("🔵 Outlook", link_outlook, use_container_width=True)
            
        st.write("")
        st.link_button("✉️ Abrir App de Correo (Default)", link_mailto, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True) # Cierre del div modern-card simulado

# ==========================================
# 6. ZONA DE PELIGRO
# ==========================================
st.markdown("---")
with st.expander("🗑️ Gestión de Resultados (Eliminar Exámenes Erróneos)"):
    st.warning("⚠️ Esta acción borrará el puntaje y el examen del estudiante.")
    
    if not df_resultados.empty:
        lista_borrar = df_resultados.apply(lambda x: f"{x['DNI']} | {x['Estudiante']} ({x['Puntaje']} pts)", axis=1).tolist()
        seleccion_borrar = st.selectbox("Seleccione el examen a eliminar:", [""] + lista_borrar)
        
        if seleccion_borrar:
            dni_borrar = seleccion_borrar.split(" | ")[0]
            if st.button(f"🔥 Eliminar Examen de {dni_borrar}", type="primary"):
                try:
                    db.collection('participantes').document(dni_borrar).delete()
                    st.success("✅ Examen eliminado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")