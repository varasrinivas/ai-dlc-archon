package com.acmehealth.priorauth.store;

import com.acmehealth.priorauth.model.PriorAuthRequest;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;
import java.io.InputStream;
import java.util.Comparator;
import java.util.List;

/**
 * Where the requests come from. In production this reads the queue database; here it reads the nightly export
 * packed into the jar, which is enough for the reviewer screen's contract. Existing code; unchanged by intent 261013-request-age-api.
 */
@Service
public class RequestStore {

    private final List<PriorAuthRequest> requests;

    public RequestStore(JsonMapper mapper) throws IOException {
        try (InputStream in = new ClassPathResource("data/requests.sample.json").getInputStream()) {
            List<PriorAuthRequest> loaded = mapper.readValue(in, mapper.getTypeFactory()
                    .constructCollectionType(List.class, PriorAuthRequest.class));
            this.requests = loaded.stream()
                    .sorted(Comparator.comparing(PriorAuthRequest::receivedAt).thenComparing(PriorAuthRequest::id))
                    .toList();
        }
    }

    /** Every request, oldest first. */
    public List<PriorAuthRequest> all() {
        return requests;
    }

    /** Only the requests a reviewer still has to act on, oldest first. */
    public List<PriorAuthRequest> pending() {
        return requests.stream().filter(PriorAuthRequest::isPending).toList();
    }
}
