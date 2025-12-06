import streamlit as st
from styles import load_styles
import utils
import pandas as pd
from datetime import datetime

# Configuración y Estilos
load_styles()
st.set_page_config(page_title="Registro de Participantes", layout="wide")

# CSS Personalizado para las cajitas de respuesta (Igual que en Editar)
st.markdown("""
<style>
    .question-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .question-label {
        font-weight: 700;
        color: #1A3A8C;
        font-size: 16px;
        margin-bottom: 5px;
        display: block;
    }
    div[data-testid="stSelectbox"] {
        min-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <h1 class="header-title">📝 Registro de Participantes</h1>
    <p class="header-subtitle">Busca un estudiante para autocompletar o registra uno nuevo.</p>
</div>
""", unsafe_allow_html=True)

# --- 1. CARGAR DIRECTORIO ---
try:
    df_busqueda = utils.cargar_directorio_csv()
except:
    df_busqueda = pd.DataFrame()

# --- 2. BUSCADOR ---
st.markdown("### 🔍 Buscar Estudiante")
col_busq, col_btn = st.columns([5, 1])

if not df_busqueda.empty:
    df_busqueda['dni_str'] = df_busqueda['dni'].astype(str).str.strip()
    opciones_busqueda = df_busqueda.apply(lambda x: f"{x['dni_str']} | {x['nombre_completo']}", axis=1).tolist()
    opciones_busqueda.insert(0, "")
else:
    opciones_busqueda = [""]

def limpiar_todo():
    if "sb_buscador" in st.session_state:
        st.session_state.sb_buscador = opciones_busqueda[0]

with col_btn:
    st.write("") 
    st.write("") 
    st.button("🧹 Limpiar", on_click=limpiar_todo, help="Borrar búsqueda y limpiar campos", use_container_width=True)

with col_busq:
    seleccion = st.selectbox("Seleccione un estudiante:", opciones_busqueda, key="sb_buscador")

# Variables por defecto
val_dni = ""
val_nombre = ""
val_inst = ""
val_ugel = ""
val_gestion = "Gestión pública"
val_grado = "1ro"
val_cat = "CAT 3" 
val_docente = "No registrado"

# Si hay selección
if seleccion and seleccion != "":
    dni_seleccionado = seleccion.split(" | ")[0].strip()
    datos_alumno = df_busqueda[df_busqueda['dni_str'] == dni_seleccionado]
    
    if not datos_alumno.empty:
        fila = datos_alumno.iloc[0]
        val_dni = str(fila['dni'])
        val_nombre = str(fila['nombre_completo'])
        val_inst = str(fila['institucion'])
        val_ugel = str(fila['ugel'])
        val_gestion = str(fila['gestion'])
        val_grado = str(fila['grado'])
        val_cat = str(fila['categoria']) 
        val_docente = str(fila.get('docente', 'No registrado'))
        if val_docente == "nan": val_docente = "No registrado"
        
        st.success(f"✅ Datos cargados: **{val_nombre}**")

