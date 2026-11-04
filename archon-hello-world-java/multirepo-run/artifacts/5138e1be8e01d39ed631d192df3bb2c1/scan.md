# Scan: New Year's Day counted as a working day (Ravi Menon, 17 Oct 2026)

Source: `docs-in/bug-report.md`. Attachment next to it: `docs-in/holidays-TX-01-2027.json`.
Ravi's report: `GET /requests/pending?asOf=2027-01-05` shows PA-10231 (received 2026-10-01) and every other pending
TX-01 request one business day older than the nightly report gives. He thinks 1 Jan 2027 is counted as a working
day. The rule has not changed: weekends and the tenant's holidays don't count. The nightly report is correct.

## The repos

| | priorauth-aging | priorauth-api |
|---|---|---|
| What | Library: `BusinessDays`, `HolidayCalendar` (`@Service`), `AgeBadge` (record) in `com.acmehealth.priorauth.aging` | Spring Boot API: `GET /requests/pending[?asOf=]` (`PendingRequestsController`), `RequestStore` (reads `data/requests.sample.json`), `PriorAuthRequest` |
| Coordinates | `com.acmehealth:priorauth-aging:1.0.0` (pom) | `com.acmehealth:priorauth-api:1.2.0` (pom) |
| Tags | `v1.0.0` (only tag) | `v1.2.0` (latest tag; history covers 1.0.2 → 1.1.0 → 1.2.0) |
| Branch / state | `main`, clean, 1 commit (`f6153ee`) | `main`, clean, HEAD `c2dc5d4` |
| `fix/*` branches | none | none |
| Build | Maven, Java 21, parent `spring-boot-starter-parent` 4.1.1; deps: spring-boot-starter, `tools.jackson.core:jackson-databind` (Jackson 3) | Maven, Java 21, same parent 4.1.1; spring-boot-starter-webmvc, `priorauth-aging` **1.0.0** (pinned), spring-boot-maven-plugin |
| Tests | `BusinessDaysTest` (4), `AgeBadgeTest` (1). **No test for `HolidayCalendar`.** | `PendingRequestsControllerTest` (3, full `@SpringBootTest` + MockMvc), `RequestStoreTest` (2) |

**Dependency.** priorauth-api pulls priorauth-aging 1.0.0 out of the local Maven repo. The controller injects
`HolidayCalendar` and calls `AgeBadge.of(...)`. Component scanning picks up `HolidayCalendar`: the API's
`@SpringBootApplication` sits in `com.acmehealth.priorauth`, and the aging package is beneath it.

**Verification.** Only `scripts/verify.sh` / `scripts\verify.cmd` at the **workspace** root. It runs
`mvn -q install` in priorauth-aging and then `mvn -q test` in priorauth-api. Neither repo has a `scripts/` folder of
its own. CLAUDE.md's table ("Verify with `./scripts/verify.sh`" per repo) means the workspace script.

## The cause, as far as the code shows it

**priorauth-aging, `HolidayCalendar.load(String tenantId)`**
(`src/main/java/com/acmehealth/priorauth/aging/HolidayCalendar.java`):

```java
ClassPathResource file = new ClassPathResource("data/holidays-" + tenantId + "-2026.json");
```

- **The year is hardcoded to 2026.** `forTenant(tenantId)` only ever loads the 2026 file, so no 2027 date can be a
  holiday. That stays true even after a 2027 file is added.
- The cache is keyed by tenant only (`Map<String, Set<LocalDate>>`). It has no notion of a year, so one tenant gets
  one set.
