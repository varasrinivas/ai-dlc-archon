# Requirements — request age on the pending list (API)

Request: `docs-in/request.md` (Ravi Menon, 13 Oct). Answers to the questions: Ravi and Meena. Revision 2 adds
Meena's changes: the field names from the screen team, the config key, the holiday file path, and an as-of date
before the received date treated as a caller error.
Scope: `GET /requests/pending` in priorauth-api adds a business-day age, an over-limit flag and a display label to each
row. Nothing else about the endpoint changes.

## Functional requirements

**FR1. New fields on each pending row.** The reviewer-screen team named these fields. Every row returned by
`GET /requests/pending` carries:
- `ageBusinessDays`: JSON integer, ≥ 0
- `overLimit`: JSON boolean
- `ageLabel`: JSON string, for example `"7 bd OVER 5"` (FR5)

The existing fields (`id`, `tenantId`, `service`, `status`, `receivedAt`) and their names, types and values do not change.

**FR2. Counting rule.** `ageBusinessDays` is the number of business days **after** `receivedAt`, up to and
**including** the as-of date. The received day is day 0, so a request received on the as-of date has age 0. This is the
same rule the nightly report uses (answer 2).

**FR3. Business day.** A business day is a Monday to Friday date that is not a holiday of the request's tenant (FR6).
Saturdays, Sundays and that tenant's holidays are never counted.

**FR4. Flag and threshold.** `overLimit` is `true` when `ageBusinessDays` is **strictly greater than** the threshold and
`false` otherwise. The threshold is read from the configuration key **`priorauth.aging.threshold-days`** in
`application.yml`, set to **5** (answer 3).

**FR5. Label.** `ageLabel` is `"<age> bd"`. When `overLimit` is true it becomes `"<age> bd OVER <threshold>"`, for
example `"7 bd OVER 5"` (see A-02 for the case that is not over). The number after `OVER` is the configured threshold.

**FR6. Holidays per tenant.** Holidays come from one JSON file per tenant and year in the API's resources, at
**`data/holidays-<tenantId>-<year>.json`** (`src/main/resources/data/`). For TX-01 that is
`data/holidays-TX-01-2026.json`, which lists exactly these dates:
2026-01-01, 2026-01-19, 2026-02-16, 2026-05-25, 2026-07-03, 2026-09-07, **2026-10-12**, 2026-11-11, 2026-11-26,
2026-11-27, 2026-12-25.
Each request uses the holidays of its own `tenantId`.

**FR7. The as-of date.** By default the as-of date is today in the **server's default time zone** (answer 5).
A caller can pin it with an optional query parameter `asOf` in ISO format (`yyyy-MM-dd`), for example
`GET /requests/pending?asOf=2026-10-13`.

**FR8. Caller errors on `asOf`.** These are input validation, not refusals based on age, and both return **HTTP 400**
with a message that names the problem:
- `asOf` is not a valid `yyyy-MM-dd` date.
- `asOf` is before the `receivedAt` of a request in the pending list. The message names the request (Meena).

**FR9. Informational only.** The API only reports the age, the flag and the label. It never refuses, filters,
re-sorts, alerts or otherwise acts on a request because of them (answer 6). The list keeps today's filter (PENDED and
IN_REVIEW) and order (oldest `receivedAt` first, then `id`).

## Non-functional requirements

**NFR1. No new dependency.** The work uses `java.time` and the Jackson that already comes with Spring Boot. pom.xml is
not changed.

**NFR2. Backward-compatible contract.** The change only adds three fields, plus the new 400 cases for the new `asOf`
parameter. No existing field, path, filter or order changes. A call without `asOf` behaves as before apart from the
added fields.

**NFR3. Deterministic and tested.** The date is injectable (a `Clock`, or `asOf`) so tests do not depend on the day they
run. Tests cover:
- the worked check below
- age 0 on the received day
- a weekend and a holiday
- the boundary: age 5 gives `false` and `"5 bd"`, age 6 gives `true` and `"6 bd OVER 5"`
- `asOf` given and not given
- `asOf` invalid, and `asOf` before a received date, both 400
- a tenant or year with no holiday file (A-03)

They run through `./scripts/verify.sh`.

**NFR4. Untouched files.** `PriorAuthRequest`, `RequestStore`, `requests.sample.json` and `RequestStoreTest` stay
unchanged (their Javadoc says "unchanged by intent 261013-request-age-api"). The age logic lives with the API layer or
in a new small class.

**NFR5. Configuration, not code.** The threshold lives under `priorauth.aging.threshold-days` and the holidays in the
holiday files. Changing either needs no code change (a rebuild is fine, since both are packaged in the jar).

