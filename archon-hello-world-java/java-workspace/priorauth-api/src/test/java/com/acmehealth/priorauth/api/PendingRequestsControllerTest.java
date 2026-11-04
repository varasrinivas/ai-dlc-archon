package com.acmehealth.priorauth.api;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Starts the whole application in the test and calls the endpoint the way the screen does. */
@SpringBootTest
@AutoConfigureMockMvc
class PendingRequestsControllerTest {

    /** "Today" is Tue 2026-10-13 in every test, so no test depends on the real date. */
    @TestConfiguration
    static class FixedClock {
        @Bean
        @Primary
        Clock fixedClock() {
            return Clock.fixed(Instant.parse("2026-10-13T12:00:00Z"), ZoneOffset.UTC);
        }
    }

    @Autowired
    private MockMvc mvc;

    @Test
    void listsPendingRequestsOldestFirst() throws Exception {
        mvc.perform(get("/requests/pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(3))
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[0].receivedAt").value("2026-10-01"));
    }

    @Test
    void agesAsOfWorkedCheck() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-13"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(3))
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[1].id").value("PA-10244"))
                .andExpect(jsonPath("$[2].id").value("PA-10263"))
                .andExpect(jsonPath("$[0].ageBusinessDays").value(7))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(4))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(1))
                .andExpect(jsonPath("$[0].overLimit").value(true))
                .andExpect(jsonPath("$[1].overLimit").value(false))
                .andExpect(jsonPath("$[2].overLimit").value(false))
                .andExpect(jsonPath("$[0].ageLabel").value("7 bd OVER 5"))
                .andExpect(jsonPath("$[1].ageLabel").value("4 bd"))
                .andExpect(jsonPath("$[2].ageLabel").value("1 bd"))
                .andExpect(jsonPath("$[0].tenantId").value("TX-01"))
                .andExpect(jsonPath("$[0].service").value("MRI lumbar spine"))
                .andExpect(jsonPath("$[0].status").value("PENDED"))
                .andExpect(jsonPath("$[0].receivedAt").value("2026-10-01"));
    }

    @Test
    void defaultsToTodayFromClock() throws Exception {
        mvc.perform(get("/requests/pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].ageBusinessDays").value(7))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(4))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(1));
    }

    @Test
    void asOfEqualToNewestReceivedIsValid() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-09"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[2].ageBusinessDays").value(0))
                .andExpect(jsonPath("$[2].ageLabel").value("0 bd"));
    }

    @Test
    void invalidAsOfIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-13-45")).andExpect(status().isBadRequest());
        mvc.perform(get("/requests/pending").param("asOf", "yesterday")).andExpect(status().isBadRequest());
    }

    @Test
    void asOfBeforeReceivedIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-05"))
                .andExpect(status().isBadRequest())
                .andExpect(status().reason(containsString("2026-10-06")));
    }

    @Test
    void asOfAfterTodayIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-14"))
                .andExpect(status().isBadRequest())
                .andExpect(status().reason(containsString("2026-10-13")));
        mvc.perform(get("/requests/pending").param("asOf", "+999999999-12-31"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void emptyAsOfIsToday() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", ""))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].ageBusinessDays").value(7))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(4))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(1));
    }
}
