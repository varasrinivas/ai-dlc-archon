# Plan: New Year's Day counted as a working day (Ravi Menon, 17 Oct 2026)

Based on `scan.md`. The cause is in **priorauth-aging**. `HolidayCalendar.load()` only reads
`data/holidays-<tenant>-2026.json`, so no 2027 holiday is ever loaded. Also, no TX-01 2027 file exists yet.
**priorauth-api** gets no logic change. It moves to the fixed library and adds a test that reproduces Ravi's request.

Branch in both repos, from `main`: **`fix/holidays-across-years`**

## The approach

`HolidayCalendar.forTenant(String tenantId)` keeps its signature. It will return the **union of every year's file
for that tenant** on the classpath (`data/holidays-<tenant>-????.json`). An age range that crosses a year boundary
then sees the holidays of both years. That is what PA-10231 needs: 1 Oct 2026 → 5 Jan 2027.

Why this approach:
- It is the smallest complete change. The public API stays the same, so priorauth-api's controller doesn't change.
- It uses what is already on the classpath: Spring's `PathMatchingResourcePatternResolver` from spring-core. No new
  dependency.
- Every file for a tenant is small and cached for the process's lifetime. Loading all of them costs nothing that
  matters.

Pattern detail: use `????` (exactly four characters for the year), not `*`. With `*`, a tenant id that is a prefix
of another would pick up the other tenant's files. For example, `TX` would match `holidays-TX-01-2026.json`.

Rejected: passing a year range into `HolidayCalendar` (`forTenant(tenant, from, to)`). It is a new API, which means
a minor release. It also needs a controller change in priorauth-api, and it adds nothing for this bug.

## priorauth-aging

**Version:** 1.0.0 (pom `1.0.0`, tag `v1.0.0`) → **1.0.1**. This is a patch: a fix that keeps the API.

**Files to change**

| File | Change |
|---|---|
| `src/main/resources/data/holidays-TX-01-2027.json` | **New.** Copied byte-for-byte from `docs-in/holidays-TX-01-2027.json`: `tenantId` `TX-01` and 11 dates, 2027-01-01 … 2027-12-24. |
| `src/main/java/com/acmehealth/priorauth/aging/HolidayCalendar.java` | Change `load(tenantId)`: resolve `classpath*:data/holidays-<tenantId>-????.json` with a `PathMatchingResourcePatternResolver` (a private field, so the constructor stays `HolidayCalendar(JsonMapper)`). Parse each file exactly as today and add all its dates to one set. Return `Set.copyOf(...)`. Keep the rest as it is: no files means `Set.of()`; an `IOException` means `IllegalStateException("cannot read holidays for tenant …")`. Update the class javadoc to say "one JSON file per tenant per year". |
| `pom.xml` | `<version>1.0.0</version>` → `1.0.1`. |

**Tests to add**: a new `src/test/java/com/acmehealth/priorauth/aging/HolidayCalendarTest.java`. It is a plain
unit test using `new HolidayCalendar(JsonMapper.builder().build())`, the same way `RequestStoreTest` builds its mapper.

1. `loadsEveryYearForTheTenant`: `forTenant("TX-01")` contains `2026-01-01`, `2026-10-12` **and** `2027-01-01`.
   It has 22 dates: 11 from each file. This test would fail today.
2. `tenantWithoutFilesHasNoHolidays`: `forTenant("ZZ-99")` is empty. It pins the existing safe default.
3. `ageAcrossTheYearSkipsNewYearsDay`: the scenario from the report, run through the real calendar.
   `BusinessDays.between(2026-10-01, 2027-01-05, forTenant("TX-01")) == 62`. Today it is 63.

`BusinessDaysTest` and `AgeBadgeTest` stay as they are.

## priorauth-api

**Version:** 1.2.0 (pom `1.2.0`, tag `v1.2.0`) → **1.2.1**. A patch: a dependency bump that fixes a wrong value,
with no API change.

**Files to change**

| File | Change |
|---|---|
| `pom.xml` | `<version>1.2.0</version>` → `1.2.1`. The `priorauth-aging` dependency goes from `1.0.0` → `1.0.1`. |

No change to `src/main`.

**Tests to add**: one test method in the existing
`src/test/java/com/acmehealth/priorauth/api/PendingRequestsControllerTest.java`:

