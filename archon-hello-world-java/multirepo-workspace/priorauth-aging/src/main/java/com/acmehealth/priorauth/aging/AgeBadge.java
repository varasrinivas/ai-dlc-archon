package com.acmehealth.priorauth.aging;

import java.time.LocalDate;
import java.util.Set;

/** What the reviewer sees next to a request: how long it has waited, and whether it is over the tenant's limit (FR2). */
public record AgeBadge(int businessDays, boolean overLimit, int thresholdDays) {

    public static AgeBadge of(LocalDate receivedAt, LocalDate asOf, Set<LocalDate> holidays, int thresholdDays) {
        int days = BusinessDays.between(receivedAt, asOf, holidays);
        return new AgeBadge(days, days > thresholdDays, thresholdDays);
    }

    /** "7 bd OVER 5" or "4 bd": the text the screen may show as-is. */
    public String label() {
        return businessDays + " bd" + (overLimit ? " OVER " + thresholdDays : "");
    }
}