- When the file is missing, `load` returns `Set.of()` without a sound ("the safe default: the age is then slightly
  higher, never lower"). That silent fallback is why the bug shows up as a wrong age and not as an error. For a
  2026 date the file is present. For 2027 dates, today's code doesn't even look for a file.

**priorauth-aging, `BusinessDays.between` / `isBusinessDay`**: correct. They count days after `start` up to and
including `end`, skipping Sat, Sun and any date in the set they are given. They only ever see the 2026 set. For
1 Oct 2026 → 5 Jan 2027 the range crosses the year, so the set needs holidays from **both** years.

**priorauth-api, `PendingRequestsController.pending(LocalDate asOf)`**
(`src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java`): it calls
`holidays.forTenant(r.tenantId())` with no year or range and passes the result to
`AgeBadge.of(r.receivedAt(), day, ..., thresholdDays)`. That is correct for the API's role. The defect is in the
library, not here.

**Arithmetic check (by hand, not run):** PA-10231, 2026-10-01 → 2027-01-05.
- Weekdays from 2 Oct to 5 Jan: 21 (Oct) + 21 (Nov) + 23 (Dec) + 3 (1, 4, 5 Jan) = 68.
- Minus the five 2026 TX-01 holidays in range (12 Oct, 11 Nov, 26 Nov, 27 Nov, 25 Dec) = **63**. That is what the screen shows today.
- Minus 1 Jan 2027 = **62**. That is what the nightly report should show.
- 1 Jan 2027 is a Friday and the only 2027 holiday before 5 Jan, so every pending row is exactly one too high.

This agrees with Ravi's report.

## What is missing, and where it belongs

1. **Data: the TX-01 2027 holiday file.** It belongs in **priorauth-aging** as
   `src/main/resources/data/holidays-TX-01-2027.json`, with the content of `docs-in/holidays-TX-01-2027.json`
   (same shape as the 2026 file: `tenantId` plus 11 dates, 2027-01-01 … 2027-12-24).
   Note: the tenant id is `TX-01`, so the name is `holidays-<tenant>-<year>.json` with a hyphen inside the tenant.
2. **Rule: load the holidays for every year the age range covers, not just 2026.** This also belongs in
   **priorauth-aging** (`HolidayCalendar`). Ways to do it, for the planner to choose from:
   - (a) Keep `forTenant(String)` and have it return the union of every `holidays-<tenant>-*.json` on the
     classpath. Spring's `PathMatchingResourcePatternResolver` is already available through spring-core, and the
     signature stays the same.
   - (b) Load per year and union the years from `receivedAt` to `asOf`. This changes or adds to the API, and
     priorauth-api's controller would need to change.
   - Option (a) keeps the public API as it is, which points to a **patch** release, aging 1.0.0 → **1.0.1**.
     priorauth-api then needs a dependency bump to 1.0.1 and its own patch, 1.2.0 → **1.2.1** (CLAUDE.md rule).
     Option (b) is a minor (1.1.0) if a method is added.
3. **Not in either repo, and an open question:** whether the "nightly report" reads these same files. The class
   javadoc says "the same list the nightly report uses". I have not checked that.

priorauth-api needs **no data change**. It holds no holiday data.

## Risks

**Callers**
- priorauth-aging:
  - `HolidayCalendar.forTenant` is called only by `PendingRequestsController.pending` (priorauth-api).
  - `AgeBadge.of` is called by the controller and `AgeBadgeTest`.
  - `BusinessDays.between` is called by `AgeBadge.of` and `BusinessDaysTest`.
  - No other callers in either repo. Callers outside these two repos, if the library is published, were not checked.
- If `forTenant`'s signature or the meaning of its return value changes, priorauth-api's controller must change in
  the same change. With option (a) it doesn't need to.
- Spring wiring: `HolidayCalendar` has a single `JsonMapper` constructor parameter. If a new constructor dependency
  is added (such as a resource resolver), it must still be resolvable in priorauth-api's context and in
  `@SpringBootTest`.

**Tests that a change could break**
- `PendingRequestsControllerTest.eachRowCarriesItsAgeAndFlag` (api): `asOf=2026-10-13`, expects PA-10231 = 7 bd
  ("7 bd OVER 5") and PA-10244 = 4 bd. It depends on 2026-10-12 still being loaded. Any change that drops or
  replaces the 2026 file breaks it.
- `PendingRequestsControllerTest.listsPendingRequestsOldestFirst` (api): no `asOf`, so it uses `LocalDate.now()`.
  It only asserts ids and count, so it is unaffected. `asOfBeforeReceivedIsABadRequest` relies on
  `IllegalArgumentException` from `BusinessDays.between` being mapped to 400. Keep that exception type.
- `BusinessDaysTest`, `AgeBadgeTest` (aging): they pass sets in directly, so a `HolidayCalendar` change doesn't
  touch them.
- No test covers `HolidayCalendar`, nor any range that crosses a year. The fix will need a new test for the
  file-loading and parsing logic (CLAUDE.md "Prove it"), for example a 2027 `asOf` in the controller test or a unit
  test for `HolidayCalendar`.
- Order of the release and the build: verify installs aging from the working tree. If the aging version bumps to
  1.0.1 and the api pom still says 1.0.0, the API is tested against a stale 1.0.0 in `~/.m2` (or fails to resolve).
  Bump both in the same change.

**Other observations (not to fix here)**
- The silent `Set.of()` for a missing file will cause the same bug again in January 2028 if nobody adds a 2028
  file. It could be worth a log line or a failure. That is the planner's or the team's call, not part of this request.
- Holiday sets go into a `ConcurrentHashMap` cache for the life of the process. A long-running instance won't see
  new files without a restart. Files ship in the jar, so this only matters across deployments.
- The priorauth-api README mentions `../aidlc/...`, which is not in this workspace. Unrelated.

## Not checked

- I did not run the verify script. This scan changes nothing.
- The 63 → 62 figures are hand arithmetic, not a test run.
- I did not compare the 2027 list against an authoritative TX-01 source. I took payer ops' attachment as given.
- I did not check the nightly report's source code or data.
- I did not check remotes or open PRs.
