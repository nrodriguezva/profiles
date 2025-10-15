pipeline {
    agent any

    environment {
        JBOSS_HOME = "/opt/jboss-eap-7.3"
        JBOSS_USER = "jboss"
        CONTROLLER = "remote+http://saos101ea05:9990"
    }

    stages {
        stage('Obtener estado de aplicaciones en JBoss') {
            steps {
                script {
                    echo "📡 Consultando aplicaciones desde el Domain Controller..."

                    // Ejecutar comando jboss-cli con salida en JSON
                    def rawJson = sh(
                        script: """
                            sudo -u ${JBOSS_USER} ${JBOSS_HOME}/bin/jboss-cli.sh \\
                            --connect \\
                            --controller=${CONTROLLER} \\
                            --output-json \\
                            --command="/server-group=*:read-children-resources(child-type=deployment)"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "🧾 Resultado crudo del CLI:"
                    echo rawJson.take(400) + (rawJson.size() > 400 ? "..." : "")

                    // Parsear el JSON
                    def json = new groovy.json.JsonSlurper().parseText(rawJson)

                    if (json.outcome != "success") {
                        error("❌ Falló la ejecución del comando CLI: ${json['failure-description']}")
                    }

                    // Recorrer resultados
                    def aplicaciones = []
                    json.result.each { serverGroup, deployments ->
                        deployments.each { appName, props ->
                            def estado = props['enabled'] ?: false
                            aplicaciones << [
                                grupo: serverGroup,
                                nombre: appName,
                                habilitada: estado
                            ]
                        }
                    }

                    if (aplicaciones.isEmpty()) {
                        echo "⚠️ No se encontraron aplicaciones desplegadas en los grupos."
                    } else {
                        echo "📋 Listado de aplicaciones encontradas:"
                        aplicaciones.each {
                            echo "- ${it.nombre} | Grupo: ${it.grupo} | Estado: ${it.habilitada ? '🟢 Activa' : '🔴 Inactiva'}"
                        }

                        // Mostrar resumen de inactivas
                        def inactivas = aplicaciones.findAll { !it.habilitada }
                        if (inactivas) {
                            echo "\n⚠️ Aplicaciones inactivas detectadas:"
                            inactivas.each { echo "- ${it.nombre} (${it.grupo})" }
                        } else {
                            echo "\n✅ Todas las aplicaciones están activas."
                        }
                    }
                }
            }
        }
    }
/host=*/server=*/:read-attribute(name=server-group)

    $JBOSS_HOME/bin/jboss-cli.sh --connect --command="/host=*/server=*/:read-resource(include-runtime=true, recursive=false)" \
| grep -E 'host =>|server =>|server-group =>' \
| awk '
    /host =>/ {host=$3}
    /server =>/ {server=$3}
    /server-group =>/ {
        group=$3
        gsub(/\"|,/, "", host)
        gsub(/\"|,/, "", server)
        gsub(/\"|,/, "", group)
        printf "%-25s | %-15s | %-15s\n", group, host, server
    }' \
| sort | uniq

    post {
        success {
            echo "✅ Pipeline finalizado correctamente."
        }
        failure {
            echo "❌ Error durante la ejecución del pipeline."
        }
    }
}

import groovy.json.JsonOutput
def jsonText = JsonOutput.toJson(data)
echo jsonText




