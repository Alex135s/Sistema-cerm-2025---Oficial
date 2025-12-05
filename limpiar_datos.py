import pandas as pd
import sys
import os

print("--- Procesando archivo FINAL CORRECTO ---")

archivo_entrada = 'Datoslimpios.csv'
archivo_salida = 'Resultado_Final_Limpio.csv'

if not os.path.exists(archivo_entrada):
    print(f"❌ ERROR: No encuentro '{archivo_entrada}'.")
    sys.exit()

try:
    # 1. Leer el archivo
    df = pd.read_csv(archivo_entrada, sep=';', header=1, encoding='utf-8')
    
    # 2. MAPEO EXACTO (Confirmado con tu último archivo)
    columnas_nuevas = {
        'Nombre  la Institución Educativa': 'Institución Educativa',
        'UGEL a la que pertenece su I.E.': 'UGEL',
        'Tipo de Gestión Educativa': 'Gestión',
        
        # 1ro (Sin sufijo)
        'Nombres': '1ro - Nombres', 'Apellidos': '1ro - Apellidos', 'Número de DNI': '1ro - DNI',
        # 2do (.1)
        'Nombres.1': '2do - Nombres', 'Apellidos.1': '2do - Apellidos', 'Número de DNI.1': '2do - DNI',
        # 3ro (.2)
        'Nombres.2': '3ro - Nombres', 'Apellidos.2': '3ro - Apellidos', 'Número de DNI.2': '3ro - DNI',
        # 4to (.3)
        'Nombres.3': '4to - Nombres', 'Apellidos.3': '4to - Apellidos', 'Número de DNI.3': '4to - DNI',
        # 5to (.4)
        'Nombres.4': '5to - Nombres', 'Apellidos.4': '5to - Apellidos', 'Número de DNI.4': '5to - DNI',
        
        # DOCENTE (.5) - ¡Ahora sí existe!
        'Nombres.5': 'Docente - Nombres',
        'Apellidos.5': 'Docente - Apellidos',
        'Número de DNI.5': 'Docente - DNI'
    }

    # 3. Filtrar y Renombrar
    cols_existentes = [c for c in columnas_nuevas.keys() if c in df.columns]
    df_final = df[cols_existentes].rename(columns=columnas_nuevas)

    # 4. Guardar
    df_final.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ ¡FELICIDADES! Base de datos maestra generada correctamente en '{archivo_salida}'.")
    print("El archivo incluye a todos los alumnos y sus docentes asesores.")

except Exception as e:
    print(f"❌ Error: {e}")