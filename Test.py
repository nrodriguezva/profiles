#!/usr/bin/env python3
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de conexión
TEA_HOST = "https://localhost"
TEA_PORT = 8777
TEA_USER = "admin"
TEA_PASS = "admin"

def get_users():
    url = f"{TEA_HOST}:{TEA_PORT}/tea/api/v1/users"
    try:
        response = requests.get(url, auth=(TEA_USER, TEA_PASS), verify=False)
        response.raise_for_status()
        users = response.json()
        print("Usuarios TEA encontrados:\n")
        print(json.dumps(users, indent=4))
    except Exception as e:
        print("⚠️ Error al obtener los usuarios de TEA:")
        print(str(e))

if __name__ == "__main__":
    get_users()
    
