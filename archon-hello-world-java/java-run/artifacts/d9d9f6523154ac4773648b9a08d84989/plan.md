# Plan: request age on the pending list (API)

Source: `requirements.md` (revision 2) and the code in `priorauth-api/` (`main`, clean, version 1.0.2, no tags).

- Repo: `priorauth-api`. Branch: **`request-age/pending-age`** from `main`. PR base: `main`.
- **No new dependency; `pom.xml` unchanged** (version stays 1.0.2, FR13/NFR1). Everything below uses `java.time`,
  Spring (`@Value`, `@RequestParam`, `@DateTimeFormat`, `ResponseStatusException`, `PathMatchingResourcePatternResolver`)
  and the Jackson 3 `JsonMapper` already injected into `RequestStore` (it already reads `LocalDate`, so no extra module).
- **Not touched** (NFR5): `PriorAuthRequest`, `RequestStore`, `RequestStoreTest`, `requests.sample.json`.

## Design in one paragraph

A new Spring component `RequestAging` (package `com.acmehealth.priorauth.aging`) holds the threshold and the
per-tenant holiday sets, loaded once at startup, and answers three questions: `ageBusinessDays(tenantId, receivedAt,
asOf)`, `overLimit(age)` and `label(age)`. The controller takes an optional `asOf`, falls back to `LocalDate.now(clock)`
from a new `Clock` bean, rejects an explicit `asOf` earlier than any returned row's `receivedAt` with 400, and maps each
row through `PendingRequestResponse.from(request, aging, asOf)`, which appends the three new fields. Row set and order
come from `store.pending()` unchanged (FR12).

## Files to add or change (in priorauth-api)

### 1. Add `src/main/resources/data/holidays-TX-01-2026.json` (FR7, FR8, A-08)
A plain JSON array of the 11 ISO dates, exactly:
`["2026-01-01","2026-01-19","2026-02-16","2026-05-25","2026-07-03","2026-09-07","2026-10-12","2026-11-11","2026-11-26","2026-11-27","2026-12-25"]`

### 2. Change `src/main/resources/application.yml` (FR6)
Add:
```yaml
priorauth:
  aging:
    threshold-days: 5
```

### 3. Add `src/main/java/com/acmehealth/priorauth/aging/RequestAging.java` (FR1–FR8, NFR6)
`@Component`, two constructors:
- **Spring constructor** (`@Autowired`): `RequestAging(JsonMapper mapper, @Value("${priorauth.aging.threshold-days}") int thresholdDays)`.
  Reads every `classpath*:data/holidays-*.json` with `PathMatchingResourcePatternResolver`; takes tenant and year from the
  file name with `holidays-(.+)-(\d{4})\.json` (tenant ids contain `-`, e.g. `TX-01`, so the tenant group is greedy and
  the year is the last 4 digits); parses each file as `List<LocalDate>` (same `constructCollectionType` style as
  `RequestStore`) and merges into `Map<String, Set<LocalDate>>` (so a 2027 file is data, not code, A-05).
  Fails fast (NFR6): a file whose name does not match the pattern, that is not a JSON array of ISO dates, or that holds
  a date whose year differs from the file name's year → `IllegalStateException` naming the file; Spring then refuses to
  start. A missing `priorauth.aging.threshold-days` already stops startup (no default in `@Value`); a non-integer value
  fails conversion. Logs at INFO which tenants/years were loaded.
- **Package-private constructor** for unit tests: `RequestAging(Map<String, Set<LocalDate>> holidaysByTenant, int thresholdDays)`;
  the Spring constructor delegates to it. It throws `IllegalArgumentException` when `thresholdDays < 0` (NFR6).
