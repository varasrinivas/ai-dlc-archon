# Review: request age on the pending list (API)

Branch `request-age/age-api`, one commit `f3a465d` on top of `main` (`git diff main...HEAD`, 12 files, +449/−7).
Checked against `requirements.md` (revision 2) and `plan.md`. Nothing in the repo was edited.

**Verdict: NOT READY.** One finding needs fixing first (R-1). It needs a decision from the approver, because the
requirements set no upper limit on `asOf`. Everything else matches the plan, and every FR has code and a test.

## Verify

I ran `./scripts/verify.sh` myself: **exit 0**. 21 tests, 0 failures, 0 errors, 0 skipped (HolidayCalendarTest 3,
RequestAgeTest 9, PendingRequestsControllerTest 7, RequestStoreTest 2). This matches `implementation.md`.
`git status` was clean afterwards (`target/` is ignored).

## FR / NFR coverage

| Req | Code | Test | OK |
|-----|------|------|----|
| FR1 three new fields, existing ones unchanged | `PendingRequestResponse` adds 3 components at the end and keeps the existing ones in order | `agesAsOfAGivenDate`, `agesAsOfTodayWithoutAsOf` (existing fields on row 0), `listsPendingRequestsOldestFirst` kept | yes |
| FR2 counts days after receipt, through as-of; received day is 0 | `RequestAge.of` loops from `receivedAt+1` to `asOf` inclusive | `receivedDayIsZero`, `workedCheckAsOf20261013`, `asOfOnAReceivedDateIsAgeZero` | yes |
| FR3 Mon–Fri, not a tenant holiday | `RequestAge.of` + `HolidayCalendar.isHoliday(tenantId, d)` | `weekendIsNotCounted`, `holidayIsNotCounted`, `saturdayReceiptIsOneOnMonday` (A-06) | yes |
| FR4 strictly greater than `priorauth.aging.threshold-days` = 5 | `days > thresholdDays`; `@Value` with no default; `application.yml` | `thresholdIsStrictlyGreater` (5 → false, 6 → true). The yml value is exercised by the full-context controller tests (7 → true) | yes |
| FR5 label `"<n> bd"` / `"<n> bd OVER <t>"` | `RequestAge.of` | label asserted in RequestAgeTest and the controller tests | yes |
| FR6 `data/holidays-<tenant>-<year>.json`, the 11 TX-01 dates | `holidays-TX-01-2026.json` (I compared it date by date with FR6: they match); `HolidayCalendar` keys on tenant+year and splits at the last `-` | `loadsTheTx01File` checks all 11 dates | yes |
| FR7 default today in the server's zone; optional `asOf` | `Clock.systemDefaultZone()` bean; `LocalDate.now(clock)`; `@RequestParam(required=false) String asOf` | `agesAsOfTodayWithoutAsOf` (`@TestBean` clock), `agesAsOfAGivenDate` | yes |
| FR8 400 with a message: invalid date; before a row's receivedAt, naming the row | `parse()` → `ResponseStatusException`; loop over pending rows; local `@ExceptionHandler` → `ProblemDetail.detail` | `invalidAsOfIs400`, `asOfBeforeAReceivedDateIs400` (`PA-10263` in `detail`) | yes, but see R-1 |
| FR9 never acts on age; filter/order unchanged | rows still come from `store.pending()` in order, with only a `map` over them | 3 rows in order PA-10231/10244/10263 asserted | yes |
| NFR1 no new dependency | pom.xml not in the diff | n/a | yes |
| NFR2 backward compatible | only adds fields; the exception handler is local to this controller | existing test kept | yes |
| NFR3 deterministic, tested | `Clock` bean plus `asOf` | every bullet in NFR3 has a test (A-03 tenant and year: `tenantWithoutFileCountsWeekendsOnlyAndWarns`, `yearWithoutFileCountsWeekendsOnly`) | yes |
| NFR4 untouched files | `PriorAuthRequest`, `RequestStore`, `requests.sample.json`, `RequestStoreTest` not in the diff | n/a | yes |
| NFR5 config, not code | threshold in yml, holidays in files | n/a | yes |
| NFR6 load once; a bad file stops startup | constructor loads into `Map.copyOf`; any failure → `IllegalStateException` naming the file | `unparsableFileStopsStartup`, `dateOutsideTheFilesYearStopsStartup` | yes |

