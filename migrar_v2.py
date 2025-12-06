import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

# Configuración de salida
sys.stdout.reconfigure(encoding='utf-8')

print("--- 🚀 ACTUALIZANDO 4TO GRADO (CON DOCENTES) ---")

# ==========================================
# 1. CONEXIÓN A FIREBASE
# ==========================================
if not firebase_admin._apps:
    try:
        if not os.path.exists("serviceAccountKey.json"):
            print("❌ ERROR: Falta 'serviceAccountKey.json'.")
            sys.exit()
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Conexión a Firebase establecida.")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit()

db = firestore.client()

# ==========================================
# 2. CARGAR EL ARCHIVO NUEVO (4TO2.csv)
# ==========================================
archivo_csv = '4TO2.csv'
try:
    # Leemos con header=1 (la fila 2 tiene los títulos)
    df = pd.read_csv(archivo_csv, sep=';', header=1, dtype=str, encoding='utf-8')
    print(f"✅ Archivo cargado. Filas encontradas: {len(df)}")
except Exception as e:
    print(f"❌ Error leyendo CSV: {e}")
    sys.exit()

# ==========================================
# 3. PROCESAR Y ACTUALIZAR
# ==========================================
batch = db.batch()
contador_batch = 0
total_procesados = 0

print("\n⏳ Actualizando registros con datos de docentes...")

for index, row in df.iterrows():
    try:
        # --- A. DATOS DEL ALUMNO ---
        dni_raw = str(row.get('Número de DNI', '')).strip()
        dni = dni_raw.replace(" ", "").replace(".0", "")
        
        if not dni.isdigit() or len(dni) < 6:
            continue # Saltamos filas vacías o inválidas

        nombres = str(row.get('Nombres', '')).strip().title()
        apellidos = str(row.get('Apellidos', '')).strip().title()
        nombre_completo = f"{apellidos} {nombres}"
        
        # Colegio
        institucion = str(row.get('Nombre  la Institución Educativa', 'No registrado')).strip()
        ugel = str(row.get('UGEL', '')).strip()
        gestion = str(row.get('Tipo de Gestión', '')).strip()

        # --- B. DATOS DEL DOCENTE (Nuevos) ---
        # Pandas renombra las columnas repetidas con .1
        doc_nom = str(row.get('Nombres.1', '')).strip()
        doc_ape = str(row.get('Apellidos.1', '')).strip()
        
        docente_nombre = "No registrado"
        if doc_nom or doc_ape:
            docente_nombre = f"{doc_nom} {doc_ape}".strip().title()

        # --- C. OBJETO A GUARDAR ---
        datos_alumno = {
            "dni": dni,
            "nombres": nombres,
            "apellidos": apellidos,
            "nombre_completo": nombre_completo,
            "grado": "4to",
            "categoria": "CAT 2",
            "institucion": institucion,
            "ugel": ugel,
            "gestion": gestion,
            "docente": docente_nombre # <--- ¡Dato actualizado!
        }

        # --- D. SUBIR (Upsert) ---
        # Al usar el mismo DNI, sobrescribimos el registro anterior con esta versión mejorada
        doc_ref = db.collection('directorio_alumnos').document(dni)
        batch.set(doc_ref, datos_alumno)
        
        contador_batch += 1
        total_procesados += 1
        
        if contador_batch >= 400:
            batch.commit()
            batch = db.batch()
            contador_batch = 0
            print(f"   -> {total_procesados} alumnos actualizados...")

    except Exception as e:
        print(f"⚠️ Error en fila {index}: {e}")

# Guardar lote final
if contador_batch > 0:
    batch.commit()

print("\n" + "="*50)
print(f"🎉 ACTUALIZACIÓN COMPLETADA")
print(f"✅ Total Alumnos Procesados: {total_procesados}")
print(f"ℹ️  Ahora todos los alumnos de 4to tienen su docente asignado.")
print("="*50)