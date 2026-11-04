package com.acmehealth.priorauth.api;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Starts the whole application in the test and calls the endpoint the way the screen does. */
@SpringBootTest
@AutoConfigureMockMvc
class PendingRequestsControllerTest {

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

    @Test // FR3: the age and the flag travel with each row; 1 Oct -> 13 Oct is 7 business days (12 Oct is a TX-01 holiday)
    void eachRowCarriesItsAgeAndFlag() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-13"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[0].ageBusinessDays").value(7))
                .andExpect(jsonPath("$[0].overLimit").value(true))
                .andExpect(jsonPath("$[0].ageLabel").value("7 bd OVER 5"))
                .andExpect(jsonPath("$[1].id").value("PA-10244"))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(4))
                .andExpect(jsonPath("$[1].overLimit").value(false));
    }

    @Test // bug report 17 Oct 2026 (Ravi Menon): 1 Jan 2027 is a TX-01 holiday, so each age is one lower than before
    void newYearsDayIsNotABusinessDay() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2027-01-05"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[0].ageBusinessDays").value(62))
                .andExpect(jsonPath("$[0].ageLabel").value("62 bd OVER 5"))
                .andExpect(jsonPath("$[1].id").value("PA-10244"))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(59))
                .andExpect(jsonPath("$[2].id").value("PA-10263"))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(56));
    }

    @Test // FR1: PA-10231 arrived on 1 Oct, so an as-of of 30 Sep is the caller's error: 400, not 500
    void asOfBeforeReceivedIsABadRequest() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-09-30"))
                .andExpect(status().isBadRequest());
    }
}
