package com.afrikcareunited;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModule;
import org.springframework.modulith.core.ApplicationModules;
import org.springframework.modulith.docs.Documenter;

/**
 * Frontières entre modules (plan de tests, niveau « Architecture ») : aucun cycle, aucun accès aux classes
 * internes d'un autre module, aucune dépendance hors de celles déclarées dans les {@code package-info.java}.
 */
class ModularityTests {

    private static final ApplicationModules MODULES = ApplicationModules.of(AfrikCareUnitedApplication.class);

    @Test
    void modulesRespectTheirDeclaredBoundaries() {
        MODULES.verify();
    }

    @Test
    void declaresOnePackagePerFeatureOfTheM0() {
        assertThat(MODULES.stream().map(module -> module.getIdentifier().toString()))
                .containsExactlyInAnyOrder(
                        "shared",
                        "contract",
                        "session",
                        "home",
                        "identity",
                        "organization",
                        "access",
                        "membership",
                        "audit",
                        "support",
                        "notification");
    }

    @Test
    void auditAndNotificationDependOnNoBusinessModule() {
        for (String leaf : new String[] {"audit", "notification"}) {
            ApplicationModule module = MODULES.getModuleByName(leaf).orElseThrow();
            assertThat(module.getBootstrapDependencies(MODULES))
                    .map(dependency -> dependency.getIdentifier().toString())
                    .allMatch(name -> name.equals("shared") || name.equals("contract"));
        }
    }

    @Test
    void writesTheModuleDocumentation() {
        new Documenter(MODULES).writeDocumentation();
        assertThat(Path.of("target", "spring-modulith-docs")).isDirectoryContaining("glob:**/components.puml");
    }
}
