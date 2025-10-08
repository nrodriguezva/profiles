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