- `int ageBusinessDays(String tenantId, LocalDate receivedAt, LocalDate asOf)`: returns 0 if `asOf` is not after
  `receivedAt` (covers same-day and A-03's future row without `asOf`); otherwise counts
  `receivedAt.plusDays(1).datesUntil(asOf.plusDays(1))` that are not SATURDAY/SUNDAY and not in the tenant's set (FR1–FR3).
  Unknown tenant → empty set, weekends only, and a WARN logged once per tenant (A-04; see question Q1 below).
- `boolean overLimit(int age)`: `age > thresholdDays` (FR4).
- `String label(int age)`: `overLimit ? age + " bd OVER " + thresholdDays : age + " bd"` (FR5, A-02).

The day loop is at most a few hundred iterations per row for realistic ages; no caching or arithmetic shortcut.

### 4. Change `src/main/java/com/acmehealth/priorauth/PriorAuthApiApplication.java` (FR9)
Add one bean: `@Bean Clock clock() { return Clock.systemDefaultZone(); }` (A-06: JVM default zone). This is the only
`Clock` in the app; tests override it (see step 7).

### 5. Change `src/main/java/com/acmehealth/priorauth/api/PendingRequestResponse.java` (FR1, FR4, FR5, FR13)
Append three components after `receivedAt` (existing ones unchanged in name, type, order):
`int ageBusinessDays, boolean overLimit, String ageLabel`.
Replace `from(PriorAuthRequest)` with `from(PriorAuthRequest request, RequestAging aging, LocalDate asOf)`, which
computes the age once and fills flag and label from it. Only the controller calls `from` (scan), so nothing else breaks.

### 6. Change `src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java` (FR9–FR12)
- Constructor gains `RequestAging aging` and `Clock clock`.
- `pending(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate asOf)`.
  An unparsable value raises Spring's `MethodArgumentTypeMismatchException`, which Spring MVC already answers with
  **400** (FR10) — no handler code added.
- `List<PriorAuthRequest> rows = store.pending();` If `asOf != null` and some row has `receivedAt.isAfter(asOf)`, throw
  `new ResponseStatusException(HttpStatus.BAD_REQUEST, "asOf " + asOf + " is before receivedAt " + r.receivedAt() + " of " + r.id())`
  for the first such row (FR11, A-03: whole call, no partial list). Without `asOf` no such check (A-03).
- `LocalDate day = asOf != null ? asOf : LocalDate.now(clock);` then map every row with
  `PendingRequestResponse.from(r, aging, day)`. No filtering, sorting or other behavior by age (FR12).

### 7. Tests

**Add `src/test/java/com/acmehealth/priorauth/aging/RequestAgingTest.java`** — plain JUnit 5 + AssertJ, no Spring;
built with the package-private constructor, TX-01 = `{2026-10-12}`, threshold 5 (NFR4):
- `sameDayIsZero`: received 2026-10-13, asOf 2026-10-13 → 0.
- `weekendIsSkipped`: received Fri 2026-10-02, asOf Mon 2026-10-05 → 1.
- `holidayIsSkipped`: received Fri 2026-10-09, asOf Tue 2026-10-13 → 1 (10-10/11 weekend, 10-12 holiday);
  and the same dates for an unknown tenant → 2 (proves the holiday, not the weekend, made the difference; A-04).
- `weekendReceiptStartsNextBusinessDay`: received Sat 2026-10-03, asOf Mon 2026-10-05 → 1.
- `asOfOnWeekendAddsNothing`: received Thu 2026-10-01, asOf Sat 2026-10-03 and Sun 2026-10-04 → both 1 (FR3).
- `asOfBeforeReceivedIsZero`: received 2026-10-13, asOf 2026-10-12 → 0 (A-03 default-date case).
- `worked check ages`: 10-01→7, 10-06→4, 10-09→1 as of 10-13 (same numbers as the controller test, at unit level).
- `thresholdBoundary`: `overLimit(5)` false / `label(5)` = `"5 bd"`; `overLimit(6)` true / `label(6)` = `"6 bd OVER 5"`;
  `label(0)` = `"0 bd"`; with threshold 3, `label(7)` = `"7 bd OVER 3"` (threshold from config, not a literal 5).
- `negativeThresholdFails`: threshold -1 → `IllegalArgumentException` (NFR6).
- `loadsTheTx01Calendar`: Spring-style constructor with `JsonMapper.builder().build()` and threshold 5 reads the real
  resource; assert received 2026-10-09 / asOf 2026-10-13 → 1 for TX-01 and that a known 2026 holiday from another month
  (e.g. received Wed 2026-11-25, asOf Mon 2026-11-30 → 1, since 11-26 and 11-27 are holidays) is honored (FR8).
- `malformedHolidayFileFails`: the parsing step is a package-private static method taking the file name and an
  `InputStream`; feed it `{"not": "an array"}` and a bad file name → `IllegalStateException` (NFR6). No malformed file
  is put on the test classpath (it would break every Spring test).

**Change `src/test/java/com/acmehealth/priorauth/api/PendingRequestsControllerTest.java`** (keep the existing test and
its assertions as they are, NFR3):
- Add a nested `@TestConfiguration` with a `@Primary` bean `Clock fixedClock()` =
  `Clock.fixed(2026-10-13T12:00:00Z, ZoneOffset.UTC)`, so no test depends on the real date (NFR3). (A `@Primary` bean
  with a different name, not an override, because Boot disables bean-definition overriding.)
- `agesAsOfWorkedCheck`: `GET /requests/pending?asOf=2026-10-13` → 200, 3 rows, ids PA-10231/PA-10244/PA-10263 in that
  order, `ageBusinessDays` 7/4/1, `overLimit` true/false/false, `ageLabel` `"7 bd OVER 5"`/`"4 bd"`/`"1 bd"`; and
  `$[0].tenantId`, `service`, `status`, `receivedAt` unchanged (FR13).
- `defaultsToTodayFromClock`: `GET /requests/pending` (no param) → same ages 7/4/1 via the fixed clock (FR9).
- `asOfEqualToNewestReceivedIsValid`: `?asOf=2026-10-09` → 200, `$[2].ageBusinessDays` 0, `$[2].ageLabel` `"0 bd"`.
- `invalidAsOfIs400`: `?asOf=2026-13-45` and `?asOf=yesterday` → 400.
- `asOfBeforeReceivedIs400`: `?asOf=2026-10-05` → 400, and `status().reason(containsString("2026-10-06"))` so the
  message names the date problem (FR11).

### 8. Change `README.md` (A-09, docs only)
One line: each row also carries `ageBusinessDays`, `overLimit`, `ageLabel` (business days after receipt, weekends and
tenant holidays excluded, over when > `priorauth.aging.threshold-days`); `?asOf=YYYY-MM-DD` computes them as of that
date (400 if invalid or before a row's `receivedAt`).

## Order

1. `git -C priorauth-api switch -c request-age/pending-age main`.
2. Resources and config: holiday JSON (step 1), `application.yml` (step 2).
3. `RequestAgingTest` (step 7, unit part) → `RequestAging` (step 3) until it compiles and passes.
4. `Clock` bean (step 4).
5. Controller tests (step 7, controller part) → `PendingRequestResponse` (step 5) and controller (step 6).
6. README line (step 8).
7. Run `./scripts/verify.sh` from the workspace folder (`scripts\verify.cmd` on Windows); all tests green, including the
   unchanged `RequestStoreTest` and the original `listsPendingRequestsOldestFirst`.
8. One commit in priorauth-api on the branch, e.g. `Pending list: business-day age, over-limit flag and label (asOf)`.
   No push (the workflow's last node does it), nothing committed in the workspace folder.

## Questions / assumptions carried into the build

- **Q1 (A-04 wording):** the requirement says a tenant with no holiday file "logs a warning at startup". At startup the
  aging component does not know which tenants exist (the store is the source, and in production that is a database), so
  the plan logs the warning **once, on the first row for that tenant**, and logs the loaded tenants at startup. Behavior
  (weekends only, row kept) is as required. Confirm, or we check `store.all()` tenants at startup instead.
- **Q2:** the 400 body. Spring Boot's default error JSON omits the message (`server.error.include-message` is `never`),
  so the message is in the HTTP status reason (asserted in the test), not in the body. If the screen should see the
  message in the body, we would set `server.error.include-message: always` — a global change, so not done without a yes.
- A-01 (report uses the same rule), A-02 (non-over label `"<age> bd"`), A-03 (whole-call 400; no 400 without `asOf`)
  are implemented as written and remain to be confirmed by the people named in requirements.md.

## Skipped / not checked / risks

- Not run yet: nothing was built or tested while planning.
- The nightly report and screen code were not available; matching the report rests on the answers (A-01).
- Holidays outside 2026 are absent: ages spanning 2025/2027 dates count weekends only and may be overstated (A-05).
- If the server's JVM zone is UTC, "today" changes at 18:00/19:00 Central (A-06); callers that care pass `asOf`.
- The holiday list now exists in two places (here and the report); they can drift until a shared calendar exists
  (out of scope).
- Version bump and tag: none (stays 1.0.2; Meena at release).
