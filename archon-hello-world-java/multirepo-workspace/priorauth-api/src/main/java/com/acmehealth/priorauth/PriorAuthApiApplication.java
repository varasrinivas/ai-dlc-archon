package com.acmehealth.priorauth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point. Spring Boot scans this package and below for controllers and services. */
@SpringBootApplication
public class PriorAuthApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(PriorAuthApiApplication.class, args);
    }
}
