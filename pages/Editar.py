import streamlit as st
from styles import load_styles
import utils
import pandas as pd

# 1. Configuración Inicial
load_styles()
st.set_page_config(page_title="Editar Registros", layout="wide")

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
    /* Ajuste para centrar el selectbox dentro del div */
    div[data-testid="stSelectbox"] {
        min-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <h1 class="header-title">✏️ Gestión y Corrección</h1>
    <p class="header-subtitle">Edita datos personales o corrige las respuestas de un examen ya procesado.</p>
</div>
""", unsafe_allow_html=True)

# 2. Cargar Datos
try:
    df_directorio = utils.cargar_directorio_csv()
    raw_resultados = utils.load_data()
    lista_resultados = raw_resultados.get("participants", [])
    
    mapa_examenes = {}
    for r in lista_resultados:
        d = str(r.get('dni', '')).strip()
        if d: mapa_examenes[d] = r
            
except Exception as e:
    st.error(f"Error cargando bases de datos: {e}")
    df_directorio = pd.DataFrame()
    mapa_examenes = {}

# --- BUSCADOR ---
st.markdown("### 🔍 Buscar Estudiante")

col_search, col_btn = st.columns([4, 1])

if not df_directorio.empty:
    df_directorio['dni_str'] = df_directorio['dni'].astype(str).str.strip()
    lista_busqueda = df_directorio.apply(lambda x: f"{x['dni_str']} | {x['nombre_completo']}", axis=1).tolist()
    lista_busqueda.insert(0, "") 
else:
    lista_busqueda = [""]

def limpiar_filtro():
    if "sb_editar_alumno" in st.session_state:
        st.session_state.sb_editar_alumno = lista_busqueda[0]

with col_btn:
    st.write("") 
    st.write("") 
    st.button("🧹 Limpiar", on_click=limpiar_filtro, use_container_width=True)

with col_search:
    seleccion = st.selectbox("Seleccione un estudiante:", lista_busqueda, key="sb_editar_alumno")

# Variables por defecto
dni_val = ""
nombre_val = ""
inst_val = ""
ugel_val = ""
gestion_val = "Gestión pública"
grado_val = "1ro"
cat_val = "CAT 3"
docente_val = "No registrado"
respuestas_actuales = [""] * 20 
hora_val = "10:30"  # Default actualizado al inicio del rango
examen_encontrado = False

# --- CARGA DE DATOS ---
if seleccion and seleccion != "":
    dni_sel = seleccion.split(" | ")[0].strip()
    datos_dir = df_directorio[df_directorio['dni_str'] == dni_sel]
    
    if not datos_dir.empty:
        fila = datos_dir.iloc[0]
        dni_val = str(fila['dni'])
        nombre_val = str(fila['nombre_completo'])
        inst_val = str(fila['institucion'])
        ugel_val = str(fila['ugel'])
        gestion_val = str(fila['gestion'])
        grado_val = str(fila['grado'])
        cat_val = str(fila['categoria'])
        docente_val = str(fila.get('docente', 'No registrado'))
        if docente_val == "nan": docente_val = "No registrado"
        
        if dni_sel in mapa_examenes:
            examen = mapa_examenes[dni_sel]
            examen_encontrado = True
            st.success(f"✅ **EXAMEN ENCONTRADO:** Mostrando respuestas guardadas de {nombre_val}.")
            
            resps = examen.get("respuestas", [])
            if len(resps) < 20: resps += [""] * (20 - len(resps))
            respuestas_actuales = resps
            
            info = examen.get("info_registro", {})
            if isinstance(info, dict):
                hora_val = info.get("hora_entrega", "10:30")
                
            cat_guardada = examen.get("categoria")
            if cat_guardada: cat_val = cat_guardada
        else:
            st.warning(f"⚠️ El alumno {nombre_val} está en el padrón pero **NO TIENE EXAMEN REGISTRADO** aún.")

# --- FORMULARIO ---
st.markdown("---")

with st.form("form_edicion"):
    # Sección Datos
    st.markdown("#### 👤 Datos Personales")
    c1, c2 = st.columns(2)
    with c1:
        new_dni = st.text_input("🆔 DNI", value=dni_val)
        new_nombre = st.text_input("👤 Nombres y Apellidos", value=nombre_val)
        new_inst = st.text_input("🏫 Institución Educativa", value=inst_val)
        new_ugel = st.text_input("📍 UGEL", value=ugel_val)
    
    with c2:
        grados = ["1ro", "2do", "3ro", "4to", "5to"]
        idx_g = grados.index(grado_val) if grado_val in grados else 0
        new_grado = st.selectbox("🎓 Grado", grados, index=idx_g)
        
        cats = ["CAT 1", "CAT 2", "CAT 3"]
        try: idx_c = cats.index(cat_val)
        except: 
            if new_grado == "5to": idx_c = 0 
            elif new_grado in ["3ro", "4to"]: idx_c = 1 
            else: idx_c = 2 
            
        new_cat = st.selectbox("🏷️ Categoría", cats, index=idx_c)

        gests = ["Gestión pública", "Gestión privada"]
        idx_gs = 1 if "privada" in str(gestion_val).lower() else 0
        new_gestion = st.selectbox("🏢 Gestión", gests, index=idx_gs)
        
        st.text_input("👨‍🏫 Docente (Solo lectura)", value=docente_val, disabled=True)

    st.markdown("---")
    st.markdown("#### 📝 Corregir Respuestas y Hora")
    
    # =========================================================
    # ACTUALIZACIÓN DE HORARIO: 10:30 AM a 4:00 PM (minuto a minuto)
    # =========================================================
    horas_lista = []
    # Rango de horas: 10 a 16
    for h in range(10, 17): 
        for m in range(60):
            # Restricción inicio: Nada antes de las 10:30
            if h == 10 and m < 30:
                continue
            # Restricción final: Nada después de las 16:00
            if h == 16 and m > 0:
                break
            horas_lista.append(f"{h:02d}:{m:02d}")
    
    # Intentar buscar la hora guardada en la nueva lista
    try: 
        idx_h = horas_lista.index(hora_val)
    except: 
        # Si la hora antigua no existe en el rango nuevo, mostrar la primera (10:30)
        idx_h = 0
    
    # --- DISEÑO MEJORADO DE RESPUESTAS ---
    # Usamos un contenedor principal para la cuadrícula
    
    c_hora, c_resp = st.columns([1, 4])
    
    with c_hora:
        st.markdown("<br>", unsafe_allow_html=True) # Espacio para alinear
        new_hora = st.selectbox("⏰ Hora de Entrega", horas_lista, index=idx_h)
    
    with c_resp:
        # GRID DE 10 COLUMNAS (2 FILAS) PARA QUE SE VEA COMPACTO Y ORDENADO
        # Fila 1: P1 - P10
        cols_r1 = st.columns(10)
        resps_editadas = []
        opciones = ["", "A", "B", "C", "D", "E"]
        
        for i in range(1, 11): # 1 al 10
            with cols_r1[i-1]:
                # Usamos HTML para el estilo "Cajita"
                st.markdown(f'<div class="question-box"><span class="question-label">P{i}</span></div>', unsafe_allow_html=True)
                
                val_prev = respuestas_actuales[i-1]
                try: idx_r = opciones.index(val_prev)
                except: idx_r = 0
                
                key_unica = f"ed_p{i}_{dni_val}"
                val = st.selectbox(
                    f"P{i}", 
                    opciones, 
                    index=idx_r, 
                    key=key_unica,
                    label_visibility="collapsed"
                )
                resps_editadas.append(val)
        
        st.write("") # Separador visual entre filas
        
        # Fila 2: P11 - P20
        cols_r2 = st.columns(10)
        for i in range(11, 21): # 11 al 20
            with cols_r2[i-11]:
                st.markdown(f'<div class="question-box"><span class="question-label">P{i}</span></div>', unsafe_allow_html=True)
                
                val_prev = respuestas_actuales[i-1]
                try: idx_r = opciones.index(val_prev)
                except: idx_r = 0
                
                key_unica = f"ed_p{i}_{dni_val}"
                val = st.selectbox(
                    f"P{i}", 
                    opciones, 
                    index=idx_r, 
                    key=key_unica,
                    label_visibility="collapsed"
                )
                resps_editadas.append(val)

    st.markdown("---")
    guardar = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)

    if guardar:
        if not new_dni:
            st.error("DNI es obligatorio")
        else:
            patron = utils.obtener_patron_respuestas(new_cat)
            if not patron:
                st.error("⚠️ Falta configurar el patrón de respuestas.")
            else:
                total, ok, bad, blank, metricas = utils.calcular_nota(resps_editadas, patron)
                
                datos_upd = {
                    "alumno": {
                        "dni": new_dni, "nombres": new_nombre, "colegio": new_inst,
                        "grado": new_grado, "categoria": new_cat,
                        "ugel": new_ugel, "gestion": new_gestion, "docente": docente_val
                    },
                    "examen": {"respuestas": resps_editadas},
                    "metricas": {"total_puntos": total, "correctas": ok, "incorrectas": bad, "en_blanco": blank},
                    "info_registro": {"hora_entrega": new_hora}
                }
                
                if utils.guardar_alumno(datos_upd):
                    st.success("✅ **Examen Actualizado Correctamente.**")
                    st.info(f"Nuevo Puntaje Calculado: **{total} puntos**")
                    if not examen_encontrado:
                        st.balloons()
                else:
                    st.error("Error al guardar en Firebase.")