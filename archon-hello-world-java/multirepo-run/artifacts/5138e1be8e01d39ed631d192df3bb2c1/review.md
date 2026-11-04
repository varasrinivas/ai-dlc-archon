# Review: New Year's Day counted as a working day (fix/holidays-across-years)

Reviewed against `docs-in/bug-report.md` (Ravi Menon, 17 Oct 2026) and `plan.md`, by reading
`git -C <repo> diff main...HEAD` in each repo. Nothing was edited.

**Verdict: ready to push**, with one deviation from the plan that was justified and documented (see the API test ages
below).

## Branches and commits

| Repo | Branch | Base = `main`? | Commits on branch |
|---|---|---|---|
| priorauth-aging | `fix/holidays-across-years` | yes (f6153ee) | `074d524` Load every year's holiday file for a tenant; add TX-01 2027 (1.0.1) |
| priorauth-api | `fix/holidays-across-years` | yes (c2dc5d4) | `8d65a37` Depend on priorauth-aging 1.0.1; test New Year's Day ages (1.2.1) |

The workspace folder is clean. Nothing was committed there.

## 1. Is the bug fixed, with a test? Yes

- **Cause addressed.** `HolidayCalendar.load()` no longer hard-codes `-2026.json`. It resolves
  `classpath*:data/holidays-<tenant>-????.json` and returns the union of all the files' dates. The new
  `holidays-TX-01-2027.json` contains 2027-01-01.
- **Fixed against the real data.** The new resource has the same git blob hash as `docs-in/holidays-TX-01-2027.json`
  (`5e60ca99…`), so it is a byte-for-byte copy.
- **Tests in priorauth-aging (`HolidayCalendarTest`):**
  - `loadsEveryYearForTheTenant`: 22 dates, including 2026-01-01, 2026-10-12 and 2027-01-01.
  - `tenantWithoutFilesHasNoHolidays`: keeps the safe default.
  - `ageAcrossTheYearSkipsNewYearsDay`: 1 Oct 2026 to 5 Jan 2027 is 62.
  
  The first and third would fail on the old code.
- **Test in priorauth-api (`newYearsDayIsNotABusinessDay`):** reproduces Ravi's exact request,
  `GET /requests/pending?asOf=2027-01-05`.
- **The API test's expected ages differ from the plan, and the test is right.** The plan said 62 / 60 / 57. The test
  says 62 / 59 / 56. I recounted independently using `BusinessDays.between` semantics: business days strictly after the
  received date, up to and including the as-of date, minus weekends and TX-01 holidays.

  | Request | Received | With the fix | Old code (2026 file only) |
  |---|---|---|---|
  | PA-10231 | 2026-10-01 | **62** | 63 |
  | PA-10244 | 2026-10-06 | **59** | 60 |
  | PA-10263 | 2026-10-09 | **56** | 57 |

  The plan's 60 and 57 were its own miscount (its "today's age" column, 61 and 58, was off by one as well). The test
  values are exactly one lower than the old code for every row, which matches Ravi's report. `implementation.md`
  records this as Meena's correction, re-counted before the test was written. The plan required exactly that: stop and
  re-count rather than adjust a number to make the test pass.
- **No regression in 2026.** `eachRowCarriesItsAgeAndFlag` (asOf 2026-10-13) and `asOfBeforeReceivedIsABadRequest`
  are unchanged.

## 2. Do the versions follow CLAUDE.md? Yes

| Repo | Tag / pom on `main` | Branch pom | Type |
|---|---|---|---|
| priorauth-aging | `v1.0.0` / 1.0.0 | **1.0.1** | Patch. The fix keeps the API: `forTenant(String)` and the `HolidayCalendar(JsonMapper)` constructor are unchanged. |
| priorauth-api | `v1.2.0` / 1.2.0 | **1.2.1** | Patch. A dependency bump, no API change. |

- priorauth-api's `priorauth-aging` dependency goes from 1.0.0 to **1.0.1**, the version that contains the fix.
- Release order still applies: merge and tag aging `v1.0.1` first, then api `v1.2.1`. Until aging 1.0.1 is
  published, the api branch builds only where aging 1.0.1 has been installed locally.

## 3. Was anything changed that the plan didn't name? No

| Repo | Files changed | In the plan? |
|---|---|---|
| priorauth-aging | `pom.xml` | yes |
| | `src/main/java/.../HolidayCalendar.java` | yes |
| | `src/main/resources/data/holidays-TX-01-2027.json` (new) | yes |
| | `src/test/java/.../HolidayCalendarTest.java` (new) | yes |
| priorauth-api | `pom.xml` (own version and the aging dependency) | yes |
| | `src/test/java/.../PendingRequestsControllerTest.java` (one method added) | yes |

- priorauth-api has no `src/main` change, as planned.
- `BusinessDaysTest` and `AgeBadgeTest` are untouched.
- The `HolidayCalendar` diff matches the plan: a private resolver field, `????` rather than `*`, `Set.copyOf`, an empty
  set when there are no files, `IllegalStateException` on an `IOException`, and the javadoc updated.
- The code is the smallest complete change. There is no new dependency (`PathMatchingResourcePatternResolver` is in
  spring-core).

## Smaller observations (no change needed)

- **The `????` pattern is correct.** For tenant `TX`, the remainder `01-2026` is 7 characters, so it won't match
  TX-01's files.
- **Not a trust boundary.** `tenantId` now goes into a resource pattern, but it comes from stored request data
  (`r.tenantId()`), not from the caller.
- **Pre-existing, not introduced here:** a file without a `holidays` key throws a `NullPointerException`, not the
  `IllegalStateException`. It is a mention only; it is out of scope.
- **Q1 from the plan is still open and should go to Ravi and Kiran.** A missing year still means no holidays for that
  year, silently. January 2028 will repeat this bug unless a 2028 file is added.

## What I skipped or did not check, and risk

- **I did not run `./scripts/verify.sh` / `scripts\verify.cmd`.** The instruction was not to change anything, and
  verify installs into `~/.m2` and writes `target/`. I rely on `implementation.md`, which reports a pass with
  `verify.cmd` (exit 0) and test counts. It says `verify.sh` could not run under Git Bash because of a Maven launcher
  problem in that environment.
- **The new tests were never seen to fail on the old code.** `implementation.md` says so. My hand count confirms the
  old code gives 63 / 60 / 57, so the tests do discriminate.
- **Not checked:**
  - the Spring Boot fat jar or `spring-boot:run` with the `classpath*:` wildcard (verify exercises only the installed
    library jar)
  - that the 2027 list matches the nightly report's source (plan A1)
  - remotes, open PRs and other consumers of priorauth-aging
