package com.acmehealth.priorauth.api;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import tools.jackson.databind.json.JsonMapper;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(OutputCaptureExtension.class)
class RequestAgeTest {

    private final RequestAge age = new RequestAge(new HolidayCalendar(JsonMapper.builder().build()), 5);

    private RequestAge.Age tx01(String receivedAt, String asOf) {
        return age.of("TX-01", LocalDate.parse(receivedAt), LocalDate.parse(asOf));
    }

    @Test
    void workedCheckAsOf20261013() {
        assertThat(tx01("2026-10-01", "2026-10-13")).isEqualTo(new RequestAge.Age(7, true, "7 bd OVER 5"));
        assertThat(tx01("2026-10-06", "2026-10-13")).isEqualTo(new RequestAge.Age(4, false, "4 bd"));
        assertThat(tx01("2026-10-09", "2026-10-13")).isEqualTo(new RequestAge.Age(1, false, "1 bd"));
    }

    @Test
    void receivedDayIsZero() {
        assertThat(tx01("2026-10-13", "2026-10-13")).isEqualTo(new RequestAge.Age(0, false, "0 bd"));
    }

    @Test
    void weekendIsNotCounted() {
        assertThat(tx01("2026-10-16", "2026-10-19").businessDays()).isEqualTo(1);
    }

    @Test
    void holidayIsNotCounted() {
        assertThat(tx01("2026-10-09", "2026-10-13").businessDays()).isEqualTo(1);
    }

    @Test
    void saturdayReceiptIsOneOnMonday() {
        assertThat(tx01("2026-10-17", "2026-10-19").businessDays()).isEqualTo(1);
    }

    @Test
    void thresholdIsStrictlyGreater() {
        assertThat(tx01("2026-10-01", "2026-10-08")).isEqualTo(new RequestAge.Age(5, false, "5 bd"));
        assertThat(tx01("2026-10-01", "2026-10-09")).isEqualTo(new RequestAge.Age(6, true, "6 bd OVER 5"));
    }

    @Test
    void asOfBeforeReceivedIsZero() {
        assertThat(tx01("2026-10-09", "2026-10-08")).isEqualTo(new RequestAge.Age(0, false, "0 bd"));
    }

    @Test
    void tenantWithoutFileCountsWeekendsOnlyAndWarns(CapturedOutput output) {
        RequestAge.Age result = age.of("OK-02", LocalDate.parse("2026-10-09"), LocalDate.parse("2026-10-13"));

        assertThat(result.businessDays()).isEqualTo(2);
        assertThat(output).contains("holidays-OK-02-2026.json");
    }

    @Test
    void yearWithoutFileCountsWeekendsOnly() {
        assertThat(tx01("2026-12-31", "2027-01-04").businessDays()).isEqualTo(2);
    }
}
