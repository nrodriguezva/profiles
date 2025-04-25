import requests
from requests.auth import HTTPBasicAuth

# Configuración
JIRA_DOMAIN = "tudominio.atlassian.net"
EMAIL = "tuemail@dominio.com"
API_TOKEN = "tu_token_api"

# Configura tu proxy aquí
proxies = {
    "http": "http://usuario:contraseña@proxy.dominio.com:puerto",
    "https": "http://usuario:contraseña@proxy.dominio.com:puerto"
}

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {
    "Accept": "application/json"
}

def obtener_tableros():
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board"
    response = requests.get(url, headers=headers, auth=auth, proxies=proxies)
    response.raise_for_status()
    return response.json().get("values", [])

def obtener_tareas_por_tablero(board_id):
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board/{board_id}/issue"
    response = requests.get(url, headers=headers, auth=auth, proxies=proxies)
    response.raise_for_status()
    return response.json().get("issues", [])

if __name__ == "__main__":
    tableros = obtener_tableros()
    for tablero in tableros:
        print(f"Tablero: {tablero['name']} (ID: {tablero['id']})")
        tareas = obtener_tareas_por_tablero(tablero['id'])
        for tarea in tareas:
            clave = tarea["key"]
            resumen = tarea["fields"]["summary"]
            estado = tarea["fields"]["status"]["name"]
            print(f"  - {clave}: {resumen} [{estado}]")
        print()