# --- 4. FORMULARIO ---
st.markdown("---")
with st.form("form_registro"):
    # Sección de Datos
    st.markdown("#### 👤 Datos Personales")
    c1, c2 = st.columns(2)

    with c1:
        dni = st.text_input("🆔 DNI / Código", value=val_dni)
        nombre = st.text_input("👤 Apellidos y Nombres", value=val_nombre)
        institucion = st.text_input("🏫 Institución Educativa", value=val_inst)
        ugel = st.text_input("📍 UGEL", value=val_ugel)

    with c2:
        # Grado
        grados_opts = ["1ro", "2do", "3ro", "4to", "5to"]
        idx_grado = grados_opts.index(val_grado) if val_grado in grados_opts else 0
        grado = st.selectbox("🎓 Grado / Año", grados_opts, index=idx_grado)
        
        # Categoría Automática (Lógica visual dentro del form para referencia)
        # Nota: Al guardar usaremos la lógica final, aquí es para mostrar opciones correctas
        cat_opts = ["CAT 1", "CAT 2", "CAT 3"]
        try:
            # Intentar mantener la categoría cargada si es válida
            idx_cat = cat_opts.index(val_cat)
        except:
            # Si no, calcular por defecto
            if grado == "5to": idx_cat = 0
            elif grado in ["3ro", "4to"]: idx_cat = 1
            else: idx_cat = 2

        categoria = st.selectbox("🏷️ Categoría", cat_opts, index=idx_cat)

        # Gestión
        gestion_opts = ["Gestión pública", "Gestión privada"]
        idx_gestion = 1 if "privada" in str(val_gestion).lower() else 0
        gestion = st.selectbox("🏢 Tipo de Gestión", gestion_opts, index=idx_gestion)
        
        # Docente
        st.text_input("👨‍🏫 Docente Asesor (Solo lectura)", value=val_docente, disabled=True)

    st.markdown("---")
    st.markdown("#### 📝 Respuestas y Entrega")

    # Hora
    horas_lista = []
    for h in range(8, 18):
        for m in range(0, 60, 5):
            horas_lista.append(f"{h:02d}:{m:02d}")

    try:
        idx_hora = 0
        now_min = datetime.now().hour * 60 + datetime.now().minute
        min_diff = 9999
        for i, h_str in enumerate(horas_lista):
            hh, mm = map(int, h_str.split(":"))
            h_min = hh * 60 + mm
            if abs(h_min - now_min) < min_diff:
                min_diff = abs(h_min - now_min)
                idx_hora = i
    except:
        idx_hora = 0

    # Grid de Respuestas Mejorado
    c_hora, c_resp = st.columns([1, 4])

    with c_hora:
        st.markdown("<br>", unsafe_allow_html=True)
        hora_entrega = st.selectbox("⏰ Hora de Entrega", horas_lista, index=idx_hora)

    with c_resp:
        respuestas = []
        opciones = ["","A","B","C","D","E"]
        
        # Fila 1 (1-10)
        cols_r1 = st.columns(10)
        for i in range(1, 11):
            with cols_r1[i-1]:
                st.markdown(f'<div class="question-box"><span class="question-label">P{i}</span></div>', unsafe_allow_html=True)
                resp = st.selectbox(f"P{i}", opciones, key=f"resp_{i}", label_visibility="collapsed")
                respuestas.append(resp)
        
        st.write("")
        
        # Fila 2 (11-20)
        cols_r2 = st.columns(10)
        for i in range(11, 21):
            with cols_r2[i-11]:
                st.markdown(f'<div class="question-box"><span class="question-label">P{i}</span></div>', unsafe_allow_html=True)
                resp = st.selectbox(f"P{i}", opciones, key=f"resp_{i}", label_visibility="collapsed")
                respuestas.append(resp)

    st.markdown("---")
    submitted = st.form_submit_button("💾 Guardar Participante", type="primary", use_container_width=True)

    if submitted:
        if nombre == "" or dni == "":
            st.error("⚠️ Nombre y DNI son obligatorios.")
        else:
            patron = utils.obtener_patron_respuestas(categoria)
            if patron is None:
                st.error("⚠️ Configure la clave de respuestas primero en 'Configuración'.")
            else:
                total, ok, bad, blank, metricas = utils.calcular_nota(respuestas, patron)
                
                datos = {
                    "alumno": {
                        "dni": dni, "nombres": nombre, "colegio": institucion,
                        "grado": grado, "categoria": categoria,
                        "ugel": ugel, "gestion": gestion,
                        "docente": val_docente
                    },
                    "examen": {"respuestas": respuestas},
                    "metricas": {"total_puntos": total, "correctas": ok, "incorrectas": bad, "en_blanco": blank},
                    "info_registro": {"hora_entrega": hora_entrega}
                }
                if utils.guardar_alumno(datos):
                    st.success(f"✅ Registrado Exitosamente. Puntaje: {total}")
                    st.balloons()
                else:
                    st.error("❌ Error al guardar en la base de datos.")