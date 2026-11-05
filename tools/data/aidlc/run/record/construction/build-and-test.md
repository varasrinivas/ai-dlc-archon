# Build and Test (AI-DLC stage 3.6, Construction)

Request: `docs-in/request.md` (intent 261013-request-age-api). Checked against `record/inception/requirements-analysis.md` v2
(R1–R17, A1–A8) and `record/construction/code-generation.md` (commits `6103fdd`, `d4a98c9`).
Repo `priorauth-api/`, branch `request-age/pending-list-age` @ `d4a98c9`, clean, not pushed. **No code changed in this stage.**
Run on 2026-11-05, Windows, JDK 21.0.10, Maven 3.9.16, server zone UTC+05:30.

## Questions only a person can decide

1. **The list can refuse the reviewer screen even when no `asOf` is sent.** Without `asOf`, the date is the server's
   today, and the same "before the newest `receivedAt`" check still runs (`PendingRequestsController.java:44` and `:50`).
   If any pending row has a `receivedAt` after the server's today, **every** call from the screen gets 400 and an empty
   screen. That happens with one future-dated row in the queue DB, or near midnight when the intake system's zone is
   ahead of the server's zone (a request stamped "tomorrow"). This breaks R12 ("never refuses; only caller errors in R8/R9
   give a non-200"). I found this by reading the code. The sample data cannot trigger it, so no test or HTTP call shows it.
   - a) Send it back to 3.5 for a small fix: without `asOf`, never answer 400. A row received "after today" shows age 0
     (and is logged). The checks on an explicit `asOf` stay as they are. Add one test. *(recommended: an empty reviewer
     screen is worse than one row aged 0)*
   - b) Accept it as it is and record it as a known risk.
2. **Rejecting an `asOf` after today is not in the approved requirements.** Revision 2 added it to stop a caller from
   running the day-by-day count for billions of days (Kiran's `+999999999-12-31`). The security engineer would keep it:
   it is what bounds the loop. But R8 and R9 do not name it.
   - a) Add it to the requirements as R18 ("an `asOf` after today in the server's zone → 400") and approve. *(recommended)*
   - b) Keep the code and leave the requirements unchanged.
   - c) Remove it. This brings back the denial-of-service hole, so I advise against it.
3. **The year rollover is 57 days away.** Only `holidays-<tenant>-2026.json` is read (`BusinessDayCalendar.java:53`).
   From 1 Jan 2027, no 2027 holidays count (1 Jan 2027 itself first), so the API's ages drift above the report's without
   any error.
   - a) Do not release until a 2027 TX-01 file exists and the loader reads the file for each date's year (needs the 2027
     dates from Ravi or Meena, and a code change in 3.5).
   - b) Release now, and open a follow-up with a named owner due by 2026-12-15. *(recommended: the change is useful in
     November and December, and the follow-up is small)*
   - c) Accept the drift.
4. **The two kinds of 400 have different bodies.** A bad range gives `application/problem+json` with the reason in
   `detail`. A malformed date (`13/10/2026`, `2026-02-30`) gives Spring's default `application/json`
   `{timestamp,status,error,path}` with no reason. Neither leaks a stack trace.
   - a) Accept it: both are JSON 400s, and the screen only sends dates it builds itself. *(recommended)*
   - b) Make the malformed case problem+json too (a small change in 3.5).

## Build and test results

| Step | Command | Result |
|---|---|---|
| Verify (bash) | `./scripts/verify.sh` (Git Bash, from workspace) | **green**, exit 0, ~10 s |
| Verify (Windows) | `scripts\verify.cmd` | **green**, exit 0 (first run on `d4a98c9`) |
| Package | `mvn -q -DskipTests package` (tests had just passed through verify) | exit 0, `target/priorauth-api-1.0.2.jar` (19.9 MB) |
| HTTP smoke | `java -jar ... --server.port=18080` + `curl` (not a test; a run of the real jar) | see below |

Surefire: **19 tests, 0 failures, 0 errors, 0 skipped**. `BusinessDayCalendarTest` 6, `PendingRequestResponseTest` 3,
`PendingRequestsControllerTest` 8, `RequestStoreTest` 2. Baseline was 3.
Log noise: the Mockito self-attach / dynamic-agent warning (already known, unrelated) and the expected WARN for tenant
`ZZ-99` with no holiday file.

