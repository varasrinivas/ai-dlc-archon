# Requirements Analysis (AI-DLC stage 2.3, Inception), version 2

Request: `docs-in/request.md`, from Ravi Menon (Nurse Manager, Utilization Management), 13 Oct.
> Can the pending list the API returns carry the same business-day age and the over-5 flag, so the screen can show it?
> Same rule as the report: weekends and our holidays do not count. Nothing else changes.

Repo: `priorauth-api/` only (`main` @ `d9aa178`, version `1.0.2`, no tags). Endpoint: `GET /requests/pending`.
Inputs read: `record/workspace.md`, `record/inception/reverse-engineering.md`, the request, the code, and the answers from
Ravi and Meena on version 1. No code changed.

## Questions only a person can decide

**None open.** All seven questions from version 1 are answered:

| # | Question | Decision (Ravi, Meena) |
|---|---|---|
| 1 | Holiday source | One JSON file per tenant in the API resources: `data/holidays-<tenant>-2026.json`. TX-01 2026: 01-01, 01-19, 02-16, 05-25, 07-03, 09-07, 10-12, 11-11, 11-26, 11-27, 12-25. A shared calendar service is separate work. |
| 2 | Counting | The received day is day 0, same as the report. |
| 3 | Over-5 | "Over" means more than the threshold. Threshold 5, from config key `priorauth.aging.threshold-days`. |
| 4 | Clock | The server's time zone. Callers can pass `asOf` to pin the date. An `asOf` before the received date is a caller error (400), not age 0. |
| 5 | Tenants | A calendar per tenant (the files above). |
| 6 | Field names | Set by the screen team: `ageBusinessDays` (integer), `overLimit` (boolean), `ageLabel` (text, e.g. `"7 bd OVER 5"`). |
| 7 | Version | Stays `1.0.2`; Meena sets the version at release. |
| — | Behaviour | The API returns a flag and never refuses or alerts. |

The few details the answers leave open are settled below as assumptions (A1–A8); each is a default the plan can follow
without asking again. Object to any of them at approval.

## Requirements

### Response fields

- **R1.** Every row of `GET /requests/pending` carries `ageBusinessDays`: an integer, 0 or more, the number of business days after `receivedAt` up to and including the as-of date. The received day itself is day 0 (received on the as-of date → 0).
- **R2.** A business day is a Monday–Friday date that is not on the row's tenant holiday list (`data/holidays-<tenantId>-2026.json`).
- **R3.** Every row carries `overLimit`: `true` exactly when `ageBusinessDays` > the threshold. Derived from the same age the row shows.
- **R4.** Every row carries `ageLabel`: `"<age> bd"`, and when `overLimit` is true `"<age> bd OVER <threshold>"` (e.g. `"7 bd OVER 5"`, `"4 bd"`). See A1.
- **R5.** The existing fields (`id`, `tenantId`, `service`, `status`, `receivedAt`) keep their names, types and format; `memberId` stays out. Same rows, same oldest-first order, same filter (PENDED, IN_REVIEW). The model (`PriorAuthRequest`) and store (`RequestStore`) do not change.

### As-of date

- **R6.** Without `asOf`, the as-of date is today in the server's default time zone.
- **R7.** `GET /requests/pending?asOf=YYYY-MM-DD` (ISO date) pins the as-of date for every row in that response.
- **R8.** If `asOf` is earlier than the `receivedAt` of any row in the response, the API answers **400** and returns no list. See A3.
- **R9.** An `asOf` that is not a valid ISO date answers **400**. See A4.

### Configuration and data

- **R10.** The threshold is read from `priorauth.aging.threshold-days`, set to `5` in `application.yml`.
- **R11.** Holidays are read from `src/main/resources/data/holidays-<tenantId>-2026.json`. This change adds `holidays-TX-01-2026.json` with exactly the 11 dates above. Changing holidays means editing that file, not Java code.
- **R12.** The API flags and never refuses or alerts: no row is hidden, rejected or reordered because of its age; nothing is sent anywhere. Only the caller errors in R8/R9 give a non-200.

### Proof and constraints

- **R13. Report parity.** Tests use a fixed date and the TX-01 file. As of Tue 13 Oct 2026 (12 Oct is a holiday), the sample gives:

  | Request | Received | `ageBusinessDays` | `overLimit` | `ageLabel` |
  |---|---|---|---|---|
  | PA-10231 | Thu 1 Oct | 7 | true | `7 bd OVER 5` |
  | PA-10244 | Tue 6 Oct | 4 | false | `4 bd` |
  | PA-10263 | Fri 9 Oct | 1 | false | `1 bd` |

- **R14. Rule tests** cover: received on the as-of date (0); a weekend in the span; a holiday in the span; received on a Saturday and on a holiday; the boundary (age 5 → `overLimit` false, age 6 → true); a tenant with no holiday file (A2); `asOf` before `receivedAt` → 400; malformed `asOf` → 400.
- **R15. Deterministic.** "Today" comes from a `java.time.Clock` the app uses and tests replace; no test depends on the real date.
- **R16. No new dependency.** `java.time` counts the days; the JSON files are read with the Jackson 3 already used by `RequestStore`. pom.xml unchanged, version stays `1.0.2`.
- **R17.** `./scripts/verify.sh` (`scripts\verify.cmd` on Windows) is green before done; the baseline was green with 3 tests.

## Assumptions

- **A1. Label format when not over:** `"<age> bd"` (e.g. `"4 bd"`), mirroring the screen team's example; singular stays `"1 bd"`. The threshold in the label is the configured value, not a literal 5. *If the screen team expects a different under-limit text, the plan changes one line.*
- **A2. Tenant with no holiday file:** weekends still skip; no holidays apply; the API still answers (R12) and logs a warning once naming the tenant. A log line is for operators, not an alert to users. The sample has only TX-01, so this happens only with new tenants.
- **A3. 400 on any row:** `asOf` applies to the whole list, so if it predates even one row's `receivedAt` the whole call is a caller error. The error body names the earliest allowed date in plain text; Spring's default error shape otherwise.
- **A4. Malformed `asOf`** is a caller error like A3 (400), not a 500 and not ignored.
- **A5. Dates outside 2026:** only the `-2026` file is read. Spans that reach into 2027 (or 2025) count weekends only for the dates outside 2026. See risk below.
- **A6.** `receivedAt` is a date with no time of day (`LocalDate`), so received time plays no part.
- **A7.** The reviewer screen ignores unknown fields, and adding three fields does not break any other caller (none is known).
- **A8.** The production queue-database store is outside this repo; the change sits in the `api` layer (plus config, the holiday file and a `Clock`) and works with whatever store supplies `receivedAt` and `tenantId`.

## Out of scope

- A shared calendar service used by both the report and the API (separate work, per Ravi and Meena).
- 2027 holiday files, paging, tenant filtering, auth on the endpoint.
- Changes to the reviewer screen; setting the release version (Meena does it).
- The Mockito self-attach warning printed by verify on JDK 21 (harmless, unrelated).

## Not checked / risks

- **Year rollover:** the file name pins 2026. From 1 Jan 2027 holidays stop counting (A5) until a 2027 file exists and the loader reads it; ages could then exceed the report's. Someone should own adding the 2027 file before January; reading by year is a small plan choice.
- **Server time zone:** the server runs on its default zone (the test machine is UTC+05:30, tenants are US). Near midnight the default age can differ by one from the report; callers who care pass `asOf`. This was decided, recorded here as a known risk.
- **Two copies of one rule** (report and API) until the shared calendar exists; R13 proves parity for the sample only.
- Did not see the report's code or the reviewer screen's code. No tests run in this stage.
