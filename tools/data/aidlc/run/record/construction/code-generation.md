# Code Generation (AI-DLC stage 3.5, Construction)

Request: `docs-in/request.md` (intent 261013-request-age-api). Built against `record/inception/requirements-analysis.md` v2
(R1–R17, A1–A8). **No plan or design file exists in the record** (only workspace, reverse-engineering and requirements),
so the branch name and the code layout below are my choices, not an approved plan's.

## Result

- Repo `priorauth-api/`, branch **`request-age/pending-list-age`** from `main` @ `d9aa178`.
- Commit **`6103fdd`** "Request age on the pending list (intent 261013-request-age-api)", then **`d4a98c9`** (revision 2, below). Not pushed.
- `./scripts/verify.sh`: **green** (exit 0) at `d4a98c9`; `scripts\verify.cmd` was run green at `6103fdd` only. **19 tests**, 0 failures (baseline was 3; 16 after `6103fdd`).
- pom.xml unchanged: no new dependency, version stays `1.0.2` (R16).

## Revision 2 (commit `d4a98c9`, 2 files, +40 −8): answers Meena Iyer's "not pushing yet"

Kiran's jar check found `asOf=+999999999-12-31` never answered: it parsed, passed the "not before receivedAt" check,
and `BusinessDayCalendar`'s day-by-day loop ran for ~365 billion days.

- `PendingRequestsController`: an `asOf` after today (`LocalDate.now(clock)`, server zone) is now a **400 problem detail**
  under the same rule and shape as the too-early `asOf`: `detail` = "asOf is after today; the latest allowed asOf is
  <today>". The two cases share one exception (`AsOfTooEarlyException` renamed `BadAsOfException`, message passed in).
  The future check runs before the store is read. Accepted `asOf` is now bounded to [newest receivedAt, today], so the
  loop can no longer be driven by a caller; its length is bounded by the oldest pending row's age.
- An empty `asOf` (`?asOf=`) stays today: Spring's formatter turns the empty string into null. Unchanged code, now tested.
- Tests added to `PendingRequestsControllerTest`: `asOf=2026-10-14` (tomorrow vs the fixed clock) → 400 naming
  `2026-10-13`; `asOf=+999999999-12-31` → 400 naming `2026-10-13` (returns at once); `asOf=` → 200 with the
  clock's ages 7/4/1.
- `BusinessDayCalendar` itself unchanged (choice 4 stands: the loop is fine once inputs are bounded).
- Not checked: re-running Kiran's exact jar check over real HTTP (tested through MockMvc only); an `asOf` of today
  near midnight in another zone than the server's gets 400 for "tomorrow" (same server-zone risk as below).

## What changed in `6103fdd` (9 files, +297 −8)

| File | Change | Req |
|---|---|---|
| `api/PendingRequestResponse.java` | Adds `ageBusinessDays` (int), `overLimit` (age > threshold), `ageLabel` (`"4 bd"` / `"7 bd OVER 5"`). Existing fields unchanged, `memberId` still left out. | R1, R3, R4, R5, A1 |
| `api/BusinessDayCalendar.java` (new) | Counts Mon–Fri days after `receivedAt` up to and including the as-of date, minus the tenant's holidays. Loads `data/holidays-<tenant>-2026.json` once per tenant (Jackson 3, already used). No file: weekends only + one WARN log naming the tenant. Unreadable file: fails loud (500), not silently wrong. | R2, R11, A2, A5 |
| `api/PendingRequestsController.java` | Optional `asOf` (ISO date). Default: `LocalDate.now(clock)`. `asOf` before the newest row's `receivedAt` → 400 problem detail naming the earliest allowed date. Malformed `asOf` → 400 (Spring's type-mismatch default). Rows, order and filter unchanged. | R6–R9, R12, A3, A4 |
| `PriorAuthApiApplication.java` | `Clock` bean = `Clock.systemDefaultZone()` (server time zone). | R6, R15 |
| `application.yml` | `priorauth.aging.threshold-days: 5`. | R10 |
| `resources/data/holidays-TX-01-2026.json` (new) | Exactly the 11 TX-01 dates from the answers. | R11 |
| Tests | see below | R13, R14 |

Model (`PriorAuthRequest`) and store (`RequestStore`) are untouched (R5, A8).

## Tests added

- `PendingRequestsControllerTest` (full app, fixed `@Primary` clock at Tue 13 Oct 2026): R13 parity table from the clock
  (PA-10231 7/true/`7 bd OVER 5`, PA-10244 4/false/`4 bd`, PA-10263 1/false/`1 bd`); `asOf=2026-10-09` pins the date
  (received-today = 0); `asOf=2026-10-08` → 400 naming `2026-10-09`; `asOf=13/10/2026` → 400; (revision 2) future and far-future `asOf` → 400, empty `asOf` = today; existing test kept and now
  also checks `memberId` is absent.
- `BusinessDayCalendarTest` (real TX-01 file): same day = 0; weekend in span; holiday in span (Columbus Day, Thanksgiving
  pair); received on a Saturday; received on a holiday; tenant with no file counts weekends only.
- `PendingRequestResponseTest`: age 5 → not over, `"5 bd"`; age 6 → over, `"6 bd OVER 5"`; label uses the configured threshold.

## Choices to object to at approval

1. **Branch slug** `pending-list-age` (no plan named one).
2. **400 body** is Spring's `ProblemDetail` JSON (`application/problem+json`, the reason in `detail`), not a `text/plain` body:
   it stays readable for a client that only accepts JSON. A3 said "plain text" for the message; it is plain text inside `detail`.
3. **Malformed holiday file** → 500 rather than a quiet weekends-only count (a deploy defect, not a caller's fault).
4. Day-by-day loop for counting: spans are days to weeks, so no arithmetic shortcut.

## Skipped / not checked / risks

- **Year rollover (A5, unchanged):** only the `-2026` file is read. From 1 Jan 2027 holidays stop counting until a 2027
  file exists **and** the loader is changed to read by year. Someone must own this before January.
- **Server time zone:** default "today" is the server's zone (this machine is UTC+05:30); can be off by one vs the report
  near midnight. Callers pass `asOf` if they care. Decided, still a risk.
- Report parity is proven only for the sample (R13); I did not see the report's code or the reviewer screen's code.
- Did not run the app with `mvn spring-boot:run` or call it over HTTP outside MockMvc.
- No tests for a production queue-DB store (not in this repo).
- Mockito self-attach / dynamic agent warning on JDK 21 still printed by verify: unrelated, not fixed.
- Git warned LF→CRLF on the new files (repo has no `.gitattributes`); not changed.
