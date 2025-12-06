import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

print("--- 🚀 INICIANDO MIGRACIÓN DEL DATASET HORIZONTAL ---")

# ==========================================
# 1. CONEXIÓN A FIREBASE
# ==========================================
if not firebase_admin._apps:
    try:
        if not os.path.exists("serviceAccountKey.json"):
            print("❌ ERROR: Falta el archivo 'serviceAccountKey.json'")
            sys.exit()
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"❌ Error conectando a Firebase: {e}")
        sys.exit()

db = firestore.client()

# ==========================================
# 2. BORRAR DIRECTORIO ANTIGUO
# ==========================================
def delete_collection(coll_ref, batch_size=400):
    docs = list(coll_ref.limit(batch_size).stream())
    deleted = 0
    if len(docs) > 0:
        print(f"🗑️ Borrando registros antiguos...")
        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()
        deleted = len(docs)
        if deleted >= batch_size:
            return delete_collection(coll_ref, batch_size)
    return deleted

print("🧹 Limpiando base de datos 'directorio_alumnos'...")
delete_collection(db.collection('directorio_alumnos'))
print("✅ Base de datos limpia.")

# ==========================================
# 3. PROCESAR ARCHIVO HORIZONTAL
# ==========================================
archivo_csv = 'datos.csv'

if not os.path.exists(archivo_csv):
    print(f"❌ ERROR: No encuentro '{archivo_csv}'.")
    sys.exit()

try:
    # Leemos con punto y coma, header en fila 1 (índice 1, segunda fila)
    print(f"📂 Leyendo archivo: {archivo_csv}...")
    df = pd.read_csv(archivo_csv, sep=';', header=1, encoding='utf-8')
    
    # Normalizar nombres de columnas (quitar espacios extra)
    df.columns = df.columns.str.strip()
    
    # MAPEO DE COLUMNAS (Estructura Horizontal)
    # Pandas añade .1, .2, .3, .4 a los nombres repetidos automáticamente
    
    mapa_grados = {
        "1ro": {"nom": "Nombres",   "ape": "Apellidos",   "dni": "Número de DNI"},
        "2do": {"nom": "Nombres.1", "ape": "Apellidos.1", "dni": "Número de DNI.1"},
        "3ro": {"nom": "Nombres.2", "ape": "Apellidos.2", "dni": "Número de DNI.2"},
        "4to": {"nom": "Nombres.3", "ape": "Apellidos.3", "dni": "Número de DNI.3"},
        "5to": {"nom": "Nombres.4", "ape": "Apellidos.4", "dni": "Número de DNI.4"}
    }
    
    # Columnas Institucionales y Docente
    col_inst = "Institución Educativa"  # A veces tiene espacio al inicio, ya lo limpiamos con strip()
    col_ugel = "UGEL"
    col_gest = "Tipo de Gestión"
    
    col_doc_nom = "Nombres.5"
    col_doc_ape = "Apellidos.5"
    
    batch = db.batch()
    contador = 0
    total_subidos = 0
    total_errores = 0
    
    print("☁️ Procesando filas y subiendo a Firebase...")
    
    for index, row in df.iterrows():
        # Datos del Colegio (Comunes para toda la fila)
        institucion = str(row.get(col_inst, "")).strip()
        # Si la columna "Institución Educativa" falla, probar la del final "Nombre  la Institución Educativa"
        if not institucion or institucion == "nan":
             institucion = str(row.get("Nombre  la Institución Educativa", "")).strip()
             
        ugel = str(row.get(col_ugel, "")).strip()
        gestion = str(row.get(col_gest, "")).strip()
        
        # Datos del Docente
        docente = "No registrado"
        if col_doc_nom in df.columns:
            n_doc = str(row.get(col_doc_nom, "")).strip()
            a_doc = str(row.get(col_doc_ape, "")).strip()
            if n_doc and n_doc != "nan":
                docente = f"{n_doc} {a_doc}"
        
        # Recorrer los 5 grados de esta fila
        for grado, cols in mapa_grados.items():
            try:
                raw_dni = row.get(cols["dni"])
                
                # Validar si existe alumno en este grado
                if pd.notna(raw_dni) and str(raw_dni).strip() != "":
                    # Limpiar DNI
                    dni = str(int(float(raw_dni))).strip()
                    nombres = str(row.get(cols["nom"], "")).strip()
                    apellidos = str(row.get(cols["ape"], "")).strip()
                    nombre_completo = f"{apellidos} {nombres}"
                    
                    # Calcular Categoría (NUEVA LÓGICA)
                    categoria = "CAT 3"
                    if grado == "5to": 
                        categoria = "CAT 1"
                    elif grado in ["3ro", "4to"]: 
                        categoria = "CAT 2"
                    
                    # Objeto Alumno
                    alumno = {
                        "dni": dni,
                        "nombres": nombres,
                        "nombre_completo": nombre_completo,
                        "colegio": institucion,
                        "grado": grado,
                        "categoria": categoria,
                        "ugel": ugel,
                        "gestion": gestion,
                        "docente": docente
                    }
                    
                    # Agregar al lote
                    doc_ref = db.collection('directorio_alumnos').document(dni)
                    batch.set(doc_ref, alumno)
                    
                    contador += 1
                    total_subidos += 1
                    
                    if contador >= 400:
                        batch.commit()
                        batch = db.batch()
                        contador = 0
                        print(f"   -> {total_subidos} alumnos subidos...")
                        
            except Exception as e:
                # print(f"Error en fila {index} grado {grado}: {e}")
                total_errores += 1

    if contador > 0:
        batch.commit()

    print(f"🎉 ¡ÉXITO TOTAL! Se han migrado {total_subidos} estudiantes.")
    if total_errores > 0:
        print(f"⚠️ Se omitieron algunos registros incompletos.")

except Exception as e:
    print(f"❌ Error fatal: {e}")