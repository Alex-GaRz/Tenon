import os
import glob

# Ruta donde están tus RFCs
SEARCH_PATH = "docs/rfcs/*.md"

def repair_mojibake(text):
    try:
        # Esta es la magia: revierte la interpretación errónea de Windows-1252 sobre UTF-8
        # Convierte los caracteres "feos" de vuelta a sus bytes originales y los relee como UTF-8
        return text.encode('cp1252').decode('utf-8')
    except Exception:
        # Fallback manual por si algún caracter no entra en el estándar CP1252
        replacements = {
            'Ã³': 'ó',
            'Ã¡': 'á',
            'Ã©': 'é',
            'Ã': 'í',  # A veces la í se rompe raro, este es un caso común
            'Ãº': 'ú',
            'Ã±': 'ñ',
            'Ã“': 'Ó',
            'ÃNH': 'Ñ',
            'â€”': '—',
            'â€“': '–',
            'â€œ': '“',
            'â€': '”',
            'Â': '' # Caracter fantasma común
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

def fix_files():
    files = glob.glob(SEARCH_PATH)
    print(f"Encontrados {len(files)} archivos en {SEARCH_PATH}...")

    for file_path in files:
        try:
            # 1. Leer el archivo tal cual está ahora (con los caracteres rotos)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 2. Aplicar la reparación
            fixed_content = repair_mojibake(content)

            # 3. Validar si necesitamos corregir los encabezados para el CI también
            # (Aseguramos que '## Propósito' esté limpio)
            if "## PropÃ³sito" in content:
                 print(f"🔧 Reparando codificación en: {file_path}")
            
            # 4. Sobrescribir el archivo con el contenido arreglado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")

    print("✅ Reparación completada. Revisa tus archivos.")

if __name__ == "__main__":
    fix_files()