import csv
import json

def csv_a_json(csv_file, json_file):
    data = []
    
    with open(csv_file, mode='r', encoding='utf-8') as archivo_csv:
        lector = csv.DictReader(archivo_csv)
        for fila in lector:
            data.append(fila)
    
    with open(json_file, mode='w', encoding='utf-8') as archivo_json:
        json.dump(data, archivo_json, indent=4, ensure_ascii=False)

# Cambia estos nombres por los tuyos
csv_a_json('personas.csv', 'personas.json')
