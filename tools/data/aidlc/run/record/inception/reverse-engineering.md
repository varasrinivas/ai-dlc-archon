# Reverse Engineering (AI-DLC stage 2.1, Inception)

Request: `docs-in/request.md`. Ravi Menon (UM Nurse Manager) asks for the pending list from `GET /requests/pending` to
carry **the same business-day age and the over-5 flag as the nightly report**, where weekends and the company's holidays
do not count. "Nothing else changes."
Repo: `priorauth-api/` only. Nothing was changed. Baseline `scripts\verify.cmd` was run: **green** (3 tests, exit 0).

## Questions only a person can decide

The business rule lives in the nightly report, and **the report's code, rule and holiday list are not in this workspace**
(searched `C:\work\archon-aidlc` for `holiday`, `business day`, `over-5`: only the request matches). "Same rule as the
report" can't be checked against anything here, so these must be answered before Requirements.

1. **Where does the holiday list come from?**
   - a) Someone sends the report's holiday list (dates for 2026 and 2027) and we keep it as a config list in `application.yml`, so it can be changed without touching code. *(recommended)*
   - b) The same list, hard-coded in a Java class.
   - c) Read it from the report's source or a shared calendar service (we need a path or URL; this probably means a new dependency or integration, which is out of scope for "nothing else changes").
2. **How exactly does the report count age?** (We need the report's definition or a few worked examples.)
   - a) Business days *after* `receivedAt`, up to and including today (received today = 0). *(recommended guess, the common convention)*
   - b) Counting the received day too (received today = 1).
   - c) Something else (please give it).
   It also needs settling whether a request received on a weekend or holiday starts counting from the next business day.
3. **What does "over-5" mean?**
   - a) age > 5 (6 or more business days). *(literal reading)*
   - b) age >= 5.
4. **"Today" by which clock?** The API has no time zone setting; it runs on the server's default zone. The test machine is UTC+05:30.
   - a) A fixed business time zone (which one? the report's, for example `America/Chicago` for tenant TX-01). *(recommended)*
   - b) The server's default time zone.
5. **Same holidays for every tenant?** Rows carry `tenantId` (sample: only `TX-01`).
   - a) One calendar for all tenants. *(recommended unless the report already differs per tenant)*
   - b) A calendar per tenant.
6. **JSON field names the reviewer screen will read.** New fields are added; the existing ones stay as they are.
   - a) `ageBusinessDays` (number) and `overFiveBusinessDays` (boolean).
   - b) Match the report's column names (please give them, e.g. `age` / `over5`).
   - c) The screen team names them.
7. **Version.** pom is `1.0.2`, the repo has **no tags**. A new field that is purely added suggests **1.0.3** (a: patch) or **1.1.0** (b: minor, since the API contract grows). *(recommended: b)*

## Map of the existing code

`priorauth-api/`: one Maven module, Spring Boot **4.1.1** (parent `spring-boot-starter-parent`), Java **21**, version
`1.0.2`, groupId `com.acmehealth`. Remote `github.com/varasrinivas/aidlc-priorauth-api`, `main` @ `d9aa178`, clean, no tags.
No database: data is a JSON export packed into the jar.

| Path (`src/main/java/com/acmehealth/priorauth/`) | Role |
|---|---|
| `PriorAuthApiApplication.java` | Entry point (`@SpringBootApplication`), component scan from this package down. |
| `api/PendingRequestsController.java` | **The only HTTP entry point:** `GET /requests/pending` → `store.pending()` mapped by `PendingRequestResponse::from`. No paging, no tenant filter, no auth. |
| `api/PendingRequestResponse.java` | Record = the JSON contract of one row: `id, tenantId, service, status, receivedAt` (`LocalDate`, ISO `yyyy-MM-dd`). Static `from(PriorAuthRequest)`. Deliberately leaves out `memberId`. **This is where new fields would go.** |
| `model/PriorAuthRequest.java` | Domain record: `id, tenantId, memberId, service, status, receivedAt`. `isPending()` = status in `{PENDED, IN_REVIEW}`. Javadoc: "unchanged by intent 261013-request-age-api". |
| `store/RequestStore.java` | `@Service`; loads `data/requests.sample.json` with Jackson 3 (`tools.jackson.databind.json.JsonMapper`) at startup, sorted by `receivedAt` then `id`; `all()`, `pending()`. Javadoc says production reads the queue DB; same "unchanged" note. |
| `src/main/resources/application.yml` | Only `spring.application.name` and `server.port: 8080`. No clock, time zone or calendar config. |
| `src/main/resources/data/requests.sample.json` | 4 rows, `TX-01`, received 2026-10-01 (Thu), 10-06 (Tue), 10-07 (Wed, APPROVED), 10-09 (Fri). 3 pending. |

