package com.acmehealth.priorauth.api;

import com.acmehealth.priorauth.aging.RequestAging;
import com.acmehealth.priorauth.model.PriorAuthRequest;
import com.acmehealth.priorauth.store.RequestStore;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.Clock;
import java.time.LocalDate;
import java.util.List;

/** GET /requests/pending: the list the reviewer screen shows, oldest first, each row with its business-day age. */
@RestController
public class PendingRequestsController {

    private final RequestStore store;
    private final RequestAging aging;
    private final Clock clock;

    public PendingRequestsController(RequestStore store, RequestAging aging, Clock clock) {
        this.store = store;
        this.aging = aging;
        this.clock = clock;
    }

    @GetMapping("/requests/pending")
    public List<PendingRequestResponse> pending(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate asOf) {
        List<PriorAuthRequest> rows = store.pending();
        LocalDate today = LocalDate.now(clock);
        if (asOf != null) {
            if (asOf.isAfter(today)) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                        "asOf " + asOf + " is after today " + today);
            }
            for (PriorAuthRequest r : rows) {
                if (r.receivedAt().isAfter(asOf)) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                            "asOf " + asOf + " is before receivedAt " + r.receivedAt() + " of " + r.id());
                }
            }
        }
        LocalDate day = asOf != null ? asOf : today;
        return rows.stream().map(r -> PendingRequestResponse.from(r, aging, day)).toList();
    }
}
