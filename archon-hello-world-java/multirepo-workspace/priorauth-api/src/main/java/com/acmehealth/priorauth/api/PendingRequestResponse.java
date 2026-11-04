package com.acmehealth.priorauth.api;

import com.acmehealth.priorauth.aging.AgeBadge;
import com.acmehealth.priorauth.model.PriorAuthRequest;

import java.time.LocalDate;

/** One row of the pending list as the reviewer screen receives it (JSON). */
public record PendingRequestResponse(
        String id,
        String tenantId,
        String service,
        String status,
        LocalDate receivedAt,
        int ageBusinessDays,
        boolean overLimit,
        String ageLabel) {

    public static PendingRequestResponse from(PriorAuthRequest request, AgeBadge age) {
        return new PendingRequestResponse(request.id(), request.tenantId(), request.service(), request.status(),
                request.receivedAt(), age.businessDays(), age.overLimit(), age.label());
    }
}