Data flow: JSON file → `RequestStore` (startup, in memory) → `pending()` filter → controller → `PendingRequestResponse` → JSON array.

Notes in the code: `PriorAuthRequest`, `RequestStore` and `RequestStoreTest` already carry "unchanged by intent
261013-request-age-api" comments, which says the expected change is in the `api` layer (response + whatever computes the age),
not in the model or the store.

## Tests

| Test | Kind | Covers |
|---|---|---|
| `api/PendingRequestsControllerTest` | `@SpringBootTest` + `@AutoConfigureMockMvc` (full context) | `GET /requests/pending`: 200, 3 rows, first is `PA-10231` with `receivedAt` `2026-10-01`. |
| `store/RequestStoreTest` | Plain unit test (real `JsonMapper`) | Loads 4 rows oldest first; `pending()` excludes APPROVED. |

There is no business-day or date logic anywhere yet, so nothing to reuse. Age depends on "today": **no `java.time.Clock` is
injected anywhere**, so a deterministic test needs one (a `Clock` bean, overridable in tests). That is plain JDK, no new
dependency.

## Build and run

- Verify (the only sanctioned way): `./scripts/verify.sh` (bash) / `scripts\verify.cmd` (Windows), from the workspace → `cd priorauth-api && mvn -q test`.
- Toolchain: system Maven 3.9.16, Temurin JDK 21.0.10. No Maven wrapper.
- Package `mvn package`; run `mvn spring-boot:run` → `http://localhost:8080/requests/pending`.
- Dependencies: `spring-boot-starter-webmvc`; test `spring-boot-starter-webmvc-test` (JUnit 5, AssertJ, MockMvc, Mockito). `java.time` covers business-day counting: **no dependency needed**.
- No CI/CD (stage 0.2).

## Architect's view

- **Two copies of one rule.** The report and the API will each count business days. If they differ by a day, the nurse sees
  different ages in two places. The right long-term home is one shared calendar/rule, but that is outside this request. For now,
  prove parity with tests using the report's own worked examples (needs Q2) and record the duplication as known debt.
- **Time zone is a real risk:** the server runs IST here, and US tenants. Around midnight, age could be off by one (Q4).
- **Holiday list needs an owner:** if it is config with no one updating it, age silently drifts in January (Q1). Suggest
  a startup check or log line if the list has no dates for the current year (decide in the plan).
- Contract change is purely added (new JSON fields), so existing clients won't break; Jackson writes them by default.
- Likely touch points (for the plan, not decided here): `PendingRequestResponse` (+2 fields), a small business-day
  calculator in `api/` or a new package, a `Clock` bean, holiday config in `application.yml`, tests for the calculator
  (weekends, holidays, boundary at 5) and an extended controller test with a fixed clock.

## Not checked / risks

- Did not see the nightly report, its rule or its holiday list: "same rule" is unverified until Q1–Q3 are answered.
- Did not check the reviewer screen's code or how it parses the response.
- Production `RequestStore` (queue DB) is not in this repo; only the sample-file version was read.
- Verify printed a Mockito self-attach / dynamic agent warning on JDK 21: harmless today, not fixed (unrelated).
- No auth or tenant scoping on the endpoint: noted, not in scope.
