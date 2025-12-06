import streamlit as st
import pandas as pd
import json
import os
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pytz

# ==============================================================================
# 0. CONEXIÓN A FIREBASE
# ==============================================================================
if not firebase_admin._apps:
    try:
        # Híbrido: Busca archivo local O secretos de la nube
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            key_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(key_dict)
            
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"❌ Error conectando a Firebase: {e}")
        st.stop()

db = firestore.client()

# ==========================================
# 1. GESTIÓN DE CONFIGURACIÓN (CLAVES)
# ==========================================
def cargar_configuracion():
    try:
        doc = db.collection('configuracion').document('respuestas_oficiales').get()
        if doc.exists: return doc.to_dict()
    except: pass
    return {"CAT 1": [""]*20, "CAT 2": [""]*20, "CAT 3": [""]*20}

def guardar_categoria_individual(categoria, nuevas_claves):
    try:
        config_actual = cargar_configuracion()
        config_actual[categoria] = nuevas_claves
        db.collection('configuracion').document('respuestas_oficiales').set(config_actual)
        
        # Historial
        zona_peru = pytz.timezone('America/Lima')
        evento = {
            "fecha": datetime.now(zona_peru).strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": datetime.now(),
            "categoria": categoria,
            "accion": "Actualización de Clave",
            "claves_guardadas": nuevas_claves
        }
        db.collection('historial_cambios').add(evento)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def obtener_historial():
    try:
        docs = db.collection('historial_cambios').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()
        return [doc.to_dict() for doc in docs]
    except: return []

def obtener_patron_respuestas(categoria):
    cfg = cargar_configuracion()
    return cfg.get(categoria, None)

# ==========================================
# 2. CARGAR DIRECTORIO
# ==========================================
@st.cache_data(ttl=600)
def cargar_directorio_csv():
    try:
        docs = db.collection('directorio_alumnos').stream()
        lista = [doc.to_dict() for doc in docs]
        if not lista: return pd.DataFrame()
        
        df = pd.DataFrame(lista)
        if 'colegio' in df.columns and 'institucion' not in df.columns:
            df.rename(columns={'colegio': 'institucion'}, inplace=True)
        return df
    except: return pd.DataFrame()

# ==========================================
# 3. GESTIÓN DE RESULTADOS
# ==========================================
def calcular_nota(respuestas_alumno, patron_oficial):
    """
    CORRECTA: +5 Puntos
    INCORRECTA: -2 Puntos (Puntos en contra)
    BLANCO: 0 Puntos
    """
    correctas = 0
    incorrectas = 0
    en_blanco = 0
    puntaje = 0
    
    PUNTOS_CORRECTA = 5
    PUNTOS_INCORRECTA = -2  # Restamos 2 puntos
    
    for i in range(20):
        r_alu = respuestas_alumno[i] if i < len(respuestas_alumno) else ""
        r_pat = patron_oficial[i] if i < len(patron_oficial) else ""
        
        if not r_alu: # Si está vacío (Blanco)
            en_blanco += 1
            # No suma ni resta
        elif r_alu == r_pat: # Correcta
            correctas += 1
            puntaje += PUNTOS_CORRECTA
        else: # Incorrecta
            incorrectas += 1
            puntaje += PUNTOS_INCORRECTA # Esto resta 2
            
    if puntaje < 0: puntaje = 0
            
    metricas = {
        "total_puntos": puntaje, 
        "correctas": correctas, 
        "incorrectas": incorrectas, 
        "en_blanco": en_blanco
    }
    return puntaje, correctas, incorrectas, en_blanco, metricas

def load_data():
    docs = db.collection('participantes').stream()
    return {"participants": [doc.to_dict() for doc in docs]}

def guardar_alumno(datos):
    try:
        dni = str(datos['alumno']['dni'])
        # Asegurar campos
        datos['alumno']['docente'] = datos['alumno'].get('docente', 'No registrado')
        
        registro = {
            "dni": dni,
            "nombre": datos['alumno']['nombres'],
            "colegio": datos['alumno']['colegio'],
            "grado": datos['alumno']['grado'],
            "categoria": datos['alumno']['categoria'],
            "ugel": datos['alumno']['ugel'],
            "gestion": datos['alumno']['gestion'],
            "docente": datos['alumno']['docente'],
            "metricas": datos['metricas'],
            "info_registro": datos['info_registro'],
            "respuestas": datos['examen']['respuestas']
        }
        db.collection('participantes').document(dni).set(registro)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# ==========================================