**NFR6. Load once.** Holiday files are read once at startup, not on every request. A holiday file that is present but
cannot be parsed stops startup with a clear error, instead of silently ageing requests wrongly.

## Assumptions (please correct any that are wrong)

- **A-01. File format.** Each holiday file is a JSON array of ISO dates: `["2026-01-01", ...]`. Every date in
  `holidays-<tenant>-<year>.json` belongs to `<year>`.
- **A-02. Label when not over.** Only the over case was given (`"7 bd OVER 5"`). When the request is not over the
  limit, the label is `"<age> bd"` (`"4 bd"`, `"0 bd"`), with no suffix. The unit is always `bd`, with no singular
  form (`"1 bd"`). **The screen team should confirm.**
- **A-03. Missing holiday file.** A count can need a tenant or year that has no file: another tenant, or 2027 once
  requests age into January. Weekends are still excluded, that year counts as having no holidays, and a warning
  naming the missing file is logged. The request is not refused (FR9). Today only `holidays-TX-01-2026.json`
  exists, so the 2027 file is needed before 2027-01-01.
- **A-04. `asOf` before a received date fails the whole list.** The endpoint returns one list, so any pending row
  received after `asOf` makes the whole call return 400, not just that row. On the sample data, any `asOf` before
  2026-10-09 (PA-10263's received date) is rejected.
- **A-05. Future received date without `asOf`.** If the server's own today is before a row's `receivedAt` (bad data or
  clock skew), the caller made no mistake, so the call does not fail. That row gets age 0, `overLimit` false and label
  `"0 bd"`, and a warning is logged. **Please confirm**, or say whether this should also be an error.
- **A-06. Received on a non-business day.** The rule still counts business days *after* the received date. A request
  received on a Saturday has age 1 on the following Monday (if Monday is not a holiday).
- **A-07. Holiday list ownership.** The TX-01 list is a copy of the report's dates as given by Ravi and Meena, kept in
  this repo "for now". It can drift from the report's list. A shared calendar service is separate work and out of
  scope (answer 6).
- **A-08. Server time zone.** The deployed server's default zone is assumed to be the business zone (US Central for
  TX-01). If it runs on UTC, the age turns over at about 19:00 Central. Callers who need a fixed date pass `asOf`
  (answer 5).
- **A-09. Sample data location.** The holiday file sits next to `data/requests.sample.json` in the same `data/`
  resource folder. Adding it does not change the request sample.

## Worked check on the sample data, as of Tue 2026-10-13

Holidays in that window: Mon 2026-10-12 (TX-01). Threshold: 5, strictly greater.

| id       | status    | receivedAt     | business days counted (after receipt, through 10-13)            | ageBusinessDays | overLimit | ageLabel        | in list? |
|----------|-----------|----------------|-----------------------------------------------------------------|-----------------|-----------|-----------------|----------|
| PA-10231 | PENDED    | Thu 2026-10-01 | 10-02, 10-05, 10-06, 10-07, 10-08, 10-09, 10-13 (10-12 holiday) | **7**           | **true**  | `"7 bd OVER 5"` | yes      |
| PA-10244 | IN_REVIEW | Tue 2026-10-06 | 10-07, 10-08, 10-09, 10-13 (10-12 holiday)                      | **4**           | **false** | `"4 bd"`        | yes      |
| PA-10250 | APPROVED  | Wed 2026-10-07 | n/a, not pending                                                | n/a             | n/a       | n/a             | no       |
| PA-10263 | PENDED    | Fri 2026-10-09 | 10-13 (10-10/11 weekend, 10-12 holiday)                         | **1**           | **false** | `"1 bd"`        | yes      |

**Expected for `GET /requests/pending?asOf=2026-10-13`:** 3 rows in the order PA-10231, PA-10244, PA-10263.

| Request  | ageBusinessDays | overLimit | ageLabel        |
|----------|-----------------|-----------|-----------------|
| PA-10231 | 7               | true      | `"7 bd OVER 5"` |
| PA-10244 | 4               | false     | `"4 bd"`        |
| PA-10263 | 1               | false     | `"1 bd"`        |

The labels for the rows that are not over follow A-02. Without the 10-12 holiday the ages would be 8, 5 and 2, and the
flags would be the same.

**Caller-error checks:**
- `?asOf=2026-10-08` returns 400, because PA-10263 was received 2026-10-09.
- `?asOf=13-10-2026` returns 400, because the date is invalid.

## Out of scope
- A shared holiday or calendar service, or reading the report's source at runtime.
- Holiday files for years other than 2026, or for tenants other than TX-01.
- Any change to the reviewer screen, the nightly report, or the request model and store.
- A release version or tag. Check `git tag` and the pom version (1.0.2) at plan time.
