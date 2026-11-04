# Requirements: request age on the pending list (API)

Request: `docs-in/request.md` (Ravi Menon, Tue 13 Oct). Answers to `questions.md` from Ravi and Meena:
1 X, 2 A, 3 A, 4 A, 5 X, 6 A (superseded by the screen team's names, below), 7 C.
Revision 2 (Meena): screen field names `ageBusinessDays`, `overLimit`, `ageLabel`; config key
`priorauth.aging.threshold-days`; holiday files `data/holidays-<tenant>-2026.json`; an `asOf` before the received
date is a caller error. Repo: `priorauth-api` (Spring Boot 4.1.1, Java 21, version 1.0.2, no tags).

Business rule in one line: **age = the number of business days after the received day, up to and including the
"as of" date; business days exclude Saturdays, Sundays and the tenant's holidays; the row is over the limit when
age > threshold (5, from configuration).**

## Functional requirements

**FR1 – Age on every pending row.** Each row returned by `GET /requests/pending` carries `ageBusinessDays`
(integer, ≥ 0): the count of business days `d` with `receivedAt < d ≤ asOf`. The received day is day 0 (answer 2A),
so a request received on the `asOf` date has age 0, and one received Friday and seen Monday has age 1.

**FR2 – Business day.** A date is a business day unless it is a Saturday, a Sunday, or a holiday in the calendar of
the row's `tenantId`.

**FR3 – Weekend or holiday receipt.** No special case: a request received on a weekend or holiday starts counting on
the next business day, which follows from FR1 (answer 3A). If `asOf` itself is a weekend or holiday, it adds nothing.

**FR4 – Over-limit flag.** Each row carries `overLimit` (boolean), `true` exactly when `ageBusinessDays > threshold`
(answer 4A: "over" means strictly more). With threshold 5: age 5 is `false`, age 6 is `true`.

**FR5 – Age label.** Each row carries `ageLabel` (string) for the screen to show as is:
- over the limit: `"<age> bd OVER <threshold>"`, e.g. `"7 bd OVER 5"` (the screen team's example);
- otherwise: `"<age> bd"`, e.g. `"4 bd"` (see A-02).
The threshold in the label is the configured value, not a literal 5.

**FR6 – Threshold from configuration.** The threshold is `priorauth.aging.threshold-days` in `application.yml`,
set to `5`. It is read at startup.

**FR7 – Holiday calendars, one JSON file per tenant.** Holidays live in the API's resources at
`data/holidays-<tenant>-2026.json` (i.e. `src/main/resources/data/holidays-TX-01-2026.json`), loaded at startup.
A shared calendar service is out of scope (separate work).

**FR8 – TX-01 calendar for 2026.** `holidays-TX-01-2026.json` contains exactly these 11 dates:
2026-01-01, 2026-01-19, 2026-02-16, 2026-05-25, 2026-07-03, 2026-09-07, **2026-10-12**, 2026-11-11, 2026-11-26,
2026-11-27, 2026-12-25.

**FR9 – "Today".** Without a parameter, `asOf` is today's date in the server's default time zone (answer 5X), taken
from an injectable `java.time.Clock` so tests can fix it.

**FR10 – `asOf` parameter.** `GET /requests/pending?asOf=YYYY-MM-DD` computes every row's age, flag and label as of
that date instead of today. A value that is not a valid ISO date gets **400 Bad Request**.

**FR11 – `asOf` before a received date is a caller error.** If `asOf` is earlier than the `receivedAt` of any row
that would be returned, the call gets **400 Bad Request** with a message naming the date problem (see A-03); no
partial list is returned. `asOf` equal to `receivedAt` is valid and gives age 0.

**FR12 – Flag only.** The API only reports the flag and label. It never filters, hides, reorders, refuses or alerts
on over-limit rows (Ravi, Meena). Row set and order stay as today: PENDED and IN_REVIEW only, oldest first. The 400s
in FR10/FR11 are input validation, not refusal by age.

**FR13 – Nothing else changes.** Existing fields (`id, tenantId, service, status, receivedAt`) keep their names,
types and values; the three new fields are added. The pom version stays **1.0.2** (answer 7C; Meena sets it at
release).

## Non-functional requirements

**NFR1 – No new dependency.** Use the JDK (`java.time`), Spring and the Jackson already on the classpath; `pom.xml`
dependencies are unchanged.

**NFR2 – Backward-compatible JSON.** The change is additive only (see FR13).

**NFR3 – Deterministic tests.** No test depends on the real date: tests use `asOf` or a fixed `Clock`. The existing
`PendingRequestsControllerTest` assertions stay valid.

**NFR4 – Tests for the new logic** (CLAUDE.md rule 4): unit tests for the business-day count covering a weekend,
the 2026-10-12 holiday, same-day receipt (0), weekend receipt, and the threshold boundary (5 → `false`/`"5 bd"`,
6 → `true`/`"6 bd OVER 5"`); controller tests for the sample data as of 2026-10-13 (the worked check below), an
invalid `asOf` (400) and an `asOf` before a received date, e.g. 2026-10-05 (400).

**NFR5 – Scope.** The change stays in the api layer (response, controller), a new calculator/calendar class, config
and resources. `PriorAuthRequest`, `RequestStore` and `RequestStoreTest` are unchanged (marked so for this intent).

**NFR6 – Fail fast on bad configuration.** A malformed holiday file or a missing/negative
`priorauth.aging.threshold-days` stops the application at startup rather than serving wrong ages.

**NFR7 – Verified.** `./scripts/verify.sh` (or `scripts\verify.cmd` on Windows) passes before the change is called done.

## Assumptions (to confirm where marked)

- **A-01** The nightly report uses exactly this rule (received day = day 0, `> 5`, the FR8 dates). We cannot see the
  report's code; the answers are our only source. **Confirm against one real report row.**
- **A-02** The label for a row **not** over the limit is `"<age> bd"` (e.g. `"4 bd"`); the screen team gave only the
  over example. Single space, lowercase `bd`, uppercase `OVER`, no "1 bd" singular form. **Confirm with the screen team.**
- **A-03** FR11 applies to the whole call: one row received after `asOf` makes the call a 400, since `asOf` is one
  date for all rows. Rows with `receivedAt` in the future relative to the *default* (server) date are not a caller
  error: without `asOf`, such a row gets age 0 rather than a 400 (the caller sent nothing wrong). **Confirm.**
- **A-04** A tenant with **no holiday file** counts weekends only and logs a warning at startup; it does not fail and
  does not drop the row. Today only TX-01 exists, so the sample is not affected. **Confirm.**
- **A-05** Only 2026 holidays exist. The `-2026` in the file name suggests one file per tenant per year; the loader
  reads every `data/holidays-<tenant>-<yyyy>.json` present, so 2027 is a data file, not code. Until it exists, ages
  over dates outside 2026 count weekends only and may be overstated.
- **A-06** "Server's zone" means the JVM default zone (`ZoneId.systemDefault()`). If the server runs in UTC, the date
  switches at 18:00/19:00 Central; callers that care pass `asOf`.
- **A-07** `asOf` does not change which rows are pending (status is as loaded).
- **A-08** The holiday file is a plain JSON array of ISO date strings (`["2026-01-01", ...]`).
- **A-09** README gets one line on the new fields and `asOf` (documentation only).

## Worked check: sample data as of 2026-10-13 (Tuesday)

Calendar: Thu 10-01, Fri 10-02, Mon–Fri 10-05..10-09, **Mon 10-12 holiday**, Tue 10-13. Threshold 5.

| id       | status    | receivedAt       | business days counted (after receipt, ≤ 10-13)                  | ageBusinessDays | overLimit | ageLabel        |
|----------|-----------|------------------|-----------------------------------------------------------------|-----------------|-----------|-----------------|
| PA-10231 | PENDED    | 2026-10-01 (Thu) | 10-02, 10-05, 10-06, 10-07, 10-08, 10-09, 10-13 (10-12 skipped)  | **7**           | **true**  | `"7 bd OVER 5"` |
| PA-10244 | IN_REVIEW | 2026-10-06 (Tue) | 10-07, 10-08, 10-09, 10-13 (10-12 skipped)                       | **4**           | **false** | `"4 bd"`        |
| PA-10250 | APPROVED  | 2026-10-07       | not pending, not returned                                       | –               | –         | –               |
| PA-10263 | PENDED    | 2026-10-09 (Fri) | 10-13 (10-10/11 weekend, 10-12 holiday)                          | **1**           | **false** | `"1 bd"`        |

So `GET /requests/pending?asOf=2026-10-13` returns 3 rows in this order with ages 7, 4, 1, `overLimit` true, false,
false. PA-10231's label matches the screen team's example exactly. Without the 10-12 holiday the ages would be 8, 5,
2: the holiday changes every number but no flag, so tests must assert the ages, not only the flags.

FR11 check on the same data: `asOf=2026-10-05` is before PA-10244 (10-06) and PA-10263 (10-09) → 400.
`asOf=2026-10-09` is valid (PA-10263 age 0, label `"0 bd"`).

## Out of scope / not checked

- A shared holiday calendar service; holidays for years other than 2026; other tenants' calendars.
- The nightly report's code and the reviewer screen's code were not available, so the match with the report (A-01)
  and the non-over label format (A-02) rest on the answers alone.
- Version bump and tagging (Meena, at release).
