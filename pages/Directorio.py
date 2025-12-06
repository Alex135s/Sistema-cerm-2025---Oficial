import streamlit as st
from styles import load_styles
import utils
import pandas as pd
import firebase_admin
from firebase_admin import firestore

# Configuración básica
load_styles()
st.set_page_config(page_title="Gestión de Directorio", layout="wide")
db = firestore.client()

st.markdown("""
<div class="header-container">
    <h1 class="header-title">📇 Gestión de Directorio</h1>
    <p class="header-subtitle">Agrega nuevos estudiantes o elimina registros incorrectos del padrón oficial.</p>
</div>
""", unsafe_allow_html=True)

# Cargamos la data existente para el autocompletado
try:
    df_actual = utils.cargar_directorio_csv()
    if not df_actual.empty:
        # Extraemos listas únicas y ordenadas
        lista_colegios = sorted(df_actual['institucion'].dropna().unique().tolist())
        lista_docentes = sorted(df_actual['docente'].dropna().unique().tolist())
    else:
        lista_colegios = []
        lista_docentes = []
except:
    lista_colegios = []
    lista_docentes = []

# Pestañas
tab_add, tab_del = st.tabs(["➕ Agregar Estudiante", "🗑️ Eliminar Estudiante"])

# ==========================================
# PESTAÑA 1: AGREGAR ESTUDIANTE (CON CATEGORÍA VISIBLE)
# ==========================================
with tab_add:
    st.info("Utiliza este formulario para inscribir a un estudiante nuevo.")
    
    st.markdown("#### 👤 Datos Personales")
    c1, c2 = st.columns(2)
    
    with c1:
        dni = st.text_input("🆔 DNI (Obligatorio)")
        nombres = st.text_input("👤 Nombres")
        apellidos = st.text_input("👤 Apellidos")
        
        # --- AUTOCOMPLETADO DE COLEGIO ---
        opciones_col = ["Seleccione una I.E..."] + lista_colegios + ["🏫 OTRA (Escribir nueva)..."]
        sel_colegio = st.selectbox("🏫 Institución Educativa", opciones_col)
        
        colegio_manual = ""
        if sel_colegio == "🏫 OTRA (Escribir nueva)...":
            colegio_manual = st.text_input("📝 Escribe el nombre de la nueva I.E.")
        
    with c2:
        # Usamos key para detectar cambios en el grado
        grado = st.selectbox("🎓 Grado", ["1ro", "2do", "3ro", "4to", "5to"], key="dir_grado")
        
        # CÁLCULO AUTOMÁTICO DE CATEGORÍA
        cat_auto = "CAT 3"
        if grado == "5to": cat_auto = "CAT 1"
        elif grado in ["3ro", "4to"]: cat_auto = "CAT 2"
        
        # Mostramos la categoría (calculada automáticamente)
        # Lo ponemos disabled=True para que sea solo lectura (automático) o False si quieres editarlo
        categoria = st.text_input("🏷️ Categoría (Automática)", value=cat_auto, disabled=True)
        
        ugel = st.selectbox("📍 UGEL", ["UGEL Ica", "UGEL Chincha", "UGEL Pisco", "UGEL Nasca", "UGEL Palpa"])
        gestion = st.selectbox("🏢 Tipo de Gestión", ["Gestión pública", "Gestión privada"])
        
        # --- AUTOCOMPLETADO DE DOCENTE ---
        opciones_doc = ["Seleccione un Docente..."] + lista_docentes + ["👨‍🏫 OTRO (Escribir nuevo)..."]
        sel_docente = st.selectbox("👨‍🏫 Docente Asesor", opciones_doc)
        
        docente_manual = ""
        if sel_docente == "👨‍🏫 OTRO (Escribir nuevo)...":
            docente_manual = st.text_input("📝 Escribe el nombre del nuevo Docente")

    st.markdown("---")
    
    if st.button("💾 Guardar Nuevo Estudiante", type="primary", use_container_width=True):
        # Lógica de Colegio Final
        if sel_colegio == "🏫 OTRA (Escribir nueva)...":
            colegio_final = colegio_manual
        elif sel_colegio == "Seleccione una I.E...":
            colegio_final = ""
        else:
            colegio_final = sel_colegio

        # Lógica de Docente Final
        if sel_docente == "👨‍🏫 OTRO (Escribir nuevo)...":
            docente_final = docente_manual
        elif sel_docente == "Seleccione un Docente...":
            docente_final = "No registrado"
        else:
            docente_final = sel_docente

        # Validaciones
        if not dni or not nombres or not apellidos or not colegio_final:
            st.error("⚠️ Faltan datos obligatorios (DNI, Nombres, Apellidos o Colegio).")
        else:
            nuevo_alumno = {
                "dni": dni.strip(),
                "nombres": nombres.strip().upper(),
                "nombre_completo": f"{apellidos.strip().upper()} {nombres.strip().upper()}",
                "grado": grado,
                "categoria": categoria, # Usamos la categoría calculada y mostrada
                "colegio": colegio_final.strip().upper(),
                "ugel": ugel,
                "gestion": gestion,
                "docente": docente_final.strip().upper()
            }
            
            try:
                db.collection('directorio_alumnos').document(dni.strip()).set(nuevo_alumno)
                st.success(f"✅ Estudiante **{nombres} {apellidos}** ({categoria}) agregado al padrón.")
                st.balloons()
                utils.cargar_directorio_csv.clear() 
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

# ==========================================
# PESTAÑA 2: ELIMINAR ESTUDIANTE
# ==========================================
with tab_del:
    st.warning("⚠️ Cuidado: Esta acción borrará al estudiante del padrón permanentemente.")
    
    if not df_actual.empty:
        df_actual['busqueda'] = df_actual['dni'].astype(str) + " | " + df_actual['nombre_completo']
        lista_opciones = df_actual['busqueda'].tolist()
        
        seleccion_borrar = st.selectbox("🔍 Buscar estudiante a eliminar:", [""] + lista_opciones)
        
        if seleccion_borrar:
            dni_a_borrar = seleccion_borrar.split(" | ")[0]
            nombre_a_borrar = seleccion_borrar.split(" | ")[1]
            
            st.error(f"¿Estás seguro que deseas eliminar a: **{nombre_a_borrar}**?")
            
            if st.button(f"🗑️ SÍ, ELIMINAR A {nombre_a_borrar}", type="primary"):
                try:
                    db.collection('directorio_alumnos').document(dni_a_borrar).delete()
                    st.success("✅ Registro eliminado exitosamente.")
                    utils.cargar_directorio_csv.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")
    else:
        st.info("No hay alumnos en el directorio para eliminar.")