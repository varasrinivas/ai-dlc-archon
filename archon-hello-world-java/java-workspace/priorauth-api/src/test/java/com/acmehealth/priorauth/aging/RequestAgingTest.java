package com.acmehealth.priorauth.aging;

import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/** The business-day rule on its own, without Spring. */
class RequestAgingTest {

    private static final String TX = "TX-01";
    private final RequestAging aging = new RequestAging(Map.of(TX, Set.of(d("2026-10-12"))), 5);

    @Test
    void sameDayIsZero() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-13"), d("2026-10-13"))).isZero();
    }

    @Test
    void weekendIsSkipped() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-02"), d("2026-10-05"))).isEqualTo(1);
    }

    @Test
    void holidayIsSkipped() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-09"), d("2026-10-13"))).isEqualTo(1);
        assertThat(aging.ageBusinessDays("NO-CAL", d("2026-10-09"), d("2026-10-13"))).isEqualTo(2);
    }

    @Test
    void weekendReceiptStartsNextBusinessDay() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-03"), d("2026-10-05"))).isEqualTo(1);
    }

    @Test
    void asOfOnWeekendAddsNothing() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-01"), d("2026-10-03"))).isEqualTo(1);
        assertThat(aging.ageBusinessDays(TX, d("2026-10-01"), d("2026-10-04"))).isEqualTo(1);
    }

    @Test
    void asOfBeforeReceivedIsZero() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-13"), d("2026-10-12"))).isZero();
    }

    @Test
    void workedCheckAges() {
        assertThat(aging.ageBusinessDays(TX, d("2026-10-01"), d("2026-10-13"))).isEqualTo(7);
        assertThat(aging.ageBusinessDays(TX, d("2026-10-06"), d("2026-10-13"))).isEqualTo(4);
        assertThat(aging.ageBusinessDays(TX, d("2026-10-09"), d("2026-10-13"))).isEqualTo(1);
    }

    @Test
    void thresholdBoundary() {
        assertThat(aging.overLimit(5)).isFalse();
        assertThat(aging.label(5)).isEqualTo("5 bd");
        assertThat(aging.overLimit(6)).isTrue();
        assertThat(aging.label(6)).isEqualTo("6 bd OVER 5");
        assertThat(aging.label(0)).isEqualTo("0 bd");
        assertThat(new RequestAging(Map.of(), 3).label(7)).isEqualTo("7 bd OVER 3");
    }

    @Test
    void negativeThresholdFails() {
        assertThatThrownBy(() -> new RequestAging(Map.of(), -1)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void loadsTheTx01Calendar() throws Exception {
        RequestAging real = new RequestAging(JsonMapper.builder().build(), 5);
        assertThat(real.ageBusinessDays(TX, d("2026-10-09"), d("2026-10-13"))).isEqualTo(1);
        assertThat(real.ageBusinessDays(TX, d("2026-11-25"), d("2026-11-30"))).isEqualTo(1);
    }

    @Test
    void malformedHolidayFileFails() {
        JsonMapper mapper = JsonMapper.builder().build();
        Map<String, Set<LocalDate>> into = new HashMap<>();
        assertThatThrownBy(() -> RequestAging.readHolidayFile(mapper, "holidays-TX-01-2026.json",
                json("{\"not\": \"an array\"}"), into))
                .isInstanceOf(IllegalStateException.class).hasMessageContaining("holidays-TX-01-2026.json");
        assertThatThrownBy(() -> RequestAging.readHolidayFile(mapper, "holidays-TX-01.json", json("[]"), into))
                .isInstanceOf(IllegalStateException.class).hasMessageContaining("holidays-TX-01.json");
        assertThatThrownBy(() -> RequestAging.readHolidayFile(mapper, "holidays-TX-01-2026.json",
                json("[\"2027-01-01\"]"), into))
                .isInstanceOf(IllegalStateException.class);
        assertThat(into).isEmpty();
    }

    private static LocalDate d(String iso) {
        return LocalDate.parse(iso);
    }

    private static InputStream json(String s) {
        return new ByteArrayInputStream(s.getBytes(StandardCharsets.UTF_8));
    }
}
