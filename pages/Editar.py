import streamlit as st
from styles import load_styles
import utils
import pandas as pd

# 1. Configuración Inicial
load_styles()
st.set_page_config(page_title="Editar Registros", layout="wide")

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
    
    # Mapa de búsqueda DNI -> Examen
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
cat_val = "CAT 3" # Valor por defecto actualizado
docente_val = "No registrado"
respuestas_actuales = [""] * 20 
hora_val = "09:30" 
examen_encontrado = False

# --- CARGA DE DATOS ---
if seleccion and seleccion != "":
    dni_sel = seleccion.split(" | ")[0].strip()
    
    # 1. Datos Personales
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
        
        # 2. Datos del Examen (Firebase)
        if dni_sel in mapa_examenes:
            examen = mapa_examenes[dni_sel]
            examen_encontrado = True
            
            st.success(f"✅ **EXAMEN ENCONTRADO:** Mostrando respuestas guardadas de {nombre_val}.")
            
            # Cargar respuestas
            resps = examen.get("respuestas", [])
            if len(resps) < 20: resps += [""] * (20 - len(resps))
            respuestas_actuales = resps
            
            # Cargar hora si existe
            info = examen.get("info_registro", {})
            if isinstance(info, dict):
                hora_val = info.get("hora_entrega", "09:30")
                
            # Si el examen tenía una categoría guardada, usamos esa (útil si se cambió manualmente)
            cat_guardada = examen.get("categoria")
            if cat_guardada:
                cat_val = cat_guardada
        else:
            st.warning(f"⚠️ El alumno {nombre_val} está en el padrón pero **NO TIENE EXAMEN REGISTRADO** aún.")

# --- FORMULARIO ---
st.markdown("---")

with st.form("form_edicion"):
    # Sección Datos
    c1, c2 = st.columns(2)
    with c1:
        new_dni = st.text_input("DNI", value=dni_val)
        new_nombre = st.text_input("Nombres y Apellidos", value=nombre_val)
        new_inst = st.text_input("Institución Educativa", value=inst_val)
        new_ugel = st.text_input("UGEL", value=ugel_val)
    
    with c2:
        grados = ["1ro", "2do", "3ro", "4to", "5to"]
        idx_g = grados.index(grado_val) if grado_val in grados else 0
        new_grado = st.selectbox("Grado", grados, index=idx_g)
        
        # --- AQUÍ ESTABA EL ERROR: ACTUALIZAMOS LAS OPCIONES ---
        cats = ["CAT 1", "CAT 2", "CAT 3"]
        
        # Intentamos encontrar el índice de la categoría actual
        try:
            idx_c = cats.index(cat_val)
        except:
            # Si tiene una categoría vieja ("A", "B", "C"), calculamos la nueva por defecto
            if new_grado == "5to": idx_c = 0 # CAT 1
            elif new_grado in ["3ro", "4to"]: idx_c = 1 # CAT 2
            else: idx_c = 2 # CAT 3
            
        new_cat = st.selectbox("Categoría", cats, index=idx_c)

        gests = ["Gestión pública", "Gestión privada"]
        idx_gs = 1 if "privada" in str(gestion_val).lower() else 0
        new_gestion = st.selectbox("Gestión", gests, index=idx_gs)
        
        st.text_input("Docente (Solo lectura)", value=docente_val, disabled=True)

    st.markdown("---")
    st.markdown("#### 📝 Corregir Respuestas y Hora")
    
    # Hora
    horas_lista = []
    for h in range(8, 18):
        for m in range(0, 60, 5):
            horas_lista.append(f"{h:02d}:{m:02d}")
    
    try: idx_h = horas_lista.index(hora_val)
    except: idx_h = 0
    
    c_hora, c_resp = st.columns([1, 3])
    with c_hora:
        new_hora = st.selectbox("Hora de Entrega", horas_lista, index=idx_h)
    
    with c_resp:
        # GRID RESPUESTAS
        resps_editadas = []
        opciones = ["", "A", "B", "C", "D", "E"]
        cols_r = st.columns(5)
        
        for i in range(1, 21):
            col_idx = (i-1) % 5
            with cols_r[col_idx]:
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
                st.caption(f"P{i}")
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