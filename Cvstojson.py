import csv
import json

def csv_a_json(csv_file, json_file):
    data = []
    
    with open(csv_file, mode='r', encoding='utf-8') as archivo_csv:
        lector = csv.DictReader(archivo_csv)
        for fila in lector:
            persona = {
                "nombre": fila.get("nombre", "").strip(),
                "cargo": fila.get("cargo", "").strip(),
                "herramientas": [h.strip() for h in fila.get("herramientas", "").split(",") if h.strip()],
                "foto": fila.get("foto", "").strip(),
                "pais": fila.get("pais", "").strip(),
                "correo": fila.get("correo", "").strip(),
                "lider": fila.get("lider", "").strip()
            }
            data.append(persona)

    with open(json_file, mode='w', encoding='utf-8') as archivo_json:
        json.dump(data, archivo_json, indent=4, ensure_ascii=False)

# Reemplaza con tu ruta
csv_a_json('personas.csv', 'personas.json')
