package com.acmehealth.priorauth.store;

import com.acmehealth.priorauth.model.PriorAuthRequest;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/** Existing tests; unchanged by intent 261013-request-age-api. */
class RequestStoreTest {

    private final RequestStore store = new RequestStore(JsonMapper.builder().build());

    RequestStoreTest() throws IOException {
    }

    @Test
    void loadsTheSampleOldestFirst() {
        List<PriorAuthRequest> all = store.all();
        assertThat(all).hasSize(4);
        assertThat(all.get(0).id()).isEqualTo("PA-10231");
        assertThat(all.get(3).id()).isEqualTo("PA-10263");
    }

    @Test
    void pendingExcludesDecidedRequests() {
        assertThat(store.pending()).extracting(PriorAuthRequest::id)
                .containsExactly("PA-10231", "PA-10244", "PA-10263");
    }
}
