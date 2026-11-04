package com.acmehealth.priorauth.api;

import com.acmehealth.priorauth.aging.AgeBadge;
import com.acmehealth.priorauth.aging.HolidayCalendar;
import com.acmehealth.priorauth.store.RequestStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.util.List;

/** GET /requests/pending[?asOf=YYYY-MM-DD]: the list the reviewer screen shows, oldest first, with its age (FR3). */
@RestController
public class PendingRequestsController {

    private final RequestStore store;
    private final HolidayCalendar holidays;
    private final int thresholdDays;

    public PendingRequestsController(RequestStore store, HolidayCalendar holidays,
                                     @Value("${priorauth.aging.threshold-days:5}") int thresholdDays) {
        this.store = store;
        this.holidays = holidays;
        this.thresholdDays = thresholdDays;
    }

    @GetMapping("/requests/pending")
    public List<PendingRequestResponse> pending(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate asOf) {
        LocalDate day = asOf != null ? asOf : LocalDate.now();
        try {
            return store.pending().stream()
                    .map(r -> PendingRequestResponse.from(r,
                            AgeBadge.of(r.receivedAt(), day, holidays.forTenant(r.tenantId()), thresholdDays)))
                    .toList();
        } catch (IllegalArgumentException e) { // FR1: an as-of date before a received date is the caller's error
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, e.getMessage(), e);
        }
    }
}
