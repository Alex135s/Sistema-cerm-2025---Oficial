import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

# Configuración de codificación
sys.stdout.reconfigure(encoding='utf-8')

print("--- 🚀 AGREGANDO ALUMNOS DE 4TO GRADO ---")

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
# 2. CARGAR EL ARCHIVO 4TO.csv
# ==========================================
archivo_csv = '4TO.csv'
try:
    # El encabezado real está en la fila 2 (índice 1)
    df = pd.read_csv(archivo_csv, sep=';', header=1, dtype=str, encoding='utf-8')
    # Limpiamos nombres de columnas (eliminamos espacios extra)
    df.columns = df.columns.str.strip()
    print(f"✅ Archivo cargado. Alumnos a procesar: {len(df)}")
except Exception as e:
    print(f"❌ Error leyendo CSV: {e}")
    sys.exit()

# ==========================================
# 3. PROCESAR Y SUBIR
# ==========================================
batch = db.batch()
contador_batch = 0
total_subidos = 0
total_omitidos = 0

print("\n⏳ Subiendo alumnos...")

for index, row in df.iterrows():
    try:
        # 1. Obtener y limpiar DNI
        dni_raw = str(row.get('Número de DNI', '')).strip()
        dni = dni_raw.replace(" ", "").replace(".0", "")
        
        if not dni.isdigit() or len(dni) < 6:
            total_omitidos += 1
            continue

        # 2. Obtener Datos Personales
        nombres = str(row.get('Nombres', '')).strip().title()
        apellidos = str(row.get('Apellidos', '')).strip().title()
        nombre_completo = f"{apellidos} {nombres}"
        
        # 3. Obtener Datos del Colegio
        # Mapeamos los nombres exactos de las columnas de tu archivo
        institucion = str(row.get('Nombre  la Institución Educativa', 'No registrado')).strip()
        ugel = str(row.get('UGEL', '')).strip()
        gestion = str(row.get('Tipo de Gestión', '')).strip()
        
        # 4. Asignar Grado y Categoría Fijos
        grado = "4to"
        categoria = "CAT 2" # 3ro y 4to son CAT 2
        
        # 5. Objeto Alumno
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
            "docente": "No registrado" # Este CSV no tiene columna de docente
        }

        # 6. Subir (Upsert)
        doc_ref = db.collection('directorio_alumnos').document(dni)
        batch.set(doc_ref, datos_alumno)
        
        contador_batch += 1
        total_subidos += 1
        
        # Gestión del lote (batch limit 500)
        if contador_batch >= 400:
            batch.commit()
            batch = db.batch()
            contador_batch = 0
            print(f"   -> {total_subidos} alumnos sincronizados...")

    except Exception as e:
        print(f"⚠️ Error en fila {index}: {e}")
        total_omitidos += 1

# Subir remanentes
if contador_batch > 0:
    batch.commit()

print("\n" + "="*50)
print(f"🎉 IMPORTACIÓN DE 4TO GRADO COMPLETADA")
print(f"✅ Alumnos Agregados/Actualizados: {total_subidos}")
if total_omitidos > 0:
    print(f"ℹ️  Registros inválidos omitidos: {total_omitidos}")
print("="*50)
print("="*50)