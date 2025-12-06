import streamlit as st
from styles import load_styles
import utils
import pandas as pd
from datetime import datetime

# Configuración y Estilos
load_styles()
st.set_page_config(page_title="Registro de Participantes", layout="wide")

# CSS Personalizado para las cajitas de respuesta
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

# Variables por defecto
def_nombre = ""
def_dni = ""
def_inst = ""
def_ugel = ""
def_gestion = ""
def_grado = "5to"
def_cat = "CAT 1"
def_docente = "" # <--- Variable nueva para el docente

# --- 2. BUSCADOR INTELIGENTE ---
st.markdown("### 🔍 Buscar Estudiante en Padrón")
col_b1, col_b2 = st.columns([3, 1])

with col_b1:
    seleccion = None
    if not df_busqueda.empty:
        # Creamos una columna temporal para buscar fácil
        df_busqueda['busqueda'] = df_busqueda['dni'].astype(str) + " | " + df_busqueda['nombre_completo']
        lista_opciones = [""] + df_busqueda['busqueda'].tolist()
        
        seleccion = st.selectbox("Escribe DNI o Nombre para buscar:", lista_opciones, index=0)

# Lógica de Autocompletado
if seleccion:
    dni_sel = seleccion.split(" | ")[0]
    # Filtramos el dataframe para encontrar al alumno
    fila = df_busqueda[df_busqueda['dni'] == dni_sel]
    
    if not fila.empty:
        reg = fila.iloc[0]
        def_dni = str(reg.get('dni', ''))
        def_nombre = reg.get('nombre_completo', '')
        def_inst = reg.get('institucion', '')
        def_ugel = reg.get('ugel', '')
        def_gestion = reg.get('gestion', '')
        def_grado = reg.get('grado', '5to')
        def_cat = reg.get('categoria', 'CAT 1')
        
        # --- AQUÍ ESTÁ EL CAMBIO IMPORTANTE ---
        # Recuperamos el docente. Si no existe o es NaN, ponemos vacío.
        val_doc = reg.get('docente', '')
        if pd.notna(val_doc) and str(val_doc).strip() != "" and str(val_doc) != "nan":
            def_docente = str(val_doc)
        else:
            def_docente = "No registrado"
            
        st.success(f"✅ Datos cargados de: **{def_nombre}**")

st.markdown("---")

# --- 3. FORMULARIO DE REGISTRO ---
with st.form("form_registro"):
    c1, c2, c3 = st.columns(3)
    
    with c1:
        dni = st.text_input("DNI del Estudiante:", value=def_dni)
        nombre = st.text_input("Apellidos y Nombres:", value=def_nombre)
        institucion = st.text_input("Institución Educativa:", value=def_inst)
    
    with c2:
        grado = st.selectbox("Grado:", ["1ro", "2do", "3ro", "4to", "5to"], index=["1ro", "2do", "3ro", "4to", "5to"].index(def_grado) if def_grado in ["1ro", "2do", "3ro", "4to", "5to"] else 4)
        categoria = st.selectbox("Categoría:", ["CAT 1", "CAT 2", "CAT 3"], index=["CAT 1", "CAT 2", "CAT 3"].index(def_cat) if def_cat in ["CAT 1", "CAT 2", "CAT 3"] else 0)
        # Input del Docente con el valor autocompletado
        val_docente = st.text_input("Docente Asesor:", value=def_docente, help="Nombre del profesor asesor")

    with c3:
        ugel = st.text_input("UGEL:", value=def_ugel)
        gestion = st.selectbox("Gestión:", ["Pública", "Privada"], index=0 if def_gestion.lower() == "pública" or def_gestion == "" else 1)
        hora_entrega = datetime.now().strftime("%H:%M:%S")
        st.info(f"🕒 Hora de registro: {hora_entrega}")

    st.markdown("### 📝 Hoja de Respuestas")
    
    # Generación dinámica de inputs para respuestas (1-20)
    filas_resp = [st.columns(5) for _ in range(4)]
    respuestas = []
    
    for i in range(1, 21):
        fila_idx = (i - 1) // 5
        col_idx = (i - 1) % 5
        
        with filas_resp[fila_idx][col_idx]:
            st.markdown(f"""<div class="question-box"><span class="question-label">Pregunta {i}</span></div>""", unsafe_allow_html=True)
            resp = st.selectbox(f"P{i}", ["", "A", "B", "C", "D", "E"], key=f"resp_{i}", label_visibility="collapsed")
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
                        "docente": val_docente # Guardamos el docente en la base de datos de resultados
                    },
                    "examen": {"respuestas": respuestas},
                    "metricas": {"total_puntos": total, "correctas": ok, "incorrectas": bad, "en_blanco": blank},
                    "info_registro": {"hora_entrega": hora_entrega}
                }
                
                if utils.guardar_alumno(datos):
                    st.success(f"✅ Registrado Exitosamente. Puntaje: {total}")
                    st.balloons()
                    # Opcional: limpiar form
                else:
                    st.error("❌ Error al guardar en la base de datos.")