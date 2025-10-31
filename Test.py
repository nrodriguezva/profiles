#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import tibco.tea

def main():
    try:
        # Parámetros de conexión a TEA
        tea_url = "https://localhost:8777"  # Cambia por la URL real de tu TEA
        username = "admin"                  # Usuario con permisos de administración
        password = "admin"                  # Contraseña

        # Crear cliente de conexión
        client = tibco.tea.TEAClient(tea_url, username, password)

        # Obtener lista de usuarios
        response = client.get("users")
        users = json.loads(response.text)

        print("\n=== Usuarios registrados en TEA ===\n")
        for user in users.get("items", []):
            print(f"Usuario: {user.get('name')}")
            print(f"  Rol: {user.get('role')}")
            print(f"  Email: {user.get('email')}")
            print("-" * 40)

    except Exception as e:
        print("❌ Error al obtener los usuarios de TEA:")
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
  
