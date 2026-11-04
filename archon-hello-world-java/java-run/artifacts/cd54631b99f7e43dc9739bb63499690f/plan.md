# Plan — request age on the pending list (API)

Request: `docs-in/request.md`. Requirements: `requirements.md` (revision 2, approved). Branch: `request-age/age-api`, PR base `main`.

## Approach in one paragraph

Two small new classes in the `api` package hold all the age logic (NFR4): `HolidayCalendar` loads every
`data/holidays-<tenantId>-<year>.json` once at startup and answers "is this date a holiday for this tenant";
`RequestAge` counts business days after `receivedAt` up to and including the as-of date and builds the flag and label
from `priorauth.aging.threshold-days`. `PendingRequestResponse` gets three new components at the end; the controller
takes an optional `asOf`, a `Clock` for "today", and turns bad `asOf` values into a 400 with a message.
Only `java.time`, Spring (`PathMatchingResourcePatternResolver`, `ProblemDetail`, `@Value`) and the Jackson 3
`JsonMapper` already used by `RequestStore`. **pom.xml is not changed; no dependency is added** (NFR1).

## Files

### Add

1. **`src/main/resources/data/holidays-TX-01-2026.json`** (FR6, A-01, A-09)
   JSON array of the 11 ISO dates in FR6, exactly as listed (incl. `2026-10-12`).

2. **`src/main/java/com/acmehealth/priorauth/api/HolidayCalendar.java`** — `@Component` (FR3, FR6, A-01, A-03, NFR5, NFR6)
   - Public constructor `HolidayCalendar(JsonMapper mapper)` delegates to a package-private
     `HolidayCalendar(JsonMapper mapper, String locationPattern)` with `"classpath*:data/holidays-*.json"`
     (the second one exists so the test can point at a bad file; mark the public one `@Autowired`).
   - At construction, resolves the pattern with `PathMatchingResourcePatternResolver`, and for each file:
     - parses the name `holidays-<tenantId>-<year>.json`; tenant ids contain `-` (`TX-01`), so the **last** `-`
       separates the year;
     - reads it as `List<LocalDate>` with the injected mapper (same way `RequestStore` reads the sample);
     - checks every date is in `<year>` (A-01).
     - Any failure (unparsable JSON, bad date, bad file name, date in the wrong year) throws
       `IllegalStateException` naming the file and the cause, so startup stops (NFR6).
   - Stores an immutable `Map<String, Set<LocalDate>>` keyed by `"<tenantId>-<year>"`.
   - `boolean isHoliday(String tenantId, LocalDate date)`: if no file for that tenant and `date.getYear()`,
     logs one warning per missing file naming `data/holidays-<tenantId>-<year>.json` (deduplicated with a
     `ConcurrentHashMap.newKeySet()`, so a missing 2027 file does not flood the log on every call) and returns
     `false` (A-03). No refusal (FR9).

3. **`src/main/java/com/acmehealth/priorauth/api/RequestAge.java`** — `@Component` (FR2–FR5, A-02, A-06)
   - Constructor `RequestAge(HolidayCalendar holidays, @Value("${priorauth.aging.threshold-days}") int thresholdDays)`.
     No default value: a missing key fails startup instead of silently using a number in code (NFR5).
   - Nested `record Age(int businessDays, boolean overLimit, String label)`.
   - `Age of(String tenantId, LocalDate receivedAt, LocalDate asOf)`:
     - counts dates `d` from `receivedAt + 1` through `asOf` inclusive where `d` is Mon–Fri and
       `!holidays.isHoliday(tenantId, d)` (FR2, FR3; A-06 falls out of this: a Saturday receipt is 1 on Monday);
     - returns 0 when `asOf` is on or before `receivedAt` (the controller decides whether that is an error, see below);
     - `overLimit = days > thresholdDays` (FR4);
     - `label = days + " bd"`, plus `" OVER " + thresholdDays` when over (FR5, A-02).
   - A plain day-by-day loop: ages are days to weeks, no need for anything cleverer.

### Change

4. **`src/main/resources/application.yml`** (FR4, NFR5) — add:
   ```yaml
   priorauth:
     aging:
       threshold-days: 5
   ```

5. **`src/main/java/com/acmehealth/priorauth/api/PendingRequestResponse.java`** (FR1, NFR2)
   - Append `int ageBusinessDays, boolean overLimit, String ageLabel` after `receivedAt`. Existing components,
     names and order unchanged; Jackson serialises the record components by name, so the JSON gets exactly the FR1
     names and types.
   - `from(PriorAuthRequest request)` becomes `from(PriorAuthRequest request, RequestAge.Age age)`.

