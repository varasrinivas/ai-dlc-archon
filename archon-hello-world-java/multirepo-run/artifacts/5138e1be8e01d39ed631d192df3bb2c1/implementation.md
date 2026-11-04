# Implementation: New Year's Day counted as a working day (docs-in/bug-report.md, Ravi Menon, 17 Oct 2026)

Plan: `plan.md`, approved by Meena Iyer with one correction (applied, see below).

## priorauth-aging (1.0.0 → 1.0.1)

- **Branch:** `fix/holidays-across-years` (from `main`)
- **Commit:** `074d5244f7c9d1768e334b26e6c6e3e895f8c724`
- **Files changed**
  - `src/main/resources/data/holidays-TX-01-2027.json`: new, copied byte-for-byte from `docs-in/holidays-TX-01-2027.json` (11 dates).
  - `src/main/java/com/acmehealth/priorauth/aging/HolidayCalendar.java`: `load()` resolves
    `classpath*:data/holidays-<tenant>-????.json` with a private `PathMatchingResourcePatternResolver` and returns the
    union of all files' dates. No files → empty set; `IOException` → `IllegalStateException` as before. Javadoc says
    "one JSON file per tenant per year". Constructor and `forTenant` signature unchanged.
  - `pom.xml`: version `1.0.1`.
- **Tests added:** `HolidayCalendarTest` — `loadsEveryYearForTheTenant` (22 dates incl. 2026-01-01, 2026-10-12, 2027-01-01),
  `tenantWithoutFilesHasNoHolidays`, `ageAcrossTheYearSkipsNewYearsDay` (1 Oct 2026 → 5 Jan 2027 = 62).

## priorauth-api (1.2.0 → 1.2.1)

- **Branch:** `fix/holidays-across-years` (from `main`)
- **Commit:** `8d65a37f113d2a075e8f6ae2acefe355d9ebfac6`
- **Files changed**
  - `pom.xml`: version `1.2.1`; `priorauth-aging` dependency `1.0.1`.
  - No change to `src/main`.
- **Tests added:** `PendingRequestsControllerTest.newYearsDayIsNotABusinessDay` — `GET /requests/pending?asOf=2027-01-05`:
  PA-10231 62 (`62 bd OVER 5`), PA-10244 **59**, PA-10263 **56**.

### Correction to the plan's expected ages

The plan expected 62 / 60 / 57. Meena's correction (62 / 59 / 56; today 63 / 60 / 57) is right: 1 Jan 2027 lies in all
three periods. I re-counted independently from the two holiday files before writing the test (weekdays after the
received date up to and including 5 Jan, minus TX-01 holidays): 62 / 59 / 56 with the fix, 63 / 60 / 57 with only the
2026 file. The test uses 62 / 59 / 56.

## Verify

`scripts\verify.cmd` from the workspace root: **PASS** (exit 0).
- priorauth-aging: AgeBadgeTest 1, BusinessDaysTest 4, HolidayCalendarTest 3 — all pass; 1.0.1 installed to `~/.m2`.
- priorauth-api against aging 1.0.1: PendingRequestsControllerTest 4, RequestStoreTest 2 — all pass.
- The installed `priorauth-aging-1.0.1.jar` contains `data/holidays-TX-01-2026.json` and `data/holidays-TX-01-2027.json`.

`./scripts/verify.sh` (Git Bash) did not run on this machine: Git Bash's `mvn` launcher fails with
`ClassNotFoundException: org.codehaus.plexus.classworlds.launcher.Launcher` before any build starts — an environment
problem with the shell's Maven wrapper, not the code. I used the Windows twin `verify.cmd`, which CLAUDE.md names for
Windows and which runs the same two steps.

## Skipped / not checked / risk

- **Not seen red:** I did not run the new tests against the old code first. The hand count (63 without 2027) and the
  old `load()` reading only `-2026.json` make the failure clear, but it was not observed.
- **Not checked:** the Spring Boot fat jar / `mvn spring-boot:run` (Kiran checks the packaged jar by hand before push).
  Verify does exercise `classpath*:` + wildcard against the installed library jar.
- **Left as is (per Meena):** a tenant with no file for a year still silently gets no holidays for that year (Jan 2028
  will repeat this bug without a 2028 file).
- **Not checked:** that the 2027 list matches the nightly report's source (plan A1); that a file's `tenantId` matches
  its name; remotes, open PRs, other consumers of priorauth-aging.
- Nothing pushed, nothing committed in the workspace folder. Git warned the new test file will be stored with LF→CRLF
  conversion per local autocrlf settings; content is unaffected.
