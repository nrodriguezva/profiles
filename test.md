Documento Técnico – Proceso de Automatización: Limpieza de Discos
1. Información General
Nombre del proceso: Automatización de Limpieza de Discos
Versión: 1.0
Fecha: [dd/mm/aaaa]
Responsable: [Nombre del autor o área]
Plataforma: [Windows / Linux / Mixta]
Herramientas utilizadas: [PowerShell, Bash, Jenkins, Azure DevOps, Cron, etc.]
2. Objetivo
Describir el proceso automatizado que permite realizar la limpieza periódica de discos en los servidores de la organización, con el fin de optimizar el espacio de almacenamiento, prevenir errores de capacidad y mantener el rendimiento del sistema.
3. Alcance
Este proceso aplica a los servidores [especificar nombres o tipos de servidores], ubicados en [entorno: producción / pruebas / desarrollo]. Incluye la eliminación de archivos temporales, logs antiguos y carpetas de caché no críticas.
4. Descripción General del Proceso
1. Validación de espacio disponible en disco.
2. Eliminación de archivos temporales y carpetas especificadas.
3. Compresión o eliminación de logs antiguos.
4. Generación de reporte y registro en archivo log.
5. Envío de notificación (opcional) al administrador.
5. Flujo del Proceso
+------------------------+
| Inicio del proceso     |
+-----------+------------+
            |
            v
+------------------------+
| Validar espacio disco  |
+-----------+------------+
            |
            v
+------------------------+
| Borrar temporales/logs |
+-----------+------------+
            |
            v
+------------------------+
| Generar reporte/log    |
+-----------+------------+
            |
            v
+------------------------+
| Enviar notificación    |
+-----------+------------+
            |
            v
+------------------------+
| Fin del proceso        |
+------------------------+
6. Desarrollo Técnico
6.1 Script Principal (PowerShell)
$logFile = "C:\Logs\clean_disk.log"
$targetPaths = @("C:\Temp", "C:\Windows\Temp", "C:\Logs")

Add-Content $logFile "=== Inicio limpieza $(Get-Date) ==="

foreach ($path in $targetPaths) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Add-Content $logFile "Limpieza completada en $path"
    } else {
        Add-Content $logFile "Ruta no encontrada: $path"
    }
}

Add-Content $logFile "=== Fin limpieza $(Get-Date) ==="
7. Programación del Proceso
Windows: tarea programada ejecutada con PowerShell cada domingo a las 2:00 a.m.
schtasks /create /sc weekly /d SUN /tn "LimpiezaDisco" /tr "powershell.exe -File C:\Scripts\clean_disk.ps1" /st 02:00
Linux: tarea cron configurada semanalmente:
0 2 * * 0 /usr/local/bin/clean_disk.sh
8. Validación y Resultados Esperados
Verificar que el espacio libre en disco aumente después de la ejecución.
Confirmar que no se eliminen archivos críticos del sistema.
Revisar el log de ejecución (clean_disk.log) para validar resultados.
Asegurar que las notificaciones (si existen) se envían correctamente.
9. Riesgos y Consideraciones
Asegurar permisos adecuados para ejecutar el script.
No incluir rutas del sistema operativo o aplicaciones críticas.
Probar en entorno controlado antes de desplegar en producción.
10. Historial de Cambios
Versión
Fecha
Descripción del cambio
Autor
1.0
[dd/mm/aaaa]
Creación del documento
[Nombre]


