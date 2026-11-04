package com.acmehealth.priorauth.api;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.stereotype.Component;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * The holidays of each tenant, read once at startup from {@code data/holidays-<tenantId>-<year>.json}.
 * A file that cannot be read stops startup; a tenant or year without a file counts as having no holidays.
 */
@Component
public class HolidayCalendar {

    private static final Logger log = LoggerFactory.getLogger(HolidayCalendar.class);
    private static final String LOCATION = "classpath*:data/holidays-*.json";
    private static final String PREFIX = "holidays-";
    private static final String SUFFIX = ".json";

    /** Keyed by {@code <tenantId>-<year>}. */
    private final Map<String, Set<LocalDate>> holidays;
    private final Set<String> warnedMissing = ConcurrentHashMap.newKeySet();

    @Autowired
    public HolidayCalendar(JsonMapper mapper) {
        this(mapper, LOCATION);
    }

    HolidayCalendar(JsonMapper mapper, String locationPattern) {
        Resource[] files;
        try {
            files = new PathMatchingResourcePatternResolver().getResources(locationPattern);
        } catch (IOException e) {
            throw new IllegalStateException("Cannot list holiday files at " + locationPattern + ": " + e.getMessage(), e);
        }
        Map<String, Set<LocalDate>> loaded = new HashMap<>();
        for (Resource file : files) {
            String name = file.getFilename();
            try {
                String key = keyOf(name);
                loaded.put(key, read(mapper, file, Integer.parseInt(key.substring(key.lastIndexOf('-') + 1))));
            } catch (Exception e) {
                throw new IllegalStateException("Cannot load holiday file " + name + ": " + e.getMessage(), e);
            }
        }
        this.holidays = Map.copyOf(loaded);
    }

    /** True when the date is a holiday of that tenant. No file for the tenant and year: false, with a warning. */
    public boolean isHoliday(String tenantId, LocalDate date) {
        String key = tenantId + "-" + date.getYear();
        Set<LocalDate> dates = holidays.get(key);
        if (dates == null) {
            if (warnedMissing.add(key)) {
                log.warn("No holiday file data/{}{}{}; counting {} with weekends only", PREFIX, key, SUFFIX,
                        date.getYear());
            }
            return false;
        }
        return dates.contains(date);
    }

    /** {@code holidays-TX-01-2026.json} gives {@code TX-01-2026}; the last '-' separates the year. */
    private static String keyOf(String name) {
        if (name == null || !name.startsWith(PREFIX) || !name.endsWith(SUFFIX)) {
            throw new IllegalArgumentException("file name is not holidays-<tenantId>-<year>.json");
        }
        String key = name.substring(PREFIX.length(), name.length() - SUFFIX.length());
        int dash = key.lastIndexOf('-');
        if (dash <= 0 || !key.substring(dash + 1).matches("\\d{4}")) {
            throw new IllegalArgumentException("file name is not holidays-<tenantId>-<year>.json");
        }
        return key;
    }

    private static Set<LocalDate> read(JsonMapper mapper, Resource file, int year) throws IOException {
        try (InputStream in = file.getInputStream()) {
            List<LocalDate> dates = mapper.readValue(in, mapper.getTypeFactory()
                    .constructCollectionType(List.class, LocalDate.class));
            for (LocalDate date : dates) {
                if (date.getYear() != year) {
                    throw new IllegalArgumentException("date " + date + " is not in " + year);
                }
            }
            return Set.copyOf(dates);
        }
    }
}
