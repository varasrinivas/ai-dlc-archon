package com.acmehealth.priorauth.aging;

import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

/** Bug report 17 Oct 2026 (Ravi Menon): New Year's Day 2027 was counted as a working day. */
class HolidayCalendarTest {

    private final HolidayCalendar calendar = new HolidayCalendar(JsonMapper.builder().build());

    @Test // every year's file for the tenant is loaded, not just 2026's
    void loadsEveryYearForTheTenant() {
        assertThat(calendar.forTenant("TX-01"))
                .contains(LocalDate.of(2026, 1, 1), LocalDate.of(2026, 10, 12), LocalDate.of(2027, 1, 1))
                .hasSize(22);
    }

    @Test // the existing safe default: no file, no holidays
    void tenantWithoutFilesHasNoHolidays() {
        assertThat(calendar.forTenant("ZZ-99")).isEmpty();
    }

    @Test // PA-10231, received 1 Oct 2026, as of 5 Jan 2027: 62, not 63
    void ageAcrossTheYearSkipsNewYearsDay() {
        assertThat(BusinessDays.between(LocalDate.of(2026, 10, 1), LocalDate.of(2027, 1, 5), calendar.forTenant("TX-01")))
                .isEqualTo(62);
    }
}
