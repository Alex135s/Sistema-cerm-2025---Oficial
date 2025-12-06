import streamlit as st
from styles import load_styles
import utils
import pandas as pd
import firebase_admin
from firebase_admin import firestore

# 1. Configuración
load_styles()
st.set_page_config(page_title="Resultados y Ranking", layout="wide")
db = firestore.client()

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
    
    # Cargamos el directorio para obtener los docentes
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
        # Extraemos la hora para poder ordenar por ella
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

    # --- CRUCE DE DOCENTES ---
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
    
    # ==============================================================================
    # 🚀 LÓGICA DE ORDENAMIENTO (CRITERIO DE DESEMPATE)
    # ==============================================================================
    # 1. Puntaje: Descendente (Mayor gana) -> False
    # 2. Correctas: Descendente (Mayor gana) -> False
    # 3. Hora: Ascendente (Menor tiempo/Más temprano gana) -> True
    df_view = df_view.sort_values(
        by=["Puntaje", "Correctas", "Hora"], 
        ascending=[False, False, True]
    ).reset_index(drop=True)
    
    # Puesto (Index + 1)
    df_view.index += 1 

    # Configuración de columnas para mostrar
    cols_mostrar = ["DNI", "Estudiante", "Puntaje", "Correctas", "Incorrectas", "En Blanco", "Hora", "Grado", "Categoría", "Colegio", "Docente"]
    # Filtramos para que no falle si alguna columna no existe
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

# 5. Exportación
with c_export:
    st.write("")
    if not df_view.empty:
        if st.button("📄 Generar Reportes PDF", use_container_width=True):
            # Usamos el dataframe filtrado y ordenado para el PDF
            archivo_pdf = utils.generar_reporte_pdf(df_view)
            with open(archivo_pdf, "rb") as f:
                st.download_button("⬇️ Descargar Ranking PDF", f, "Ranking_Oficial_CERM.pdf", "application/pdf", type="primary")

# ==========================================
# 6. ZONA DE PELIGRO: ELIMINAR EXÁMENES
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