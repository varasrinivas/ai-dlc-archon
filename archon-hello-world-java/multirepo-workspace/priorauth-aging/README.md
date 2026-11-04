# priorauth-aging

Request aging for the prior-auth reviewer screen, as a library: `BusinessDays` (business days between two dates),
`HolidayCalendar` (a tenant's holidays, from `src/main/resources/data/holidays-<tenant>-<year>.json`) and `AgeBadge`
(the age and the over-limit flag). `priorauth-api` depends on it (`com.acmehealth:priorauth-aging`).

Build and install it locally before building the API: `mvn -q install`.
Split out of priorauth-api 1.1.0 (the `aging` package and its tests, unchanged).
