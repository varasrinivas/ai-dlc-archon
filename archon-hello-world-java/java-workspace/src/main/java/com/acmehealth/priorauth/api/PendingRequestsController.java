package com.acmehealth.priorauth.api;

import com.acmehealth.priorauth.model.PriorAuthRequest;
import com.acmehealth.priorauth.store.RequestStore;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.time.Clock;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.List;

/** GET /requests/pending: the list the reviewer screen shows, oldest first, with each request's business-day age. */
@RestController
public class PendingRequestsController {

    private static final Logger log = LoggerFactory.getLogger(PendingRequestsController.class);

    private final RequestStore store;
    private final RequestAge requestAge;
    private final Clock clock;

    public PendingRequestsController(RequestStore store, RequestAge requestAge, Clock clock) {
        this.store = store;
        this.requestAge = requestAge;
        this.clock = clock;
    }

    /**
     * {@code asOf} (yyyy-MM-dd, not after today) pins the date the age is counted to; without it, today in the
     * server's zone.
     */
    @GetMapping("/requests/pending")
    public List<PendingRequestResponse> pending(@RequestParam(required = false) String asOf) {
        List<PriorAuthRequest> pending = store.pending();
        LocalDate today = LocalDate.now(clock);
        LocalDate date;
        if (asOf == null) {
            date = today;
            for (PriorAuthRequest r : pending) {
                if (r.receivedAt().isAfter(date)) {
                    log.warn("Request {} has receivedAt {} after today {}; reporting age 0",
                            r.id(), r.receivedAt(), date);
                }
            }
        } else {
            date = parse(asOf);
            if (date.isAfter(today)) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                        "asOf " + date + " is after today " + today);
            }
            for (PriorAuthRequest r : pending) {
                if (r.receivedAt().isAfter(date)) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                            "asOf " + date + " is before receivedAt " + r.receivedAt() + " of request " + r.id());
                }
            }
        }
        return pending.stream()
                .map(r -> PendingRequestResponse.from(r, requestAge.of(r.tenantId(), r.receivedAt(), date)))
                .toList();
    }

    private static LocalDate parse(String asOf) {
        try {
            return LocalDate.parse(asOf);
        } catch (DateTimeParseException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "asOf '" + asOf + "' is not a valid yyyy-MM-dd date");
        }
    }

    /** Boot's error page hides messages; the caller needs to know what was wrong with asOf. */
    @ExceptionHandler(ResponseStatusException.class)
    ResponseEntity<ProblemDetail> badRequest(ResponseStatusException e) {
        return ResponseEntity.status(e.getStatusCode())
                .body(ProblemDetail.forStatusAndDetail(e.getStatusCode(), e.getReason()));
    }
}