6. **`src/main/java/com/acmehealth/priorauth/PriorAuthApiApplication.java`** (FR7, NFR3)
   - Add `@Bean Clock clock() { return Clock.systemDefaultZone(); }` — "today" in the server's default zone
     (FR7, A-08), replaceable in tests. One bean, no new config class.

7. **`src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java`** (FR7, FR8, FR9, A-04, A-05)
   - Constructor gains `RequestAge requestAge, Clock clock`.
   - `pending(@RequestParam(required = false) String asOf)`. Taken as a `String` (not `LocalDate`) so the
     controller owns the error message.
     - No `asOf`: `LocalDate.now(clock)`.
     - `asOf` given: `LocalDate.parse(asOf)` (ISO `yyyy-MM-dd`); on `DateTimeParseException` → 400
       `"asOf '13-10-2026' is not a valid yyyy-MM-dd date"`. An empty `asOf=` is also invalid → 400.
   - `asOf` given and any pending row has `receivedAt` after it → 400 naming the first such row in list order,
     e.g. `"asOf 2026-10-08 is before receivedAt 2026-10-09 of request PA-10263"` (FR8, A-04). `asOf` equal to a
     received date is fine (age 0).
   - No `asOf` and a row is received after today (A-05): no error, the row gets age 0 / `false` / `"0 bd"`
     (from `RequestAge`), and a warning naming the request is logged.
   - Rows still come from `store.pending()` in its order; nothing is filtered or re-sorted (FR9).
   - Errors: throw `ResponseStatusException(BAD_REQUEST, message)` and add a controller-local
     `@ExceptionHandler(ResponseStatusException.class)` returning `ResponseEntity<ProblemDetail>` with the message
     as `detail`. Reason: Boot's default `/error` page hides messages (`server.error.include-message: never`),
     and FR8 needs the message in the body. Local to this controller, so no global error behaviour changes.

### Not touched (NFR4)
`PriorAuthRequest`, `RequestStore`, `requests.sample.json`, `RequestStoreTest`, `pom.xml`, `scripts/`.

## Tests

All run through `./scripts/verify.sh` (NFR3). The existing test `listsPendingRequestsOldestFirst` stays as it is.

**A. `src/test/java/com/acmehealth/priorauth/api/RequestAgeTest.java`** — plain JUnit, no Spring context.
Builds `new RequestAge(new HolidayCalendar(JsonMapper.builder().build()), 5)` on the real TX-01 file.
- Worked check, as of Tue 2026-10-13: received 10-01 → `7, true, "7 bd OVER 5"`; 10-06 → `4, false, "4 bd"`;
  10-09 → `1, false, "1 bd"`.
- Received day: received 2026-10-13, as of 2026-10-13 → `0, false, "0 bd"`.
- Weekend: Fri 2026-10-16 → Mon 2026-10-19 = 1.
- Holiday: Fri 2026-10-09 → Tue 2026-10-13 = 1 (10-12 skipped). Without it, it would be 2.
- Saturday receipt (A-06): Sat 2026-10-17 → Mon 2026-10-19 = 1.
- Boundary: received Thu 2026-10-01; as of Thu 10-08 → `5, false, "5 bd"`; as of Fri 10-09 → `6, true, "6 bd OVER 5"`.
- As-of before received → 0 (the A-05 path).
- Missing tenant (A-03): tenant `OK-02`, Fri 2026-10-09 → Tue 2026-10-13 = 2 (10-12 counted, weekend still skipped).
- Missing year (A-03): TX-01, Thu 2026-12-31 → Mon 2027-01-04 = 2 (2027-01-01 counted, no 2027 file).
- Missing-file warning: with `OutputCaptureExtension` (spring-boot-test, already on the test classpath), the output
  contains `holidays-OK-02-2026.json`.

**B. `src/test/java/com/acmehealth/priorauth/api/HolidayCalendarTest.java`** — plain JUnit.
- The real file loads: `isHoliday("TX-01", 2026-10-12)` true, `2026-10-13` false, and all 11 FR6 dates are holidays.
- Unparsable file stops startup (NFR6): the package-private constructor with
  `"classpath*:holidays-bad/holidays-*.json"` throws `IllegalStateException` whose message names the file.
- Date in the wrong year (A-01): same, with `"classpath*:holidays-wrong-year/holidays-*.json"`.