The assumptions are implemented as written: A-01 (a wrong-year date fails startup), A-02, A-03 (warns once per
tenant-year), A-04 (first row in list order), A-05 (age 0 plus a warning, `todayBeforeAReceivedDateIsAgeZeroNotAnError`),
and A-06.

## Anything the plan did not name

No extra files or behaviour beyond the plan. Every file in the diff is in the plan's Add/Change/Tests lists. The
only extra edit is the controller's Javadoc line. The commit message names `docs-in/request.md` and FR1–FR9 and
NFR1–NFR6, as step 5 of the plan says.

## Findings

### R-1 (must fix, needs a decision): `asOf` has no upper limit, so one request can tie up a thread and fill memory

`LocalDate.parse` accepts dates far in the future. I checked: `+999999999-12-31` and `9999-12-31` both parse.
`RequestAge.of` counts day by day (`PendingRequestsController.java` → `RequestAge.java` loop) and calls
`HolidayCalendar.isHoliday` for every weekday. Because no row is received after such a date, the FR8 check passes,
and then:
- `?asOf=+999999999-12-31` makes about 3.65×10¹¹ loop iterations per pending row. The request thread is effectively
  stuck, and a few such calls exhaust the pool.
- Every year without a file adds one key to `warnedMissing` and logs one warning. The set never shrinks, so the
  same call also grows memory without limit (a billion years per tenant) and floods the log.
- Even `?asOf=9999-12-31` costs about 2.9 M iterations per row and about 8,000 warning lines per tenant on the first
  call.

This is validation at a trust boundary (CLAUDE.md rule 5). The requirements do not name the case, so I am asking
rather than assuming. Options:
(a) reject an `asOf` after today (the screen never sends one, and FR7 talks about pinning "today");
(b) reject an `asOf` more than N days after today;
(c) reject any year without a holiday file.
Whichever is chosen should be a new 400 case in FR8 and get a test. Option (a) is the smallest change.

### R-2 (minor, test gap): an empty `asOf=` returning 400 is in the plan but not tested

Plan item 7 says "An empty `asOf=` is also invalid → 400". The code does handle it: Spring passes `""`, and
`LocalDate.parse("")` throws `DateTimeParseException`, which I checked. No test pins it down. One `param("asOf", "")`
case in `PendingRequestsControllerTest` would close the gap.

### R-3 (note, not checked): `classpath*:data/holidays-*.json` from inside the packaged jar

The tests resolve the pattern against `target/classes`, a directory. In the Boot fat jar, the wildcard depends on
the jar containing a `data/` directory entry (Maven normally writes one). This was never run from `java -jar`. If the
pattern resolved to nothing, the app would start quietly with no holidays and only log warnings, which is exactly the
"ageing requests wrongly" that NFR6 is meant to prevent. Suggest one manual `java -jar` + `?asOf=2026-10-13` check
before release (PA-10263 must be `1 bd`, not `2 bd`).

### R-4 (note): duplicate holiday files overwrite each other quietly

`loaded.put(key, …)` in `HolidayCalendar` keeps the last file it finds if two classpath entries have the same name.
This can't happen with one module today, so I'm only mentioning it, not asking for a fix.

## Skipped / not checked / risk

- Did not run `scripts\verify.cmd`, the app under `spring-boot:run` or `java -jar`, or any real HTTP call. Only
  `verify.sh` (MockMvc).
- Did not check the 400 `Content-Type` (`application/problem+json`). Only status and `detail` are asserted.
- Did not review `docs-in/request.md`, `scan.md` or `questions.md` beyond what `requirements.md` quotes.
- Risks carried from the plan still stand: no TX-01 2027 file (needed before 2027-01-01, A-03), the holiday list can
  drift from the report's (A-07), the age turns over at server midnight (A-08), and the screen team still has to
  confirm A-02 and A-05.
- Version stays at 1.0.2 with no tag (out of scope). `git tag` was not re-run for this review.
