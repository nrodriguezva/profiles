import jenkins.model.*
import org.jenkinsci.plugins.scriptsecurity.scripts.*

ScriptApproval.get().approveSignature("method groovy.lang.GroovyObject invokeMethod java.lang.String java.lang.Object")
ScriptApproval.get().approveSignature("staticMethod org.codehaus.groovy.runtime.DefaultGroovyMethods println java.lang.Object")
// Agrega más firmas aquí si sabes lo que haces
