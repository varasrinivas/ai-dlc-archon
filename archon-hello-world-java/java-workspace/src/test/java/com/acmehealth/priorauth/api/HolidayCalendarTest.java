package com.acmehealth.priorauth.api;

import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class HolidayCalendarTest {

    private static final JsonMapper MAPPER = JsonMapper.builder().build();

    @Test
    void loadsTheTx01File() {
        HolidayCalendar calendar = new HolidayCalendar(MAPPER);

        assertThat(calendar.isHoliday("TX-01", LocalDate.parse("2026-10-12"))).isTrue();
        assertThat(calendar.isHoliday("TX-01", LocalDate.parse("2026-10-13"))).isFalse();
        List.of("2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-07-03", "2026-09-07", "2026-10-12",
                        "2026-11-11", "2026-11-26", "2026-11-27", "2026-12-25")
                .forEach(d -> assertThat(calendar.isHoliday("TX-01", LocalDate.parse(d))).as(d).isTrue());
    }

    @Test
    void unparsableFileStopsStartup() {
        assertThatThrownBy(() -> new HolidayCalendar(MAPPER, "classpath*:holidays-bad/holidays-*.json"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("holidays-XX-01-2026.json");
    }

    @Test
    void dateOutsideTheFilesYearStopsStartup() {
        assertThatThrownBy(() -> new HolidayCalendar(MAPPER, "classpath*:holidays-wrong-year/holidays-*.json"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("holidays-XX-01-2026.json")
                .hasMessageContaining("2027-01-01");
    }
}
