package com.acmehealth.priorauth.aging;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/** One test per requirement (Minimal test strategy), intent 261013-request-age-api. */
class BusinessDaysTest {

    private static final Set<LocalDate> NO_HOLIDAYS = Set.of();
    private static final LocalDate MON_12_OCT = LocalDate.of(2026, 10, 12);

    @Test // FR1, A-01: the day a request arrives is day 0
    void receivedTodayHasAgeZero() {
        assertThat(BusinessDays.between(MON_12_OCT, MON_12_OCT, NO_HOLIDAYS)).isZero();
        assertThat(BusinessDays.between(MON_12_OCT, MON_12_OCT.plusDays(1), NO_HOLIDAYS)).isEqualTo(1);
    }

    @Test // FR1.1: Saturday and Sunday do not count
    void weekendIsNotCounted() {
        LocalDate fri9 = LocalDate.of(2026, 10, 9);
        assertThat(BusinessDays.between(fri9, MON_12_OCT, NO_HOLIDAYS)).isEqualTo(1);
    }

    @Test // FR1.2: a tenant holiday does not count
    void tenantHolidayIsNotCounted() {
        LocalDate fri9 = LocalDate.of(2026, 10, 9);
        assertThat(BusinessDays.between(fri9, MON_12_OCT, Set.of(MON_12_OCT))).isZero();
    }

    @Test // FR1: an as-of date before the received date is a caller error, not an age of -1
    void asOfBeforeReceivedIsAnError() {
        assertThatThrownBy(() -> BusinessDays.between(MON_12_OCT, MON_12_OCT.minusDays(1), NO_HOLIDAYS))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
