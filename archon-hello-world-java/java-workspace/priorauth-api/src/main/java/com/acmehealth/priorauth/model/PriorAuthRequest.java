package com.acmehealth.priorauth.model;

import java.time.LocalDate;
import java.util.Set;

/** One prior-authorization request as it sits in the queue. Existing code; unchanged by intent 261013-request-age-api. */
public record PriorAuthRequest(
        String id,
        String tenantId,
        String memberId,
        String service,
        String status,
        LocalDate receivedAt) {

    private static final Set<String> PENDING_STATUSES = Set.of("PENDED", "IN_REVIEW");

    /** A reviewer still has to act on it. */
    public boolean isPending() {
        return PENDING_STATUSES.contains(status);
    }
}
