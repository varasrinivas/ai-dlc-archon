# Implementation: request age on the pending list (API)

Request: `docs-in/request.md`. Plan: `plan.md` (approved by Meena Iyer: README kept as is, Q1 and Q2 as proposed).
Requirements: FR1–FR13, NFR1–NFR7 (`requirements.md` rev 2).

## Branch and commit

- Repo: `priorauth-api`, branch **`request-age/pending-age`**, created from `main` (d9aa178).
- Commit: **`a3972b42ef31bf68500d39389b0d5f8caf9724d1`** — "Pending list: business-day age, over-limit flag and label (asOf)";
  the message names `docs-in/request.md` and FR1–FR13, NFR1–NFR7.
- Not pushed (the workflow's last node pushes). Nothing committed in the workspace folder (its `git status` is clean).

## Files changed (in priorauth-api)

| File | Change | Requirements |
|---|---|---|
| `src/main/resources/data/holidays-TX-01-2026.json` | new: the 11 TX-01 2026 dates as a JSON array | FR7, FR8, A-08 |
| `src/main/resources/application.yml` | adds `priorauth.aging.threshold-days: 5` | FR6 |
| `src/main/java/com/acmehealth/priorauth/aging/RequestAging.java` | new `@Component`: loads `classpath*:data/holidays-*.json` (tenant and year from the file name), `ageBusinessDays`, `overLimit`, `label`; fails fast on a badly named file, non-array content, a null date or a date outside the file's year, and on a negative threshold; logs loaded tenants at INFO; WARN once per tenant without a calendar (Q1 as proposed) | FR1–FR8, NFR6, A-04, A-05 |
| `src/main/java/com/acmehealth/priorauth/PriorAuthApiApplication.java` | adds `Clock clock()` bean = `Clock.systemDefaultZone()` | FR9, A-06 |
| `src/main/java/com/acmehealth/priorauth/api/PendingRequestResponse.java` | appends `ageBusinessDays`, `overLimit`, `ageLabel`; `from(request, aging, asOf)` | FR1, FR4, FR5, FR13 |
| `src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java` | optional ISO `asOf`; 400 (`ResponseStatusException`, message in the status reason; Q2 as proposed) if `asOf` is before any returned row's `receivedAt`; otherwise today from the `Clock`; row set and order from `store.pending()` unchanged | FR9–FR12, A-03 |

Unchanged as planned: `pom.xml` (version 1.0.2, no new dependency), `PriorAuthRequest`, `RequestStore`,
`RequestStoreTest`, `requests.sample.json`, `README.md` (per the approval note, skipping plan step 8).

## Tests added

- `src/test/java/com/acmehealth/priorauth/aging/RequestAgingTest.java` (11 tests, no Spring): same day 0; weekend
  skipped; 2026-10-12 holiday skipped (and 2 for a tenant with no calendar); weekend receipt; `asOf` on Sat/Sun adds
  nothing; `asOf` before received → 0; worked check 7/4/1; threshold boundary 5 → `false`/`"5 bd"`, 6 → `true`/`"6 bd OVER 5"`,
  `"0 bd"`, threshold 3 → `"7 bd OVER 3"`; negative threshold fails; real TX-01 resource loaded (10-12 and 11-26/27
  honored); malformed file (object instead of array, bad file name, date from another year) → `IllegalStateException`.
- `PendingRequestsControllerTest`: original `listsPendingRequestsOldestFirst` kept unchanged; a `@Primary` fixed
  `Clock` (2026-10-13T12:00Z, UTC) via nested `@TestConfiguration`; new `agesAsOfWorkedCheck` (ids, ages 7/4/1, flags,
  labels, existing fields), `defaultsToTodayFromClock`, `asOfEqualToNewestReceivedIsValid` (0 / `"0 bd"`),
  `invalidAsOfIs400` (`2026-13-45`, `yesterday`), `asOfBeforeReceivedIs400` (`2026-10-05`, reason contains `2026-10-06`).

## Verify result

`./scripts/verify.sh` from the workspace root (`mvn -q test` in priorauth-api): **PASS**, exit 0.
Surefire: RequestAgingTest 11/11, PendingRequestsControllerTest 6/6, RequestStoreTest 2/2 — 19 tests, 0 failures,
0 errors, 0 skipped.

## Skipped / not checked / risks

- README not changed (approval note: updated at release).
- Not checked: a packaged-jar run (`classpath*:` scanning inside the jar was exercised only from `target/classes` in
  tests); a real startup with a malformed holiday file or missing threshold (covered at unit level, not by booting the app).
- The 400 body is Spring Boot's default error JSON without the message (Q2); the message is only in the HTTP status reason.
- The unknown-tenant warning is logged on the first row for that tenant, not at startup (Q1).
- Still open from requirements: A-01 (report uses the same rule), A-02 (non-over label format), A-03 (whole-call 400).
- Holidays exist only for TX-01 2026; ages over other years count weekends only (A-05). JVM-zone "today" (A-06).
- Git warned that the new files are LF and will be CRLF in the working copy (autocrlf); content unaffected.
- No version bump or tag (stays 1.0.2).
