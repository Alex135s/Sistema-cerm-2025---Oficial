import streamlit as st
from styles import load_styles
import utils
import pandas as pd

# 1. Estilos y Configuración
load_styles()
st.set_page_config(page_title="Configuración - CERM 2025", layout="wide")

st.markdown("""
<div class="header-container">
    <h1 class="header-title">⚙️ Configuración del Examen</h1>
    <p class="header-subtitle">Gestión de claves de respuesta y auditoría de cambios.</p>
</div>
""", unsafe_allow_html=True)

# 2. Cargar datos actuales
config_actual = utils.cargar_configuracion()

# --- FUNCIÓN DE INTERFAZ POR CATEGORÍA ---
def seccion_categoria(categoria, titulo, color_tab):
    st.markdown(f"### {titulo}")
    st.info(f"Modificando patrón oficial para: **Categoría {categoria}**")
    
    clave_actual = config_actual.get(categoria, [""]*20)
    
    # Grid de inputs
    respuestas_temp = []
    cols = st.columns(5)
    for i in range(1, 21):
        idx = (i-1) % 5
        val_bd = clave_actual[i-1] if i-1 < len(clave_actual) else ""
        
        # Validar índice del selectbox
        try: idx_sel = ["A", "B", "C", "D", "E"].index(val_bd)
        except: idx_sel = None
        
        with cols[idx]:
            val = st.selectbox(
                f"P{i}", ["A", "B", "C", "D", "E"], 
                index=idx_sel, 
                key=f"cfg_{categoria}_{i}",
                placeholder="-"
            )
            respuestas_temp.append(val if val else "") 
            
    st.write("")
    # BOTÓN INDEPENDIENTE
    if st.button(f"💾 Guardar Claves {categoria}", type="primary", use_container_width=True):
        if utils.guardar_categoria_individual(categoria, respuestas_temp):
            st.success(f"✅ ¡Claves de Categoría {categoria} actualizadas!")
            st.balloons()
            st.rerun() 
        else:
            st.error("Error al guardar.")

# --- PESTAÑAS NUEVAS (CAT 1, 2, 3) ---
tab1, tab2, tab3, tab_hist = st.tabs([
    "🏆 CAT 1 (5to)", 
    "🥈 CAT 2 (3ro-4to)", 
    "🥉 CAT 3 (1ro-2do)",
    "📜 Historial"
])

with tab1:
    seccion_categoria("CAT 1", "Clave Categoría 1 (5to Grado)", "orange")

with tab2:
    seccion_categoria("CAT 2", "Clave Categoría 2 (3ro y 4to)", "green")

with tab3:
    seccion_categoria("CAT 3", "Clave Categoría 3 (1ro y 2do)", "blue")

# --- HISTORIAL DE CAMBIOS ---
with tab_hist:
    st.markdown("### Auditoría de Modificaciones")
    historial = utils.obtener_historial()
    
    if historial:
        df_hist = pd.DataFrame(historial)
        if not df_hist.empty:
            df_show = df_hist[["fecha", "categoria", "claves_guardadas"]]
            df_show.columns = ["Fecha/Hora", "Cat", "Patrón Guardado"]
            st.dataframe(df_show, use_container_width=True)
    else:
        st.info("No hay cambios registrados todavía.")