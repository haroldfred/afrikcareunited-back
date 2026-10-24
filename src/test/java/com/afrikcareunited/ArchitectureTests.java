package com.afrikcareunited;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.library.GeneralCodingRules;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZonedDateTime;

/** Règles de code vérifiées sur tout le back-end (ArchUnit). */
@AnalyzeClasses(packages = "com.afrikcareunited", importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTests {

    /** Injection par constructeur uniquement : dépendances explicites et testables. */
    @ArchTest
    static final ArchRule noFieldInjection = GeneralCodingRules.NO_CLASSES_SHOULD_USE_FIELD_INJECTION;

    /** Journaux structurés par SLF4J, jamais la sortie standard (aucune donnée personnelle dans les journaux). */
    @ArchTest
    static final ArchRule noStandardStreams = GeneralCodingRules.NO_CLASSES_SHOULD_ACCESS_STANDARD_STREAMS;

    @ArchTest
    static final ArchRule noJavaUtilLogging = GeneralCodingRules.NO_CLASSES_SHOULD_USE_JAVA_UTIL_LOGGING;

    @ArchTest
    static final ArchRule noGenericExceptions = GeneralCodingRules.NO_CLASSES_SHOULD_THROW_GENERIC_EXCEPTIONS;

    /**
     * L'heure est injectée (java.time.Clock) : les durées du M0 (72 h, 30 min, 15 min, 2 h, 12 h) sont testées
     * en avançant l'horloge, jamais en attendant.
     */
    @ArchTest
    static final ArchRule timeComesFromTheInjectedClock = noClasses()
            .should().callMethod(Instant.class, "now")
            .orShould().callMethod(LocalDate.class, "now")
            .orShould().callMethod(LocalDateTime.class, "now")
            .orShould().callMethod(OffsetDateTime.class, "now")
            .orShould().callMethod(ZonedDateTime.class, "now")
            .because("l'heure vient de l'horloge injectée (plan de tests du M0)");

    /** Le code généré depuis le contrat ne dépend d'aucun module : il ne fait que décrire l'API. */
    @ArchTest
    static final ArchRule contractDependsOnNoModule = noClasses()
            .that().resideInAPackage("com.afrikcareunited.contract..")
            .should().dependOnClassesThat().resideInAnyPackage(
                    "com.afrikcareunited.session..",
                    "com.afrikcareunited.home..",
                    "com.afrikcareunited.identity..",
                    "com.afrikcareunited.organization..",
                    "com.afrikcareunited.access..",
                    "com.afrikcareunited.membership..",
                    "com.afrikcareunited.audit..",
                    "com.afrikcareunited.support..",
                    "com.afrikcareunited.notification..");
}
