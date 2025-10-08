pipeline {
    agent { label 'windows' }

    stages {
        stage('Validar servicios en ejecución') {
            steps {
                echo 'Listando servicios activos en Windows...'
                powershell '''
                    # Mostrar los servicios que están corriendo
                    Get-Service | Where-Object {$_.Status -eq "Running"} | 
                    Select-Object -Property Name, DisplayName, Status | 
                    Sort-Object Name | Format-Table -AutoSize
                '''
            }
        }
    }
    post {
        always {
            echo 'Verificación de servicios completada.'
        }
    }
}
@echo off
REM ============================================
REM  Script para iniciar el agente Jenkins (JNLP)
REM  Autor: Nicolas Rodriguez
REM  Fecha: 2025-10-06
REM ============================================

REM Verifica que JAVA_HOME esté configurado
if "%JAVA_HOME%"=="" (
    echo [ERROR] La variable JAVA_HOME no está configurada.
    echo Configúrala antes de ejecutar este script.
    echo Ejemplo: setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17"
    pause
    exit /b 1
)

REM Rutas y configuración
set AGENT_JAR="C:\Jenkins\agent.jar"
set JNLP_URL=https://tuservidor/jenkins/computer/mi-agente/slave-agent.jnlp
set SECRET=ABC1234567890abcdef

REM ============================================
REM Ejecutar agente Jenkins en segundo plano
REM ============================================
echo Iniciando agente Jenkins con JAVA_HOME=%JAVA_HOME% ...
start /B "%JAVA_HOME%\bin\java.exe" -Djava.net.useSystemProxies=false -jar %AGENT_JAR% -jnlpUrl %JNLP_URL% -secret %SECRET% -webSocket

echo Agente Jenkins iniciado en segundo plano.
exit
