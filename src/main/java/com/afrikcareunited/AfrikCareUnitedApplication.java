package com.afrikcareunited;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.modulith.Modulithic;

/**
 * AfrikCareUnited — back-end et BFF, monolithe modulaire (D-04, D-25).
 *
 * <p>Chaque paquet direct de {@code com.afrikcareunited} est un module applicatif Spring Modulith : ses classes
 * publiques de premier niveau forment son interface, ses sous-paquets sont internes. Les dépendances permises
 * sont déclarées dans le {@code package-info.java} de chaque module et vérifiées par {@code ModularityTests}.
 */
@Modulithic(systemName = "AfrikCareUnited", sharedModules = {"shared", "contract"})
@SpringBootApplication
public class AfrikCareUnitedApplication {

    public static void main(String[] args) {
        SpringApplication.run(AfrikCareUnitedApplication.class, args);
    }
}
