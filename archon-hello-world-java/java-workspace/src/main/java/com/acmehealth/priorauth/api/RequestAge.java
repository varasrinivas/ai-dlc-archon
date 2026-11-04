package com.acmehealth.priorauth.api;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.DayOfWeek;
import java.time.LocalDate;

/**
 * The business-day age of a request: business days after the received date, up to and including the as-of date.
 * A business day is Monday to Friday and not a holiday of the request's tenant.
 */
@Component
public class RequestAge {

    /** The age, whether it is over the threshold, and the label the screen shows. */
    public record Age(int businessDays, boolean overLimit, String label) {
    }

    private final HolidayCalendar holidays;
    private final int thresholdDays;

    public RequestAge(HolidayCalendar holidays, @Value("${priorauth.aging.threshold-days}") int thresholdDays) {
        this.holidays = holidays;
        this.thresholdDays = thresholdDays;
    }

    /** Age 0 when the as-of date is on or before the received date. */
    public Age of(String tenantId, LocalDate receivedAt, LocalDate asOf) {
        int days = 0;
        for (LocalDate d = receivedAt.plusDays(1); !d.isAfter(asOf); d = d.plusDays(1)) {
            if (d.getDayOfWeek() != DayOfWeek.SATURDAY && d.getDayOfWeek() != DayOfWeek.SUNDAY
                    && !holidays.isHoliday(tenantId, d)) {
                days++;
            }
        }
        boolean over = days > thresholdDays;
        return new Age(days, over, days + " bd" + (over ? " OVER " + thresholdDays : ""));
    }
}
