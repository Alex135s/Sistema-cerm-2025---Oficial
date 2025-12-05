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
# 0. CONEXIÓN A FIREBASE (INTELIGENTE: PC y NUBE)
# ==============================================================================
if not firebase_admin._apps:
    try:
        # CASO A: Estás en tu computadora (Existe el archivo)
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        
        # CASO B: Estás en la Nube (Streamlit Cloud usa "Secrets")
        else:
            # Esto busca la configuración interna de la nube
            key_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(key_dict)
            
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"❌ Error conectando a Firebase: {e}")
        st.stop()

db = firestore.client()

# ==========================================
# 1. GESTIÓN DE CONFIGURACIÓN Y HISTORIAL
# ==========================================
def cargar_configuracion():
    try:
        doc = db.collection('configuracion').document('respuestas_oficiales').get()
        if doc.exists: return doc.to_dict()
    except: pass
    return {"A": [""]*20, "B": [""]*20, "C": [""]*20}

def guardar_categoria_individual(categoria, nuevas_claves):
    try:
        config_actual = cargar_configuracion()
        config_actual[categoria] = nuevas_claves
        db.collection('configuracion').document('respuestas_oficiales').set(config_actual)
        
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
        return pd.DataFrame(lista) if lista else pd.DataFrame()
    except: return pd.DataFrame()

# ==========================================
# 3. GESTIÓN DE RESULTADOS
# ==========================================
def calcular_nota(respuestas_alumno, patron_oficial):
    correctas = 0
    incorrectas = 0
    en_blanco = 0
    puntaje = 0
    PUNTOS = 5
    
    for i in range(20):
        r_alu = respuestas_alumno[i] if i < len(respuestas_alumno) else ""
        r_pat = patron_oficial[i] if i < len(patron_oficial) else ""
        
        if not r_alu: en_blanco += 1
        elif r_alu == r_pat:
            correctas += 1
            puntaje += PUNTOS
        else: incorrectas += 1
            
    metricas = {"total_puntos": puntaje, "correctas": correctas, "incorrectas": incorrectas, "en_blanco": en_blanco}
    return puntaje, correctas, incorrectas, en_blanco, metricas

def load_data():
    docs = db.collection('participantes').stream()
    return {"participants": [doc.to_dict() for doc in docs]}

def guardar_alumno(datos):
    try:
        dni = str(datos['alumno']['dni'])
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
# 4. REPORTES PDF
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
    
    categorias = ["A", "B", "C"]
    
    for cat in categorias:
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(220, 230, 255)
        pdf.cell(0, 10, f"CATEGORIA {cat}", ln=True, fill=True)
        
        if not df_resultados.empty and "Categoría" in df_resultados.columns:
            top = df_resultados[df_resultados["Categoría"] == cat]
            top = top.sort_values(by=["Puntaje", "Correctas"], ascending=[False, False]).head(20)
            
            pdf.set_font("Arial", "B", 9)
            pdf.cell(10, 8, "No.", 1, align='C')
            pdf.cell(80, 8, "Estudiante", 1)
            pdf.cell(80, 8, "Colegio", 1)
            pdf.cell(20, 8, "Pts", 1, align='C')
            pdf.ln()
            
            pdf.set_font("Arial", "", 9)
            rank = 1
            for _, row in top.iterrows():
                est = str(row.get("Estudiante","")).encode('latin-1', 'replace').decode('latin-1')
                col = str(row.get("Colegio","")).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(10, 6, str(rank), 1, align='C')
                pdf.cell(80, 6, est[:40], 1)
                pdf.cell(80, 6, col[:40], 1)
                pdf.cell(20, 6, str(row.get("Puntaje",0)), 1, align='C')
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
                segundo = camp.iloc[1]
                col_2 = str(segundo['Colegio']).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_fill_color(220, 220, 220)
                pdf.cell(0, 10, f"2do Puesto: {col_2} ({segundo['Puntaje']} pts)", ln=True, fill=True, align='C')
            
            if len(camp) > 2:
                tercero = camp.iloc[2]
                col_3 = str(tercero['Colegio']).encode('latin-1', 'replace').decode('latin-1')
                pdf.set_fill_color(205, 127, 50)
                pdf.cell(0, 10, f"3er Puesto: {col_3} ({tercero['Puntaje']} pts)", ln=True, fill=True, align='C')
            
            pdf.ln(10)
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Ranking General de Instituciones (Top 5):", ln=True)
            r = 1
            pdf.set_font("Arial", "", 10)
            for _, row in camp.head(5).iterrows():
                col_name = str(row['Colegio']).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(10, 8, f"{r}.", 0)
                pdf.cell(130, 8, f"{col_name}", 0)
                pdf.cell(30, 8, f"{row['Puntaje']} pts", 0, ln=True)
                r += 1

    # REPORTE 3: DOCENTES
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RECONOCIMIENTO DOCENTE", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 11)
    texto_res = ("Se otorgara Resolucion Directoral Regional de reconocimiento y "
                 "felicitacion a los docentes asesores de los estudiantes que ocupen "
                 "los tres primeros puestos en cada categoria.")
    pdf.multi_cell(0, 6, texto_res, 0, 'C')
    pdf.ln(10)
    
    for cat in categorias:
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(0, 51, 102)
        pdf.cell(0, 10, f" CATEGORIA {cat}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        if not df_resultados.empty:
            top3 = df_resultados[df_resultados["Categoría"] == cat].sort_values(by="Puntaje", ascending=False).head(3)
            puesto = 1
            for _, row in top3.iterrows():
                docente = str(row.get("Docente", "No registrado")).encode('latin-1', 'replace').decode('latin-1')
                est = str(row.get("Estudiante", "")).encode('latin-1', 'replace').decode('latin-1')
                col = str(row.get("Colegio", "")).encode('latin-1', 'replace').decode('latin-1')
                ptj = row.get("Puntaje", 0)
                
                pdf.ln(2)
                pdf.set_font("Arial", "B", 11)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(20, 8, f"{puesto} Puesto", 0, 0, fill=True)
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 8, f"  Alumno: {est}  ({ptj} pts)", 0, 1, fill=True)
                
                pdf.set_text_color(0, 100, 0)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(20, 6, "", 0)
                pdf.cell(0, 6, f"DOCENTE ASESOR: {docente}", 0, 1)
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