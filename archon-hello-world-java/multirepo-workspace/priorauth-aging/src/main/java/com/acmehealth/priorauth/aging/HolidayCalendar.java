package com.acmehealth.priorauth.aging;

import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.stereotype.Service;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDate;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * The tenant's holidays (FR1.2): one JSON file per tenant per year under resources/data
 * ({@code holidays-<tenant>-<year>.json}), the same list the nightly report uses. A tenant's calendar is the union of
 * all its years, so an age that crosses a year boundary skips both years' holidays.
 * A tenant without a file has no holidays, which is the safe default (the age is then slightly higher, never lower).
 */
@Service
public class HolidayCalendar {

    private final JsonMapper mapper;
    private final PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
    private final Map<String, Set<LocalDate>> cache = new ConcurrentHashMap<>();

    public HolidayCalendar(JsonMapper mapper) {
        this.mapper = mapper;
    }

    public Set<LocalDate> forTenant(String tenantId) {
        return cache.computeIfAbsent(tenantId, this::load);
    }

    private Set<LocalDate> load(String tenantId) {
        try {
            // ???? (exactly a four-character year), not *: tenant "TX" must not pick up "TX-01"'s files.
            Resource[] files = resolver.getResources("classpath*:data/holidays-" + tenantId + "-????.json");
            Set<LocalDate> holidays = new HashSet<>();
            for (Resource file : files) {
                try (InputStream in = file.getInputStream()) {
                    JsonNode root = mapper.readTree(in);
                    root.get("holidays").forEach(node -> holidays.add(LocalDate.parse(node.asString())));
                }
            }
            return Set.copyOf(holidays);
        } catch (IOException e) {
            throw new IllegalStateException("cannot read holidays for tenant " + tenantId, e);
        }
    }
}
