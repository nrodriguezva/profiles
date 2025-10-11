pipeline {
    agent any
    parameters {
        string(name: 'JBOSS_CONTROLLER', defaultValue: 'saos101ea05:9990', description: 'Dirección del controller JBoss')
        string(name: 'SERVER_GROUP', defaultValue: 'main-server-group', description: 'Server group donde están las apps')
    }

    stages {
        stage('Obtener estado de las aplicaciones') {
            steps {
                script {
                    // Ejecutamos el comando en bash
                    def output = sh(
                        script: """
                            sudo -u jboss /opt/jboss-eap-7.3/bin/jboss-cli.sh --connect \
                            --controller=remote+http://${params.JBOSS_CONTROLLER} \
                            --command="/server-group=${params.SERVER_GROUP}/deployment=* :read-attribute(name=enabled)"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Resultado CLI:\n${output}"

                    // Creamos un mapa vacío
                    def appsStatus = [:]

                    // Extraemos solo las líneas con resultados tipo "nombre.war => true/false"
                    output.eachLine { line ->
                        def matcher = line =~ /"(.+\.war)"\s*=>\s*(true|false)/
                        if (matcher) {
                            def appName = matcher[0][1]
                            def status = matcher[0][2].toBoolean()
                            appsStatus[appName] = status
                        }
                    }

                    echo "Mapa de aplicaciones y su estado:\n${appsStatus}"

                    // Ejemplo: mostrar solo las que están caídas
                    def caidas = appsStatus.findAll { k, v -> v == false }
                    if (caidas) {
                        echo "⚠️ Aplicaciones caídas: ${caidas.keySet()}"
                    } else {
                        echo "✅ Todas las aplicaciones están activas."
                    }
                }
            }
        }
    }
}