**HTTP smoke on the real jar** (Kiran's check, which 3.5 had run only through MockMvc). Every call answered in 34–50 ms:

| Call | Result |
|---|---|
| `/requests/pending` (today = 2026-11-05) | 200; ages 24 / 21 / 18, all `overLimit: true` (checked by hand: Oct 2 → Nov 5, minus weekends and 12 Oct = 24) |
| `?asOf=2026-10-13` | 200; 7/true/`7 bd OVER 5`, 4/false/`4 bd`, 1/false/`1 bd`: matches the R13 table, so the holiday file is in the jar |
| `?asOf=2026-10-08` | 400 problem+json, "earliest allowed asOf is 2026-10-09" |
| `?asOf=2026-11-06` | 400 problem+json, "latest allowed asOf is 2026-11-05" |
| `?asOf=+999999999-12-31` | **400 at once** (the bug from revision 2 is fixed on the real jar) |
| `?asOf=13/10/2026`, `?asOf=2026-02-30` | 400, Spring default body (Q4) |
| `?asOf=` | 200, same as no `asOf` |

`memberId` was absent from every row. pom.xml and the model/store files are not in `git diff main..HEAD`.

## Requirement → test map

Test classes are in `src/test/java/com/acmehealth/priorauth/`. Short names used below: `C` = `api/PendingRequestsControllerTest`,
`B` = `api/BusinessDayCalendarTest`, `P` = `api/PendingRequestResponseTest`, `S` = `store/RequestStoreTest`.

| Req | What | Proven by | Status |
|---|---|---|---|
| R1 | `ageBusinessDays`, day 0 = received day | B `receivedOnTheAsOfDateIsDayZero`; C `agesMatchTheReportUsingTheClock`, `asOfPinsTheDate` (row 3 = 0) | covered |
| R2 | Mon–Fri minus tenant holidays | B `weekendsDoNotCount`, `holidaysDoNotCount` | covered |
| R3 | `overLimit` = age > threshold | P `ageAtTheThresholdIsNotOver`, `ageAboveTheThresholdIsOver`; C parity (7 → true, 4 → false) | covered |
| R4 | `ageLabel` text | P (all 3); C parity, `asOfPinsTheDate` (`0 bd`) | covered |
| R5 | existing fields, order, filter unchanged; no `memberId`; model/store untouched | C `listsPendingRequestsOldestFirst` (original test + `memberId` absent); S both tests; `git diff` shows no model/store change | covered. Field *types/format* only checked for `receivedAt` |
| R6 | default = today in the server's zone | C parity and `emptyAsOfMeansToday` (fixed clock); HTTP smoke (real clock) | covered with a test clock. The production `Clock.systemDefaultZone()` bean is not unit-tested (one line) |
| R7 | `asOf` pins the date | C `asOfPinsTheDate` | covered |
| R8 | `asOf` before any `receivedAt` → 400 | C `asOfBeforeAReceivedDateIsACallerError` | covered. **See Q1: the same check also hits the default path** |
| R9 | malformed `asOf` → 400 | C `malformedAsOfIsACallerError`; HTTP `2026-02-30` | covered |
| R10 | threshold from config = 5 | C parity (`OVER 5` comes from `application.yml`); P `labelUsesTheConfiguredThreshold` | covered, indirectly |
| R11 | TX-01 file, exactly 11 dates | B uses the real file (12 Oct, 26–27 Nov) | partly: **no test asserts the 11 dates**; I checked them by reading the file against the answers (they match) |
| R12 | flag only, never refuse/hide/reorder | C `$.length() == 3` and order on the 200 paths | partly: **no test for the default path refusing (Q1)** |
| R13 | report parity on the sample | C `agesMatchTheReportUsingTheClock`; HTTP `asOf=2026-10-13` | covered (sample only) |
| R14 | rule cases | same day, weekend, holiday, Saturday, holiday-received (B); boundary 5/6 (P); no-file tenant (B); `asOf` too early, malformed (C) | covered. The boundary is tested in the unit test only, not through the endpoint |
| R15 | deterministic clock | C `@Primary` fixed clock; B/P don't use a clock | covered |
| R16 | no new dependency, version 1.0.2 | `git diff main..HEAD -- pom.xml` is empty; jar is `1.0.2` | covered (by inspection) |
| R17 | verify green | both scripts green above | covered |
| (rev 2) | `asOf` after today → 400; far future answers at once | C `asOfAfterTodayIsACallerError`, `farFutureAsOfIsRejectedNotCounted`; HTTP smoke | covered. Not a requirement yet (Q2) |
| A2 | missing file → weekends only + one WARN | B `tenantWithoutAHolidayFileSkipsWeekendsOnly` | count covered; WARN seen in the log but not asserted |
| A3 | 400 body names the earliest date | C `asOfBeforeAReceivedDateIsACallerError` (`detail` has `2026-10-09`) | covered |
| choice 3 | malformed holiday file → 500 | none | **not tested** |

## Security engineer's view

- **Denial of service from the caller:** closed. The accepted `asOf` lies between the newest `receivedAt` and today, so the
  loop length is set by the oldest pending row, not by the caller. The real jar answers the far-future date at once.
  What is left: the work per call is (pending rows × age in days). A queue with rows years old would make each call
  slower, but a caller cannot make it worse. Acceptable.
- **Path from data:** the holiday file path is built from `tenantId` (`BusinessDayCalendar.java:53`). It comes from the
  store (the queue DB), not from the HTTP caller, and is read from the classpath only. Low risk. Worth a note if
  `tenantId` ever becomes a request parameter.
- **Unbounded cache:** `holidaysByTenant` has one entry per tenant seen in the data. It is bounded by the tenant count. Fine.
- **Information disclosure:** error bodies give dates only, with no stack trace (Spring's default
  `include-stacktrace=never`). The newest `receivedAt` named in a 400 is already in the 200 response.
- **Availability / integrity:** Q1 (one bad row empties the screen) and Q3 (ages wrong without any error from January)
  are the two real findings.
- **Already there before this change, out of scope:** no authentication or tenant scoping on `GET /requests/pending`.
  Every caller sees every tenant's rows.

## Skipped / not checked / risks

- Did not reproduce Q1 by running anything. It comes from reading the code, because the sample data has no future-dated
  row and I changed no data.
- Did not test a malformed holiday file (500), an empty pending list (expected 200 `[]`), or spans that cross into 2027.
- No load or performance test, and no test against the production queue-DB store (not in this repo).
- Did not see the nightly report's code or the reviewer screen's code: parity is proven for the 3 sample rows only.
- Server time-zone risk (default "today" can be off by one day from the report near midnight) stands as decided.
- `target/` was rebuilt by the package step (ignored build output). The smoke-test app was stopped afterwards.
- Mockito dynamic-agent warning and the git LF→CRLF warnings: unrelated, not fixed.