- `newYearsDayIsNotABusinessDay`: `GET /requests/pending?asOf=2027-01-05` should return:

  | Row | Request | Received | Expected age | Today's age | Label |
  |---|---|---|---|---|---|
  | `$[0]` | PA-10231 | 2026-10-01 | 62 bd | 63 bd | `62 bd OVER 5` |
  | `$[1]` | PA-10244 | 2026-10-06 | 60 bd | 61 bd | |
  | `$[2]` | PA-10263 | 2026-10-09 | 57 bd | 58 bd | |

  The expected figures are my hand count: weekdays in range minus 12 Oct, 11 Nov, 26 Nov, 27 Nov, 25 Dec 2026 and
  1 Jan 2027. They match Ravi's "one lower than the screen" for every row. If the verify run disagrees, stop and
  re-count before you change a number.

The existing `eachRowCarriesItsAgeAndFlag` (asOf 2026-10-13, 7 bd and 4 bd) stays as it is. It proves the 2026 file
is still loaded.

## Order

**Change**
1. priorauth-aging: on `fix/holidays-across-years`, add the 2027 file, the `HolidayCalendar` change,
   `HolidayCalendarTest` and pom 1.0.1. Commit there.
2. priorauth-api: on `fix/holidays-across-years`, make the pom changes (1.2.1, aging 1.0.1) and add the new controller
   test. Commit there.

The aging change comes first because the api pom can only resolve 1.0.1 once the library has been installed.

**Release** (CLAUDE.md)
1. The priorauth-aging PR is merged first, and 1.0.1 is published and tagged `v1.0.1`.
2. The priorauth-api PR is merged second, then tagged `v1.2.1`.

Its pom names aging 1.0.1, so merging it before step 1 would break its build anywhere but this workspace. Pushing and
opening the PRs is the workflow's last node, not this plan's.

Nothing is committed in the workspace folder. The original `docs-in/holidays-TX-01-2027.json` stays where it is.

## How `./scripts/verify.sh` proves it

`scripts/verify.sh` (`scripts\verify.cmd` on Windows) does two things:

1. **`cd priorauth-aging && mvn -q install`**: builds 1.0.1 from the working branch, runs `BusinessDaysTest`,
   `AgeBadgeTest` and the new `HolidayCalendarTest`, and installs `priorauth-aging-1.0.1.jar` into `~/.m2`. The
   2027 file is inside that jar. `loadsEveryYearForTheTenant` and `ageAcrossTheYearSkipsNewYearsDay` (62) fail on
   the old code.
2. **`cd priorauth-api && mvn -q test`**: resolves aging **1.0.1**, the jar just installed, so the API is tested
   against the fix and not the stale 1.0.0. It runs the whole application through MockMvc:
   - `newYearsDayIsNotABusinessDay` reproduces Ravi's exact request and expects 62, 60 and 57.
   - `eachRowCarriesItsAgeAndFlag` still expects 7 and 4 for 2026-10-13, so there is no regression.
   - `asOfBeforeReceivedIsABadRequest` still expects 400.
   - `RequestStoreTest` is unchanged.

A green run means: the 2027 holidays load, the 2026 ones still load, a range across the year skips 1 Jan, and the
API serves the corrected age. Recommended: add the two failing tests first and run verify once to see them fail
(red), then make the fix (green).

## Assumptions and open questions

- **A1.** The attached 2027 list from payer ops is authoritative and is the same list the nightly report uses. I have
  not checked it against the nightly report's source.
- **A2.** Patch versions (1.0.1, 1.2.1) are right, because no public signature changes.
- **Q1, for the team.** When a tenant has no file for the year an age touches, the calendar still quietly uses no
  holidays. That is how this bug happened, and it will happen again in January 2028 unless someone adds a 2028
  file. The fix could log or fail when that year is missing. This plan does **not** do that: nobody asked for it,
  and it changes behaviour. Raise it with Ravi and Kiran.

## Skipped / not checked / risk

- **Not checked:** remotes and open PRs, and whether any other consumer of priorauth-aging exists outside these
  two repos.
- **Risk:** `classpath*:` with a wildcard must also find the files inside the packaged Spring Boot jar, not only in
  `target/classes`. Maven tests run against the installed library jar in `~/.m2`, so step 2 of verify exercises the
  jar case. `mvn spring-boot:run` and the fat jar are not covered by verify.
- **Risk:** a malformed or misnamed holiday file now affects every age for that tenant, not just one year's. The
  existing `IllegalStateException` on a read error is kept, so the failure stays loud.
- **Not done:** I did not check that a file's `tenantId` field matches its file name. Today's code doesn't check it
  either. It is out of scope.
