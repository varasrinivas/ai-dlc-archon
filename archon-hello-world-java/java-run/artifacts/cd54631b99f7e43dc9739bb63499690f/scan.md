# Scan — request-age API (docs-in/request.md)

## The request
Ravi Menon (UM Nurse Manager), 13 Oct: the reviewer screen reads `GET /requests/pending` from priorauth-api and
should show the same **business-day age** and **over-5 flag** that the nightly report already shows.
"Same rule as the report: weekends and our holidays do not count. Nothing else changes."

## The repo
- Spring Boot 4.1.1 (parent POM), Java 21, Maven, artifact `com.acmehealth:priorauth-api` **1.0.2**.
- One dependency: `spring-boot-starter-webmvc` (+ `spring-boot-starter-webmvc-test`, test scope). Jackson 3
  (`tools.jackson.databind`) comes with it.
- No database: requests are read from a JSON export packed into the jar.
- Verify: `./scripts/verify.sh` (runs `mvn -q test`); `scripts\verify.cmd` by hand on Windows. Tests only through it.
- Git: tags not yet checked; one prior commit says "priorauth-api 1.0.2". Check `git tag` + pom version before proposing a version.

## Files the request touches (what they do now)
- `src/main/java/com/acmehealth/priorauth/api/PendingRequestResponse.java` — record of the JSON row
  (`id, tenantId, service, status, receivedAt`); `from(PriorAuthRequest)` maps the model. **The fields go here.**
- `src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java` — `GET /requests/pending`, maps
  `store.pending()` through `PendingRequestResponse::from`. Needs a "today" and the age rule to pass in.
- `src/main/java/com/acmehealth/priorauth/model/PriorAuthRequest.java` — the queue record; `receivedAt` is a
  `LocalDate` (no time, no zone); `isPending()` = status PENDED or IN_REVIEW. Javadoc says "unchanged by intent
  261013-request-age-api".
- `src/main/java/com/acmehealth/priorauth/store/RequestStore.java` — loads `data/requests.sample.json`, sorts
  oldest first (receivedAt, then id); `all()`, `pending()`. Javadoc also says "unchanged by intent".
- `src/main/resources/application.yml` — only app name and port 8080. Natural place for a holiday list / threshold if
  configured.
- `src/main/resources/data/requests.sample.json` — 4 requests, tenant TX-01: PA-10231 PENDED 2026-10-01 (Thu),
  PA-10244 IN_REVIEW 2026-10-06 (Tue), PA-10250 APPROVED 2026-10-07, PA-10263 PENDED 2026-10-09 (Fri).
- `PriorAuthApiApplication.java` — plain `@SpringBootApplication` entry point; no `Clock` bean.
- Tests: `PendingRequestsControllerTest` (full context + MockMvc: 3 rows, first PA-10231, receivedAt 2026-10-01);
  `RequestStoreTest` (4 loaded oldest first; pending = 10231, 10244, 10263).

## What is missing
1. **The holiday calendar.** Nothing in the repo lists holidays (grep for holiday/business day/clock: only the
   request). "Our holidays" lives with the nightly report, which is not in this repo — need the list (dates, years
   covered, per tenant or global) and its source of truth. Example: Mon 2026-10-12 (Columbus/Indigenous Peoples' Day)
   changes the sample answer.
2. **The exact counting rule** from the report: is the received day counted? today? A request received on a
   weekend/holiday? What is age on the day it arrives (0 or 1)?
3. **"Over 5"**: strictly `> 5` or `>= 5`? Field names and JSON types the screen expects (e.g. `ageBusinessDays`
   int, `overdue`/`over5` boolean)?
4. **"Today"**: which time zone (server default vs. a business zone), and a way to fix it in tests — there is no
   `Clock` bean; tests will need an injectable `Clock` or a fixed date, or results drift daily.
5. Where the threshold and holidays are configured (application.yml vs. code vs. a data file).

Worked example, as of Tue 2026-10-13, counting business days after receipt up to and including today, weekends out:
PA-10231 = 8 (7 if 10-12 is a holiday) → over 5; PA-10244 = 5 (4); PA-10263 = 2 (1). Both the 10-12 holiday and the
`>5` vs `>=5` choice change PA-10244's flag — the questions must settle them.

## Risks
- **API contract**: adding JSON fields is additive, but the screen (and any other caller) must tolerate unknown fields;
  renaming/removing existing fields would break it. "Nothing else changes" — keep order, filter, existing fields.
- **Tests**: `PendingRequestsControllerTest` uses the full context; age depends on today's date, so any new assertion
  must pin the clock. Adding a `Clock` bean or constructor parameter changes the controller's constructor.
- **Untouchables**: `PriorAuthRequest` and `RequestStore` are marked "unchanged by intent 261013-request-age-api";
  `RequestStoreTest` likewise — keep the age logic out of them.
- **Drift from the report**: if the holiday list is copied here, it can diverge from the report's; note who owns it.
- **No new dependency** is needed (`java.time` covers it); any added one must be named in the plan.
- **Time zone**: `LocalDate.now()` on a UTC server can be a day off for evening US requests.
