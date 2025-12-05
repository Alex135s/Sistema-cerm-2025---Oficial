import streamlit as st

def load_styles():
    st.markdown("""
    <style>
    /* IMPORTAR FUENTE GOOGLE (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F4F6F9; /* Fondo gris muy suave para contraste */
    }

    /* HEADER PRINCIPAL */
    .header-container {
        background: white;
        padding: 40px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 30px;
        border-bottom: 4px solid #1A3A8C;
    }
    
    .header-title {
        font-size: 36px;
        font-weight: 800;
        color: #111827;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 16px;
        color: #6B7280;
        margin-top: 8px;
    }

    /* TARJETAS DE MÉTRICAS (KPIs) */
    .metric-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 40px;
    }

    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #E5E7EB;
        width: 100%;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #2563EB; /* Azul vibrante */
    }

    .metric-label {
        font-size: 14px;
        color: #6B7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* TARJETAS DE NAVEGACIÓN (MENÚ) */
    .nav-card {
        background: white;
        border-radius: 12px;
        padding: 25px;
        height: 100%;
        border: 1px solid #E5E7EB;
        transition: all 0.3s ease;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }

    .nav-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border-color: #2563EB;
    }

    .nav-icon {
        font-size: 40px;
        margin-bottom: 15px;
        display: block;
    }

    .nav-title {
        font-size: 18px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 8px;
    }

    .nav-desc {
        font-size: 13px;
        color: #6B7280;
        line-height: 1.5;
        margin-bottom: 20px;
        min-height: 40px; /* Para alinear botones */
    }

    /* BOTONES STREAMLIT PERSONALIZADOS */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: 0.2s;
    }
    
    /* Botón Primario (Azul) */
    .stButton > button[kind="primary"] {
        background-color: #2563EB;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8;
    }

    </style>
    """, unsafe_allow_html=True)