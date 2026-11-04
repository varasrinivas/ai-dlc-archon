package com.acmehealth.priorauth.aging;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.stereotype.Component;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;
import java.io.InputStream;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Age of a request in business days: the days after the received day, up to and including the "as of" day, that are
 * not a Saturday, a Sunday or a holiday of the request's tenant. Over the limit when the age exceeds the configured
 * threshold. Holidays come from {@code data/holidays-<tenant>-<yyyy>.json}, loaded once at startup.
 */
@Component
public class RequestAging {

    private static final Logger log = LoggerFactory.getLogger(RequestAging.class);
    private static final Pattern HOLIDAY_FILE = Pattern.compile("holidays-(.+)-(\\d{4})\\.json");

    private final Map<String, Set<LocalDate>> holidaysByTenant;
    private final int thresholdDays;
    private final Set<String> warnedTenants = ConcurrentHashMap.newKeySet();

    @Autowired
    public RequestAging(JsonMapper mapper, @Value("${priorauth.aging.threshold-days}") int thresholdDays)
            throws IOException {
        this(loadHolidays(mapper), thresholdDays);
    }

    RequestAging(Map<String, Set<LocalDate>> holidaysByTenant, int thresholdDays) {
        if (thresholdDays < 0) {
            throw new IllegalArgumentException("priorauth.aging.threshold-days must be >= 0, was " + thresholdDays);
        }
        Map<String, Set<LocalDate>> copy = new HashMap<>();
        holidaysByTenant.forEach((tenant, days) -> copy.put(tenant, Set.copyOf(days)));
        this.holidaysByTenant = Map.copyOf(copy);
        this.thresholdDays = thresholdDays;
    }

    /** Business days d with receivedAt < d <= asOf; 0 when asOf is not after receivedAt. */
    public int ageBusinessDays(String tenantId, LocalDate receivedAt, LocalDate asOf) {
        if (!asOf.isAfter(receivedAt)) {
            return 0;
        }
        Set<LocalDate> holidays = holidaysOf(tenantId);
        return (int) receivedAt.plusDays(1).datesUntil(asOf.plusDays(1))
                .filter(d -> d.getDayOfWeek() != DayOfWeek.SATURDAY && d.getDayOfWeek() != DayOfWeek.SUNDAY)
                .filter(d -> !holidays.contains(d))
                .count();
    }

    public boolean overLimit(int age) {
        return age > thresholdDays;
    }

    public String label(int age) {
        return overLimit(age) ? age + " bd OVER " + thresholdDays : age + " bd";
    }

    private Set<LocalDate> holidaysOf(String tenantId) {
        Set<LocalDate> holidays = holidaysByTenant.get(tenantId);
        if (holidays == null) {
            if (warnedTenants.add(String.valueOf(tenantId))) {
                log.warn("No holiday calendar for tenant {}; its ages count weekends only", tenantId);
            }
            return Set.of();
        }
        return holidays;
    }

    private static Map<String, Set<LocalDate>> loadHolidays(JsonMapper mapper) throws IOException {
        Map<String, Set<LocalDate>> holidays = new TreeMap<>();
        Resource[] files = new PathMatchingResourcePatternResolver().getResources("classpath*:data/holidays-*.json");
        for (Resource file : files) {
            try (InputStream in = file.getInputStream()) {
                readHolidayFile(mapper, file.getFilename(), in, holidays);
            }
        }
        log.info("Loaded holiday calendars: {}", holidays.isEmpty() ? "none" : holidays.keySet());
        return holidays;
    }

    /** Reads one holiday file into {@code into}; fails with the file's name when name or content is not as expected. */
    static void readHolidayFile(JsonMapper mapper, String fileName, InputStream in, Map<String, Set<LocalDate>> into) {
        Matcher name = HOLIDAY_FILE.matcher(fileName == null ? "" : fileName);
        if (!name.matches()) {
            throw new IllegalStateException("Holiday file " + fileName + " is not named holidays-<tenant>-<yyyy>.json");
        }
        String tenant = name.group(1);
        int year = Integer.parseInt(name.group(2));
        List<LocalDate> dates;
        try {
            dates = mapper.readValue(in, mapper.getTypeFactory().constructCollectionType(List.class, LocalDate.class));
        } catch (JacksonException e) {
            throw new IllegalStateException("Holiday file " + fileName + " is not a JSON array of ISO dates", e);
        }
        if (dates == null) {
            throw new IllegalStateException("Holiday file " + fileName + " is not a JSON array of ISO dates");
        }
        for (LocalDate date : dates) {
            if (date == null || date.getYear() != year) {
                throw new IllegalStateException("Holiday file " + fileName + " holds " + date + ", not a date in " + year);
            }
        }
        into.computeIfAbsent(tenant, t -> new HashSet<>()).addAll(dates);
    }
}
