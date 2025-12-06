import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

print("--- 🚀 INICIANDO MIGRACIÓN A FIREBASE ---")

# ==========================================
# 1. CONEXIÓN A FIREBASE
# ==========================================
if not firebase_admin._apps:
    try:
        if not os.path.exists("serviceAccountKey.json"):
            print("❌ ERROR CRÍTICO: No encuentro el archivo 'serviceAccountKey.json'.")
            print("Descárgalo de tu consola de Firebase y ponlo en esta carpeta.")
            sys.exit()
            
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Conexión a Firebase exitosa.")
    except Exception as e:
        print(f"❌ Error conectando a Firebase: {e}")
        sys.exit()

db = firestore.client()

# ==========================================
# 2. CARGAR EL ARCHIVO CSV
# ==========================================
archivo_csv = 'Datoslimpios.csv'
if not os.path.exists(archivo_csv):
    print(f"❌ ERROR: No encuentro '{archivo_csv}'. Asegúrate de que el nombre sea exacto.")
    sys.exit()

try:
    # Leemos con punto y coma y saltamos la primera fila de títulos generales
    df = pd.read_csv(archivo_csv, sep=';', header=1, encoding='utf-8')
    print(f"✅ Archivo cargado. Filas encontradas: {len(df)}")
except Exception as e:
    print(f"❌ Error leyendo el CSV: {e}")
    sys.exit()

# ==========================================
# 3. PROCESAR Y SUBIR
# ==========================================
batch = db.batch()
contador_lote = 0
total_subidos = 0
total_errores = 0

print("⏳ Subiendo alumnos a la nube (Colección: 'directorio_alumnos')...")

# Definimos los prefijos de las columnas según tu archivo
# Pandas nombra las columnas repetidas agregando .1, .2, etc.
columnas_mapa = {
    "1ro": {"nom": "Nombres",   "ape": "Apellidos",   "dni": "Número de DNI"},
    "2do": {"nom": "Nombres.1", "ape": "Apellidos.1", "dni": "Número de DNI.1"},
    "3ro": {"nom": "Nombres.2", "ape": "Apellidos.2", "dni": "Número de DNI.2"},
    "4to": {"nom": "Nombres.3", "ape": "Apellidos.3", "dni": "Número de DNI.3"},
    "5to": {"nom": "Nombres.4", "ape": "Apellidos.4", "dni": "Número de DNI.4"}
}

# Columnas del Docente (El último grupo)
col_doc_nom = "Nombres.5"
col_doc_ape = "Apellidos.5"

for index, row in df.iterrows():
    # 1. Obtener datos generales del Colegio
    institucion = str(row.get('Nombre  la Institución Educativa', '')).strip()
    ugel = str(row.get('UGEL a la que pertenece su I.E.', '')).strip()
    gestion = str(row.get('Tipo de Gestión Educativa', '')).strip()
    
    # 2. Obtener Docente Asesor (Es el mismo para todos los alumnos de esta fila/colegio)
    docente_nombre = "No registrado"
    if col_doc_nom in df.columns and pd.notna(row[col_doc_nom]):
        docente_nombre = f"{row[col_doc_nom]} {row.get(col_doc_ape, '')}".strip()

    # 3. Recorrer cada grado (1ro a 5to)
    for grado, cols in columnas_mapa.items():
        dni_raw = row.get(cols["dni"])
        
        # Solo procesamos si hay un DNI válido
        if pd.notna(dni_raw) and str(dni_raw).strip() != "":
            try:
                # Limpieza de datos
                dni = str(int(float(dni_raw))).strip() # Quitar decimales .0 si existen
                nombres = str(row.get(cols["nom"], "")).strip()
                apellidos = str(row.get(cols["ape"], "")).strip()
                nombre_completo = f"{apellidos} {nombres}"
                
                # Definir categoría
                categoria = "CAT 3" # Por defecto 1ro y 2do
                if grado == "5to": 
                    categoria = "CAT 1"
                elif grado in ["3ro", "4to"]: 
                    categoria = "CAT 2"

                # Objeto Alumno para Firebase
                datos_alumno = {
                    # ... resto de datos ...
                    "categoria": categoria,
                    # ...
                }
                # Objeto Alumno para Firebase
                datos_alumno = {
                    "dni": dni,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "nombre_completo": nombre_completo,
                    "grado": grado,
                    "categoria": categoria,
                    "institucion": institucion,
                    "ugel": ugel,
                    "gestion": gestion,
                    "docente": docente_nombre  # <--- ¡AQUÍ VA EL DOCENTE!
                }

                # Agregar al lote de subida (ID del documento = DNI)
                doc_ref = db.collection('directorio_alumnos').document(dni)
                batch.set(doc_ref, datos_alumno)
                
                contador_lote += 1
                total_subidos += 1

                # Firebase acepta lotes de máximo 500 escrituras
                if contador_lote >= 450:
                    batch.commit()
                    batch = db.batch()
                    contador_lote = 0
                    print(f"   -> {total_subidos} alumnos procesados...")
            
            except Exception as e:
                # Si falla un alumno específico, no detenemos todo, solo lo contamos
                # print(f"Error en fila {index} grado {grado}: {e}")
                total_errores += 1

# Subir los últimos registros pendientes
if contador_lote > 0:
    batch.commit()

print("---------------------------------------------------")
print(f"🎉 ¡MIGRACIÓN COMPLETADA!")
print(f"✅ Total alumnos subidos: {total_subidos}")
if total_errores > 0:
    print(f"⚠️ Algunos registros incompletos se omitieron: {total_errores}")
print("---------------------------------------------------")
print("Ahora tu sistema leerá los datos (incluido el docente) directamente desde la nube.")
