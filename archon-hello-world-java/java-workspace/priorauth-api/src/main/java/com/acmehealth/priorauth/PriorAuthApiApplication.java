package com.acmehealth.priorauth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.time.Clock;

/** Entry point. Spring Boot scans this package and below for controllers and services. */
@SpringBootApplication
public class PriorAuthApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(PriorAuthApiApplication.class, args);
    }

    /** "Today" for request ages: the JVM's default time zone. Tests replace it with a fixed clock. */
    @Bean
    Clock clock() {
        return Clock.systemDefaultZone();
    }
}
