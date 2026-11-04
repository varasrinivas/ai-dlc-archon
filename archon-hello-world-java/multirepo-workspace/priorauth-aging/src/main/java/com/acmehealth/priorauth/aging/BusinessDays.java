package com.acmehealth.priorauth.aging;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.Set;

/**
 * Business-day arithmetic for request age (intent 261013-request-age-api, FR1).
 * Age counts business days strictly after the received date up to and including the as-of date, so a request
 * received on Monday has age 0 on Monday and age 1 on Tuesday (assumption A-01, confirmed by Ravi Menon).
 * Weekends and the tenant's holidays are not business days (FR1.1, FR1.2).
 */
public final class BusinessDays {

    private BusinessDays() {
    }

    public static boolean isBusinessDay(LocalDate day, Set<LocalDate> holidays) {
        DayOfWeek dow = day.getDayOfWeek();
        return dow != DayOfWeek.SATURDAY && dow != DayOfWeek.SUNDAY && !holidays.contains(day);
    }

    /** Business days strictly after {@code start}, up to and including {@code end}. */
    public static int between(LocalDate start, LocalDate end, Set<LocalDate> holidays) {
        if (end.isBefore(start)) {
            throw new IllegalArgumentException("as-of date " + end + " is before the received date " + start);
        }
        int days = 0;
        for (LocalDate cursor = start.plusDays(1); !cursor.isAfter(end); cursor = cursor.plusDays(1)) {
            if (isBusinessDay(cursor, holidays)) {
                days++;
            }
        }
        return days;
    }
}
