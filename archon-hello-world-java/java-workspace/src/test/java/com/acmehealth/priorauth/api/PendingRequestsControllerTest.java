package com.acmehealth.priorauth.api;

import com.acmehealth.priorauth.store.RequestStore;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.context.bean.override.convention.TestBean;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.json.JsonMapper;

import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Starts the whole application in the test and calls the endpoint the way the screen does. */
@SpringBootTest
@AutoConfigureMockMvc
class PendingRequestsControllerTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private RequestAge requestAge;

    /** Today is pinned to Tue 2026-10-13, noon, in the server's zone. */
    @TestBean
    private Clock clock;

    static Clock clock() {
        return fixedAt("2026-10-13");
    }

    private static Clock fixedAt(String date) {
        ZoneId zone = ZoneId.systemDefault();
        return Clock.fixed(LocalDate.parse(date).atTime(LocalTime.NOON).atZone(zone).toInstant(), zone);
    }

    @Test
    void listsPendingRequestsOldestFirst() throws Exception {
        mvc.perform(get("/requests/pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(3))
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[0].receivedAt").value("2026-10-01"));
    }

    @Test
    void agesAsOfAGivenDate() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-13"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(3))
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[0].ageBusinessDays").value(7))
                .andExpect(jsonPath("$[0].overLimit").value(true))
                .andExpect(jsonPath("$[0].ageLabel").value("7 bd OVER 5"))
                .andExpect(jsonPath("$[1].id").value("PA-10244"))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(4))
                .andExpect(jsonPath("$[1].overLimit").value(false))
                .andExpect(jsonPath("$[1].ageLabel").value("4 bd"))
                .andExpect(jsonPath("$[2].id").value("PA-10263"))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(1))
                .andExpect(jsonPath("$[2].overLimit").value(false))
                .andExpect(jsonPath("$[2].ageLabel").value("1 bd"));
    }

    @Test
    void agesAsOfTodayWithoutAsOf() throws Exception {
        mvc.perform(get("/requests/pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value("PA-10231"))
                .andExpect(jsonPath("$[0].tenantId").value("TX-01"))
                .andExpect(jsonPath("$[0].service").exists())
                .andExpect(jsonPath("$[0].status").value("PENDED"))
                .andExpect(jsonPath("$[0].receivedAt").value("2026-10-01"))
                .andExpect(jsonPath("$[0].ageBusinessDays").value(7))
                .andExpect(jsonPath("$[0].overLimit").value(true))
                .andExpect(jsonPath("$[0].ageLabel").value("7 bd OVER 5"))
                .andExpect(jsonPath("$[1].ageBusinessDays").value(4))
                .andExpect(jsonPath("$[1].ageLabel").value("4 bd"))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(1))
                .andExpect(jsonPath("$[2].ageLabel").value("1 bd"));
    }

    @Test
    void invalidAsOfIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "13-10-2026"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value(containsString("asOf")))
                .andExpect(jsonPath("$.detail").value(containsString("13-10-2026")));
    }

    @Test
    void emptyAsOfIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", ""))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value(containsString("asOf")));
    }

    @Test
    void asOfAfterTodayIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-14"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value(containsString("2026-10-14")))
                .andExpect(jsonPath("$.detail").value(containsString("after today")));
    }

    @Test
    void farFutureAsOfIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "+999999999-12-31"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void asOfBeforeAReceivedDateIs400() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-08"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value(containsString("PA-10263")));
    }

    @Test
    void asOfOnAReceivedDateIsAgeZero() throws Exception {
        mvc.perform(get("/requests/pending").param("asOf", "2026-10-09"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[2].id").value("PA-10263"))
                .andExpect(jsonPath("$[2].ageBusinessDays").value(0))
                .andExpect(jsonPath("$[2].overLimit").value(false))
                .andExpect(jsonPath("$[2].ageLabel").value("0 bd"));
    }

    @Test
    void todayBeforeAReceivedDateIsAgeZeroNotAnError() throws Exception {
        PendingRequestsController controller = new PendingRequestsController(
                new RequestStore(JsonMapper.builder().build()), requestAge, fixedAt("2026-10-08"));

        List<PendingRequestResponse> rows = controller.pending(null);

        assertThat(rows).hasSize(3);
        assertThat(rows.get(2).id()).isEqualTo("PA-10263");
        assertThat(rows.get(2).ageBusinessDays()).isZero();
        assertThat(rows.get(2).overLimit()).isFalse();
        assertThat(rows.get(2).ageLabel()).isEqualTo("0 bd");
    }
}
