import streamlit as st
from styles import load_styles
import utils
import pandas as pd

# 1. Configuración de página
load_styles()
st.set_page_config(page_title="CERM 2025", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# BLOQUE DE SEGURIDAD (LOGIN)
# ==============================================================================
def check_password():
    """Retorna True si el usuario ingresó la clave correcta."""
    # Si ya ingresó correctamente antes, pasar directo
    if st.session_state.get("password_correct", False):
        return True

    # Mostrar pantalla de login
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1 style='color: #1A3A8C;'>🔐 Sistema CERM 2025</h1>
        <p>Acceso restringido solo para personal autorizado.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("Ingrese la clave de acceso:", type="password")
        if st.button("Ingresar al Sistema", use_container_width=True):
            # --- AQUÍ DEFINES TU CONTRASEÑA ---
            if pwd == "cerm2025":  
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("🚫 Clave incorrecta")
    return False

# Si no ha puesto la clave, detenemos todo aquí.
if not check_password():
    st.stop()

# ==============================================================================
# SISTEMA PRINCIPAL (DASHBOARD)
# ==============================================================================

st.markdown("""
<div class="header-container">
    <h1 class="header-title">🎓 Sistema de Gestión de Evaluación</h1>
    <p class="header-subtitle">CERM 2025 · Panel de Control Administrativo · Universidad La Continental</p>
</div>
""", unsafe_allow_html=True)

# --- CÁLCULO DE MÉTRICAS (DATA REAL) ---
try:
    df = utils.cargar_directorio_csv()
except:
    df = pd.DataFrame()

if not df.empty:
    total_alumnos = len(df)
    total_colegios = df['institucion'].nunique()
    total_ugel = df['ugel'].nunique()
else:
    total_alumnos = 0
    total_colegios = 0
    total_ugel = 0

# --- TARJETAS DE ESTADÍSTICAS (KPIs) ---
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_alumnos}</div>
        <div class="metric-label">Estudiantes Inscritos</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_colegios}</div>
        <div class="metric-label">Instituciones Educativas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_ugel}</div>
        <div class="metric-label">UGELs Participantes</div>
    </div>
    """, unsafe_allow_html=True)

st.write("") 
st.write("") 

# --- MENÚ DE NAVEGACIÓN ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">📝</span>
            <div class="nav-title">Registro</div>
            <div class="nav-desc">Registra participantes y sus 20 respuestas.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Ir a Registro", key="registro_btn", use_container_width=True, type="primary"):
        st.switch_page("pages/Registro.py")

with col2:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">📊</span>
            <div class="nav-title">Resultados</div>
            <div class="nav-desc">Top 20, estadísticas y exportación de reportes PDF.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Ver Resultados", key="resultados_btn", use_container_width=True):
        st.switch_page("pages/Resultados.py")

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">✏️</span>
            <div class="nav-title">Edición</div>
            <div class="nav-desc">Corrige datos personales o respuestas de exámenes ya procesados.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Gestionar Datos", key="btn_edit", use_container_width=True):
        st.switch_page("pages/Editar.py")

with col4:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">⚙️</span>
            <div class="nav-title">Configuración</div>
            <div class="nav-desc">Define claves oficiales (CAT 1, 2, 3) y ve el historial de cambios.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Ajustes", key="btn_conf", use_container_width=True):
        st.switch_page("pages/Configuracion.py")

st.write("")

# --- BOTÓN DE GESTIÓN DE DIRECTORIO ---
col5, col6 = st.columns(2)

with col5:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">📇</span>
            <div class="nav-title">Directorio</div>
            <div class="nav-desc">Agrega nuevos estudiantes o elimina registros incorrectos manualmente.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Gestionar Directorio", key="btn_directorio", use_container_width=True):
        st.switch_page("pages/Directorio.py")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #9CA3AF; font-size: 12px;">
    © 2025 Sistema de Evaluación Académica · Versión 3.5 (Nube) · Soporte TI
</div>
""", unsafe_allow_html=True)