# 4. REPORTES PDF (ACTUALIZADO)
# ==========================================
def generar_reporte_pdf(df_resultados):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 10)
            self.cell(0, 10, 'Sistema de Evaluacion CERM 2025 - Reporte Oficial', 0, 1, 'R')
            self.ln(5)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # REPORTE 1: TOP 20
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "TOP 20 MEJORES ALUMNOS POR CATEGORIA", ln=True, align='C')
    pdf.ln(5)
    
    categorias = ["CAT 1", "CAT 2", "CAT 3"]
    
    for cat in categorias:
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(220, 230, 255)
        pdf.cell(0, 10, f"CATEGORIA {cat}", ln=True, fill=True)
        
        if not df_resultados.empty and "Categoría" in df_resultados.columns:
            top = df_resultados[df_resultados["Categoría"] == cat]
            
            # --- CRITERIO DE ORDENAMIENTO EXACTO ---
            # 1. Puntaje (Mayor a menor)
            # 2. Correctas (Mayor a menor)
            # 3. Hora (Menor a mayor = Más temprano gana)
            if "Hora" in top.columns:
                top = top.sort_values(by=["Puntaje", "Correctas", "Hora"], ascending=[False, False, True]).head(20)
            else:
                top = top.sort_values(by=["Puntaje", "Correctas"], ascending=[False, False]).head(20)
            
            # Encabezados de Tabla (Ancho Total A4 útil ~180-190)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(10, 8, "No.", 1, align='C')
            pdf.cell(65, 8, "Estudiante", 1)  # Reducido un poco para dar espacio a hora
            pdf.cell(65, 8, "Colegio", 1)     # Reducido un poco para dar espacio a hora
            pdf.cell(20, 8, "Pts", 1, align='C')
            pdf.cell(25, 8, "Hora", 1, align='C') # NUEVA COLUMNA
            pdf.ln()
            
            pdf.set_font("Arial", "", 9)
            rank = 1
            for _, row in top.iterrows():
                est = str(row.get("Estudiante","")).encode('latin-1', 'replace').decode('latin-1')
                col = str(row.get("Colegio","")).encode('latin-1', 'replace').decode('latin-1')
                hora = str(row.get("Hora", "--:--"))
                
                pdf.cell(10, 6, str(rank), 1, align='C')
                pdf.cell(65, 6, est[:35], 1) # Cortamos texto si es muy largo
                pdf.cell(65, 6, col[:35], 1)
                pdf.cell(20, 6, str(row.get("Puntaje",0)), 1, align='C')
                pdf.cell(25, 6, hora, 1, align='C')
                pdf.ln()
                rank += 1
        pdf.ln(5)
        
    # REPORTE 2: CAMPEÓN
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RECONOCIMIENTO INSTITUCIONAL", ln=True, align='C')
    pdf.ln(5)
    
    if not df_resultados.empty:
        camp = df_resultados.groupby("Colegio")["Puntaje"].sum().reset_index()
        camp = camp.sort_values(by="Puntaje", ascending=False)
        
        if not camp.empty:
            ganador = camp.iloc[0]
            col_ganador = str(ganador['Colegio']).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_fill_color(255, 215, 0)
            pdf.rect(10, pdf.get_y(), 190, 40, 'F')
            pdf.set_y(pdf.get_y() + 5)
            
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, f"CAMPEON REGIONAL DE MATEMATICA 2025", ln=True, align='C')
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "(Gallardete de Honor)", ln=True, align='C')
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"{col_ganador}", ln=True, align='C')
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 8, f"PUNTAJE ACUMULADO: {ganador['Puntaje']} Puntos", ln=True, align='C')
            pdf.ln(15)
            
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "MENCION HONORIFICA", ln=True, align='C')
            
            if len(camp) > 1:
                seg = camp.iloc[1]
                c2 = str(seg['Colegio']).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_fill_color(220, 220, 220)
                pdf.cell(0, 10, f"2do Puesto: {c2} ({seg['Puntaje']} pts)", ln=True, fill=True, align='C')
            
            if len(camp) > 2:
                ter = camp.iloc[2]
                c3 = str(ter['Colegio']).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_fill_color(205, 127, 50)
                pdf.cell(0, 10, f"3er Puesto: {c3} ({ter['Puntaje']} pts)", ln=True, fill=True, align='C')
            pdf.ln(10)

    # REPORTE 3: DOCENTES
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RECONOCIMIENTO DOCENTE", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 11)
    txt = ("Se otorgara Resolucion Directoral Regional de reconocimiento y "
           "felicitacion a los docentes asesores de los estudiantes que ocupen "
           "los tres primeros puestos en cada categoria.")
    pdf.multi_cell(0, 6, txt, 0, 'C')
    pdf.ln(10)
    
    for cat in categorias:
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(0, 51, 102)
        pdf.cell(0, 10, f" CATEGORIA {cat}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        if not df_resultados.empty:
            # Reutilizamos el mismo criterio de ordenamiento para los docentes
            if "Hora" in df_resultados.columns:
                 top3 = df_resultados[df_resultados["Categoría"] == cat].sort_values(
                     by=["Puntaje", "Correctas", "Hora"], 
                     ascending=[False, False, True]
                 ).head(3)
            else:
                 top3 = df_resultados[df_resultados["Categoría"] == cat].sort_values(
                     by=["Puntaje", "Correctas"], 
                     ascending=[False, False]
                 ).head(3)

            puesto = 1
            for _, row in top3.iterrows():
                doc = str(row.get("Docente", "No registrado")).encode('latin-1', 'replace').decode('latin-1')
                est = str(row.get("Estudiante", "")).encode('latin-1', 'replace').decode('latin-1')
                col = str(row.get("Colegio", "")).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.ln(2)
                pdf.set_font("Arial", "B", 11)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(20, 8, f"{puesto} Puesto", 0, 0, fill=True)
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 8, f"  Alumno: {est}", 0, 1, fill=True)
                pdf.set_text_color(0, 100, 0)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(20, 6, "", 0)
                pdf.cell(0, 6, f"DOCENTE ASESOR: {doc}", 0, 1)
                pdf.set_text_color(0,0,0)
                pdf.set_font("Arial", "I", 10)
                pdf.cell(20, 5, "", 0)
                pdf.cell(0, 5, f"Institucion: {col}", 0, 1)
                pdf.ln(2)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                puesto += 1
        pdf.ln(5)

    nombre = "Reporte_Oficial_CERM_2025.pdf"
    pdf.output(nombre)
    return nombre

# ==========================================
# 5. SEGURIDAD (LOGIN GLOBAL)
# ==========================================
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("""
    <div style='text-align: center; margin-top: 50px;'>
        <h1 style='color: #1A3A8C;'>🔐 Acceso Restringido</h1>
        <p>Por favor, inicie sesión para continuar.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd = st.text_input("Ingrese la clave de acceso:", type="password", key="login_pwd")
        if st.button("Ingresar", use_container_width=True):
            if pwd == "cerm2025":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("🚫 Clave incorrecta")
    return False