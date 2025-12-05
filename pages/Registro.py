import streamlit as st
from styles import load_styles
import utils
import pandas as pd
from datetime import datetime

load_styles()
st.set_page_config(page_title="Registro de Participantes", layout="wide")

st.markdown("""
<div class="header-container">
    <h1 class="header-title">📝 Registro de Participantes</h1>
    <p class="header-subtitle">Busca un estudiante para autocompletar o registra uno nuevo.</p>
</div>
""", unsafe_allow_html=True)

# --- 1. CARGAR LA BASE DE DATOS DEL CSV (DIRECTORIO) ---
df_busqueda = utils.cargar_directorio_csv()

# --- 2. EL BUSCADOR INTELIGENTE ---
st.markdown("### 🔍 Buscar Estudiante")

col_busq, col_btn = st.columns([5, 1])

if not df_busqueda.empty:
    # Aseguramos que el DNI sea string limpio
    df_busqueda['dni_str'] = df_busqueda['dni'].astype(str).str.strip()
    opciones_busqueda = df_busqueda.apply(lambda x: f"{x['dni_str']} | {x['nombre_completo']}", axis=1).tolist()
    opciones_busqueda.insert(0, "")
else:
    opciones_busqueda = [""]

# Función para limpiar
def limpiar_todo():
    if "sb_buscador" in st.session_state:
        st.session_state.sb_buscador = opciones_busqueda[0]

with col_btn:
    st.write("") 
    st.write("") 
    st.button("🧹 Limpiar", on_click=limpiar_todo, help="Borrar búsqueda y limpiar campos")

with col_busq:
    seleccion = st.selectbox(
        "Escribe el DNI o Apellido:", 
        opciones_busqueda, 
        key="sb_buscador"
    )

# Variables por defecto
val_dni = ""
val_nombre = ""
val_inst = ""
val_ugel = ""
val_gestion = "Gestión pública"
val_grado = "1ro"
val_cat = "A"
val_docente = "No registrado"

# Si hay selección, llenamos las variables
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
        # Recuperamos el docente de forma segura
        val_docente = str(fila.get('docente', 'No registrado'))
        if val_docente == "nan": val_docente = "No registrado"
        
        st.success(f"✅ Datos cargados: **{val_nombre}**")

# --- 4. FORMULARIO ---
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    dni = st.text_input("DNI / Código", value=val_dni)
    nombre = st.text_input("Apellidos y Nombres", value=val_nombre)
    institucion = st.text_input("Institución Educativa", value=val_inst)
    ugel = st.text_input("UGEL", value=val_ugel)

with c2:
    # Grado
    grados_opts = ["1ro", "2do", "3ro", "4to", "5to"]
    idx_grado = grados_opts.index(val_grado) if val_grado in grados_opts else 0
    grado = st.selectbox("Grado / Año", grados_opts, index=idx_grado)
    
    # Categoría
    cat_opts = ["A", "B", "C"]
    idx_cat = cat_opts.index(val_cat) if val_cat in cat_opts else 0
    categoria = st.selectbox("Categoría", cat_opts, index=idx_cat)

    # Gestión
    gestion_opts = ["Gestión pública", "Gestión privada"]
    idx_gestion = 1 if "privada" in str(val_gestion).lower() else 0
    gestion = st.selectbox("Tipo de Gestión", gestion_opts, index=idx_gestion)
    
    # Docente
    st.info(f"👨‍🏫 **Docente Asesor:** {val_docente}")

# --- 5. RESPUESTAS Y HORA ---
st.markdown("### 📝 Respuestas y Entrega")

# GENERADOR DE HORAS (Cada 5 minutos)
horas_lista = []
for h in range(8, 18): # De 8 AM a 6 PM
    for m in range(0, 60, 5):
        horas_lista.append(f"{h:02d}:{m:02d}")

# Obtenemos la hora actual aproximada para pre-seleccionar
hora_actual = datetime.now().strftime("%H:%M")
# Buscamos la hora más cercana en la lista
try:
    # Lógica simple: seleccionar la hora actual por defecto si está en lista
    idx_hora = 0
    min_diff = 9999
    now_min = datetime.now().hour * 60 + datetime.now().minute
    
    for i, h_str in enumerate(horas_lista):
        hh, mm = map(int, h_str.split(":"))
        h_min = hh * 60 + mm
        if abs(h_min - now_min) < min_diff:
            min_diff = abs(h_min - now_min)
            idx_hora = i
except:
    idx_hora = 0

# Grid para Hora y Respuestas
col_hora, col_resps = st.columns([1, 3])

with col_hora:
    st.markdown("#### ⏰ Hora de Entrega")
    hora_entrega = st.selectbox("Seleccione hora:", horas_lista, index=idx_hora)

with col_resps:
    st.markdown("#### 🔡 Clave de Respuestas")
    # Contenedor de respuestas
    respuestas = []
    cols = st.columns(5) # 5 columnas
    for i in range(1, 21):
        col_index = (i - 1) % 5 
        with cols[col_index]:
            resp = st.selectbox(f"P{i}", ["","A","B","C","D","E"], key=f"resp_{i}", label_visibility="collapsed")
            st.caption(f"P{i}")
            respuestas.append(resp)

# --- 6. GUARDAR ---
st.markdown("---")
if st.button("💾 Guardar Participante", type="primary", use_container_width=True):
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
                "info_registro": {"hora_entrega": hora_entrega} # <--- GUARDAMOS LA HORA
            }
            if utils.guardar_alumno(datos):
                st.success(f"✅ Registrado Exitosamente. Puntaje: {total}")
                st.balloons()
            else:
                st.error("❌ Error al guardar en la base de datos.")