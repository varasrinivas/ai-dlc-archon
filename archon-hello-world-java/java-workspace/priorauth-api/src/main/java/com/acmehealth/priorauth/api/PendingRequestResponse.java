package com.acmehealth.priorauth.api;

import com.acmehealth.priorauth.aging.RequestAging;
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

    public static PendingRequestResponse from(PriorAuthRequest request, RequestAging aging, LocalDate asOf) {
        int age = aging.ageBusinessDays(request.tenantId(), request.receivedAt(), asOf);
        return new PendingRequestResponse(request.id(), request.tenantId(), request.service(), request.status(),
                request.receivedAt(), age, aging.overLimit(age), aging.label(age));
    }
}
