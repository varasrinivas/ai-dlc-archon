# Scan: request age on the pending list (API)

Request: `docs-in/request.md` (Ravi Menon, Nurse Manager UM, Tue 13 Oct). The pending list returned by
`GET /requests/pending` should carry the **same business-day age and the over-5 flag as the nightly report**.
Weekends and "our holidays" do not count. "Nothing else changes."

## The repo and how it is built and tested

- `priorauth-api/`: Spring Boot 4.1.1 (starter parent), Java 21, Maven, version **1.0.2** (`pom.xml`).
  Dependencies: `spring-boot-starter-webmvc` and `spring-boot-starter-webmvc-test` (test). Jackson 3 (`tools.jackson`).
- No database. Requests come from `src/main/resources/data/requests.sample.json`, packed into the jar.
- Git: current branch `main`, clean, one commit `d9aa178 priorauth-api 1.0.2: pending list for the reviewer screen`.
  **No tags**, locally or on origin (`C:\work\archon-java\remotes\priorauth-api.git`, only `refs/heads/main`).
- Verify (CLAUDE.md): `./scripts/verify.sh` from the workspace folder (`scripts\verify.cmd` by hand on Windows);
  it runs `mvn -q test` in priorauth-api. Last surefire run in `target/`: 3 tests, all pass.

## Files the request touches

| File | What it does now |
|---|---|
| `src/main/java/.../api/PendingRequestResponse.java` | Record sent as JSON per row: `id, tenantId, service, status, receivedAt` (LocalDate); `from(PriorAuthRequest)` maps it. The obvious place for new `ageBusinessDays` / over-5 fields. |
| `src/main/java/.../api/PendingRequestsController.java` | `GET /requests/pending`: `store.pending()` mapped through `PendingRequestResponse::from`. Needs "today" to compute an age. |
| `src/main/java/.../model/PriorAuthRequest.java` | Record `id, tenantId, memberId, service, status, receivedAt`; `isPending()` = status in {PENDED, IN_REVIEW}. Comment says unchanged by intent 261013-request-age-api. |
| `src/main/java/.../store/RequestStore.java` | Loads the sample JSON at startup, sorts by `receivedAt` then `id`; `all()`, `pending()`. Comment says unchanged by this intent. |
| `src/main/java/.../PriorAuthApiApplication.java` | Spring Boot entry point. No `Clock` bean, no other config. |
| `src/main/resources/application.yml` | Only app name and port 8080. No holiday list, no age threshold. |
| `src/main/resources/data/requests.sample.json` | 4 requests, TX-01: PA-10231 PENDED 2026-10-01, PA-10244 IN_REVIEW 2026-10-06, PA-10250 APPROVED 2026-10-07, PA-10263 PENDED 2026-10-09. |
| `src/test/java/.../api/PendingRequestsControllerTest.java` | `@SpringBootTest` + MockMvc: 3 rows, `$[0].id` PA-10231, `$[0].receivedAt` 2026-10-01. |
| `src/test/java/.../store/RequestStoreTest.java` | Store loads 4 oldest first; pending = PA-10231, PA-10244, PA-10263. Says unchanged by this intent. |
| `README.md` | Describes the endpoint; would need a line if the response gains fields (optional). |

## What is missing for the request

The request says "same rule as the report", but **the nightly report's code is not in this workspace** (no other repo,
and a search of `C:\work\archon-java` for "holiday" / "business day" finds only the request). So none of the rule
exists here:

1. **Holiday calendar**: which dates are "our holidays" (list, years covered, per tenant or global, where it lives:
   config, data file, or shared with the report). Nothing in the repo.
2. **Age definition**: is the received day counted (day 0 or day 1)? Is today counted? What if `receivedAt` falls on a
   weekend/holiday? Exactly what the report computes must be matched, and we cannot see it.
3. **Over-5 flag**: `> 5` or `>= 5` business days; field name and JSON shape the screen expects
   (e.g. `ageBusinessDays`, `overFive`/`overdue`). The screen's contract is not in the repo.
4. **"Today"**: which date/time zone the age is measured against (server clock, tenant zone, the export date?).
   There is no `Clock` bean, so a testable time source must be added (JDK `java.time.Clock`, no new dependency).
5. **Tests** for the business-day logic (weekend, holiday, boundary at 5) — new branching logic, required by CLAUDE.md.
6. **Version**: pom is 1.0.2, no tags; the plan should say whether this bumps to 1.0.3 / 1.1.0 (new response fields =
   backward-compatible addition, suggesting a minor bump), confirmed with the team.

## Risks

- **JSON contract**: adding fields to `PendingRequestResponse` is additive; renaming/removing any existing field would
  break the reviewer screen. Strict clients that reject unknown fields would break on addition (unknown; ask).
- **Time-dependent tests**: computing age from the real clock makes `PendingRequestsControllerTest` (full context)
  non-deterministic; a fixed `Clock` is needed in tests. Sample dates are Oct 2026; today is 2026-11-04, so all three
  pending rows would be well over 5 with a real clock.
- **Mismatch with the report**: if the rule or holiday list differs from the report's, the screen and report will show
  different ages for the same request — the main business risk. Duplicating the holiday list in two places drifts over time.
- **"Unchanged" markers**: `PriorAuthRequest`, `RequestStore`, `RequestStoreTest` are marked unchanged by this intent;
  the change should stay in the api layer (response + controller) plus a new calculator and its config/test.
- Existing callers: only the controller uses `RequestStore.pending()` and `PendingRequestResponse.from`; changing
  `from`'s signature (e.g. passing today/age) touches only the controller.

## Not checked

- Did not run `verify.sh` (scan is read-only); test status is from the existing `target/surefire-reports`.
- The nightly report's source and the reviewer screen's code were not available.