Test resources (outside `data/`, so the app's own pattern never sees them):
- `src/test/resources/holidays-bad/holidays-XX-01-2026.json` → `["2026-13-45"]`
- `src/test/resources/holidays-wrong-year/holidays-XX-01-2026.json` → `["2027-01-01"]`

**C. `src/test/java/com/acmehealth/priorauth/api/PendingRequestsControllerTest.java`** — extend the existing
full-context MockMvc test.
- Pin today: `@TestBean Clock clock` with a static `clock()` returning `Clock.fixed` at noon on 2026-10-13 in
  `ZoneId.systemDefault()` (Spring Framework's `@TestBean`, already in `spring-test`; overrides the `clock` bean).
- `asOf=2026-10-13`: 3 rows, order PA-10231, PA-10244, PA-10263, with ages 7/4/1, flags true/false/false, labels
  `"7 bd OVER 5"`, `"4 bd"`, `"1 bd"`; `overLimit` is a JSON boolean and `ageBusinessDays` a number.
- No `asOf`: same values, from the fixed clock (FR7). Also asserts the existing fields
  (`id`, `tenantId`, `service`, `status`, `receivedAt`) are unchanged on the first row (NFR2).
- `asOf=13-10-2026` → 400, `$.detail` contains `asOf` and `13-10-2026`.
- `asOf=2026-10-08` → 400, `$.detail` contains `PA-10263`.
- `asOf=2026-10-09` → 200, PA-10263 is `0, false, "0 bd"` (equal date is not an error).
- A-05 (today before a received date, no `asOf`): a plain-Java test in the same class that builds
  `new PendingRequestsController(new RequestStore(JsonMapper.builder().build()), requestAge, Clock.fixed(2026-10-08))`
  and checks the call returns 3 rows with PA-10263 at `0, false, "0 bd"` rather than throwing. This avoids a second
  Spring context just for another clock.

## Order

1. Add `holidays-TX-01-2026.json` and the `priorauth.aging.threshold-days` key.
2. Add `HolidayCalendar` + `HolidayCalendarTest` and its two test resources. Run `./scripts/verify.sh`.
3. Add `RequestAge` + `RequestAgeTest`. Run verify.
4. Add the `Clock` bean; change `PendingRequestResponse` and `PendingRequestsController`; extend
   `PendingRequestsControllerTest`. Run verify.
5. When verify passes, commit on `request-age/age-api` with a message naming `docs-in/request.md` and the
   requirement IDs (FR1–FR9, NFR1–NFR6). Pushing is the workflow's last node; the PR is opened by the team.

## Version and tags

`git tag` returns nothing (no tags yet); pom.xml is at **1.0.2**. A release version or tag is out of scope, so this
change leaves the version alone. When the team releases it, this is an additive API change, so **1.1.0** would be the
natural next version; that is a suggestion only.

## Decisions for the approver to check

- `asOf` before a received date is checked against all pending rows and the first one in list order is named (A-04).
- A holiday file with a date outside its year stops startup, same as an unparsable file. A-01 says the dates belong
  to the year; failing loudly matches NFR6.
- The missing-file warning is logged once per tenant-year per process, not on every request.
- The 400 body is a `ProblemDetail` (`application/problem+json`, message in `detail`). The screen team never calls
  with `asOf`, so this only matters to callers who pin the date.
- `README.md` is not updated. One line about `?asOf=` could be added if wanted; the plan leaves it out as not asked for.

## Skipped / not checked / risk

- Not checked: Jackson 3 deserialising `List<LocalDate>` with the Boot-provided `JsonMapper`. `RequestStore` already
  reads `LocalDate` this way, so it is expected to work. The tests cover it.
- Not checked: that `@TestBean` overrides the `clock` bean by name in Boot 4.1 / Framework 7 as expected. If it does
  not, fall back to a `@TestConfiguration` with a `@Primary` fixed `Clock`.
- Risk (A-03, A-07): only `holidays-TX-01-2026.json` exists. From 2027-01-01, TX-01 ages count 2027 holidays as
  business days until a 2027 file is added. The list is a copy and can drift from the report's.
- Risk (A-08): the age turns over at the server's midnight. On a UTC server that is about 19:00 Central.
- Open with the screen team: the A-02 label for the not-over case and the A-05 behaviour. The plan implements the
  assumptions as written.
- Not touched, but worth knowing: `RequestStoreTest` constructs the store directly; the new controller test does the
  same for A-05.
