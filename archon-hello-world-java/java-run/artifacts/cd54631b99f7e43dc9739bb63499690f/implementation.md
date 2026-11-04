# Implementation — request age on the pending list (API)

Request: `docs-in/request.md`. Plan approved by Meena Iyer ("Keep the README as is; we update it at release").
Branch `request-age/age-api`, commit **f3a465d**. Requirements: FR1–FR9, NFR1–NFR6.

## Verify result

`./scripts/verify.sh` (`mvn -q test`): **exit 0, passed.** 21 tests, 0 failures, 0 errors, 0 skipped:
HolidayCalendarTest 3, RequestAgeTest 9, PendingRequestsControllerTest 7, RequestStoreTest 2 (unchanged).

## Files changed

Added
- `src/main/resources/data/holidays-TX-01-2026.json` — the 11 FR6 dates (FR6, A-01, A-09).
- `src/main/java/com/acmehealth/priorauth/api/HolidayCalendar.java` — loads `classpath*:data/holidays-*.json` once at
  startup; tenant id = name up to the last `-`; any bad file name, unparsable JSON or date outside the file's year
  throws `IllegalStateException` naming the file (NFR6, A-01). Missing tenant/year: `false` and one warning per
  tenant-year naming `data/holidays-<tenant>-<year>.json` (A-03).
- `src/main/java/com/acmehealth/priorauth/api/RequestAge.java` — day-by-day count after `receivedAt` through `asOf`,
  Mon–Fri minus tenant holidays; `overLimit = days > threshold`; label `"<n> bd"` / `"<n> bd OVER <threshold>"`
  (FR2–FR5, A-02, A-06). Threshold from `${priorauth.aging.threshold-days}`, no in-code default (NFR5).

Changed
- `src/main/resources/application.yml` — `priorauth.aging.threshold-days: 5` (FR4).
- `PendingRequestResponse.java` — three components appended: `ageBusinessDays`, `overLimit`, `ageLabel` (FR1, NFR2).
- `PriorAuthApiApplication.java` — `Clock` bean, `Clock.systemDefaultZone()` (FR7, NFR3).
- `PendingRequestsController.java` — optional `asOf` (String, parsed with `LocalDate.parse`); invalid → 400
  `"asOf '<value>' is not a valid yyyy-MM-dd date"`; before a pending row's `receivedAt` → 400 naming the first such
  row (FR8, A-04); no `asOf` and a future row → age 0 plus a warning (A-05). Controller-local
  `@ExceptionHandler` returns a `ProblemDetail` with the message in `detail`. Order/filter untouched (FR9).

Not touched: `PriorAuthRequest`, `RequestStore`, `requests.sample.json`, `RequestStoreTest`, `pom.xml`, `scripts/`,
`README.md` (as instructed).

## Tests added

- `HolidayCalendarTest` — real TX-01 file (10-12 holiday, 10-13 not, all 11 dates); unparsable file and
  wrong-year file each throw `IllegalStateException` naming the file (test resources `holidays-bad/`,
  `holidays-wrong-year/` under `src/test/resources`, outside `data/`).
- `RequestAgeTest` — worked check (7/true/"7 bd OVER 5", 4/false/"4 bd", 1/false/"1 bd"), received day 0,
  weekend, holiday, Saturday receipt (A-06), boundary 5 → "5 bd" / 6 → "6 bd OVER 5", as-of before received → 0,
  missing tenant (OK-02 = 2, and the warning names `holidays-OK-02-2026.json` via `OutputCaptureExtension`),
  missing year (2026-12-31 → 2027-01-04 = 2).
- `PendingRequestsControllerTest` (existing test kept) — `@TestBean Clock` fixed at 2026-10-13 noon; `asOf=2026-10-13`
  full worked check; no `asOf` gives the same values and the existing fields unchanged; `asOf=13-10-2026` → 400
  with `asOf` and the value in `detail`; `asOf=2026-10-08` → 400 naming PA-10263; `asOf=2026-10-09` → 200 with
  PA-10263 at 0/false/"0 bd"; A-05 via a directly built controller with today = 2026-10-08 → 3 rows, no error.

## Skipped / not checked / risk

- No deviation from the plan. `@TestBean` worked as expected in Boot 4.1, so no fallback was needed.
- Not checked by a test: the JSON type of `overLimit`/`ageBusinessDays` beyond `jsonPath(...).value(true/7)` (which
  matches on the deserialised value; a string `"true"` would not equal boolean `true`, so this is covered in practice).
- Not checked: the 400 body's `Content-Type` (`application/problem+json`); only status and `detail` are asserted.
- Not checked: running the app with `mvn spring-boot:run` and calling it by hand; only the MockMvc full-context test.
- Not checked: `scripts\verify.cmd` (only `verify.sh` was run, under Git Bash).
- The missing-file warning is written by the plain-JUnit `RequestAgeTest` to stdout through Logback's default config;
  if logging config changes to stop console output in tests, that one assertion would fail.
- Risks carried from the plan: no 2027 TX-01 file (needed before 2027-01-01, A-03); holiday list can drift from the
  report's (A-07); age turns over at server midnight (A-08); A-02 label and A-05 behaviour still to be confirmed by
  the screen team.
- Git warned that the new files will be checked out with CRLF in this working copy (repo's autocrlf); content is
  committed normalised, nothing to act on.
- Version left at 1.0.2, no tag (out of scope); 1.1.0 suggested for release.
