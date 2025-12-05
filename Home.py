import streamlit as st
from styles import load_styles
import utils
import pandas as pd

# Cargar estilos
load_styles()
st.set_page_config(page_title="Dashboard CERM 2025", layout="wide", initial_sidebar_state="collapsed")

# --- 1. HEADER TIPO EMPRESARIAL ---
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🎓 Sistema de Gestión de Evaluación</h1>
    <p class="header-subtitle">CERM 2025 · Panel de Control Administrativo · Universidad La Continental</p>
</div>
""", unsafe_allow_html=True)

# --- 2. CÁLCULO DE MÉTRICAS (DATA REAL) ---
# Intentamos cargar los datos para mostrar números reales en el dashboard
df = utils.cargar_directorio_csv()

if not df.empty:
    total_alumnos = len(df)
    total_colegios = df['institucion'].nunique()
    total_ugel = df['ugel'].nunique()
else:
    total_alumnos = 0
    total_colegios = 0
    total_ugel = 0

# --- 3. SECCIÓN DE ESTADÍSTICAS (KPIs) ---
# Usamos columnas de Streamlit con HTML personalizado para las tarjetitas
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

st.write("") # Espacio
st.write("") 

# --- 4. MENÚ PRINCIPAL (GRID) ---
# Creamos un grid 2x2 para las acciones
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">📝</span>
            <div class="nav-title">Registro</div>
            <div class="nav-desc">Inscripción de estudiantes, llenado de fichas ópticas y validación de datos.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Nuevo Registro", key="btn_reg", use_container_width=True, type="primary"):
        st.switch_page("pages/Registro.py")

with col2:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">📊</span>
            <div class="nav-title">Resultados</div>
            <div class="nav-desc">Visualiza el ranking en tiempo real, reportes por colegio y estadísticas.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Ver Dashboard", key="btn_res", use_container_width=True):
        st.switch_page("pages/Resultados.py")

with col3:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">✏️</span>
            <div class="nav-title">Edición</div>
            <div class="nav-desc">Corrige nombres mal escritos, DNI duplicados o respuestas erróneas.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Gestionar Datos", key="btn_edit", use_container_width=True):
        st.switch_page("pages/Editar.py")

with col4:
    st.markdown("""
        <div class="nav-card">
            <span class="nav-icon">⚙️</span>
            <div class="nav-title">Configuración</div>
            <div class="nav-desc">Define las claves de respuestas (Patrón) para las categorías A, B y C.</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Ajustes", key="btn_conf", use_container_width=True):
        st.switch_page("pages/Configuracion.py")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #9CA3AF; font-size: 12px;">
    © 2025 Sistema de Evaluación Académica · Versión 2.1 · Soporte TI
</div>
""", unsafe_allow_html=True)