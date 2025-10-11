pipeline {
    agent any

    parameters {
        string(name: 'SERVIDOR_CONTROLADOR', defaultValue: 'saos101ea01p', description: 'Servidor principal JBoss (Domain Controller o Standalone)')
        string(name: 'USUARIO_JBOSS', defaultValue: 'admin', description: 'Usuario de conexión a JBoss CLI')
        password(name: 'PASSWORD_JBOSS', description: 'Contraseña del usuario JBoss')
        string(name: 'APLICACION', defaultValue: 'mi-aplicacion.war', description: 'Nombre del despliegue en JBoss')
        string(name: 'SERVER_GROUP', defaultValue: 'main-server-group', description: 'Server group o nodo (en modo domain)')
        choice(name: 'MODO', choices: ['restart', 'stop', 'start'], description: 'Acción a ejecutar sobre la aplicación')
        booleanParam(name: 'RESTART_COMPLETO', defaultValue: false, description: 'Reiniciar todo el grupo de servidores en lugar de solo la aplicación')
    }

    environment {
        JBOSS_HOME = '/opt/jboss-eap'
    }

    stages {
        stage('Verificar conexión') {
            steps {
                script {
                    echo "Verificando conexión con ${params.SERVIDOR_CONTROLADOR}..."
                    def result = sh(
                        script: """
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command=':read-attribute(name=server-state)' || echo "error"
                        """,
                        returnStdout: true
                    ).trim()

                    if (result.contains("error") || result == "") {
                        error "❌ No se pudo conectar al controlador JBoss en ${params.SERVIDOR_CONTROLADOR}"
                    } else {
                        echo "✅ Conexión establecida correctamente con ${params.SERVIDOR_CONTROLADOR}"
                    }
                }
            }
        }

        stage('Ejecutar acción') {
            steps {
                script {
                    echo "Acción solicitada: ${params.MODO}"
                    echo "Aplicación: ${params.APLICACION}"
                    echo "Server Group: ${params.SERVER_GROUP}"
                    echo "Restart completo: ${params.RESTART_COMPLETO}"

                    if (params.RESTART_COMPLETO) {
                        echo "🔁 Reinicio completo del grupo de servidores antes de reiniciar la aplicación..."
                        sh """
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command='/server-group=${params.SERVER_GROUP}:restart-servers(blocking=true)'
                        """
                        echo "🟢 Servidores reiniciados exitosamente."
                    }

                    if (params.MODO == "stop") {
                        sh """
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command='/server-group=${params.SERVER_GROUP}/deployment=${params.APLICACION}:stop'
                        """
                    } else if (params.MODO == "start") {
                        sh """
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command='/server-group=${params.SERVER_GROUP}/deployment=${params.APLICACION}:start'
                        """
                    } else if (params.MODO == "restart") {
                        sh """
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command='/server-group=${params.SERVER_GROUP}/deployment=${params.APLICACION}:stop'
                            sleep 10
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command='/server-group=${params.SERVER_GROUP}/deployment=${params.APLICACION}:start'
                        """
                    }
                }
            }
        }

        stage('Verificar estado de la aplicación') {
            steps {
                script {
                    echo "📊 Verificando estado de ${params.APLICACION}..."
                    def status = sh(
                        script: """
                            sudo -u Svc.Br.P.Jboss ${env.JBOSS_HOME}/bin/jboss-cli.sh \
                            --controller=${params.SERVIDOR_CONTROLADOR}:9990 \
                            --user=${params.USUARIO_JBOSS} \
                            --password='${params.PASSWORD_JBOSS}' \
                            --command='/server-group=${params.SERVER_GROUP}/deployment=${params.APLICACION}:read-attribute(name=status)'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "📋 Estado actual: ${status}"

                    if (!status.contains("OK") && !status.contains("STARTED")) {
                        error "❌ La aplicación no se encuentra operativa después del proceso."
                    } else {
                        echo "✅ La aplicación ${params.APLICACION} está operativa (verde)."
                    }
                }
            }
        }
    }

    post {
        always {
            echo "🔚 Pipeline finalizado. Puedes verificar la consola JBoss: http://${params.SERVIDOR_CONTROLADOR}:9990"
        }
    }
}
