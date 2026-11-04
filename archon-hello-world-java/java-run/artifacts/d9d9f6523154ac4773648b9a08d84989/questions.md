# Questions before requirements: request age on the pending list (API)

The request asks for "the same rule as the report", but the nightly report's code is not in this workspace. A
person who knows the report, or can see it, needs to answer these.

1. **Where do "our holidays" come from?**
   - A. Copy the report's holiday list into this repo as a data file (`src/main/resources/data/holidays.json`).
   - B. Put it in `application.yml` as a list of dates.
   - C. Read the same file or source the report reads, shared with it.
   - X. Other.
   - **Pick: A, unless C is cheap.** It is one source of truth inside this repo, needs no new dependency, and works
     the way the requests export already does. C avoids the two lists drifting apart, but nothing shared exists here.
     Please send the actual dates (2026 at least, plus 2027 if the list exists) and say whether the list differs
     by tenant.

2. **How does the report count age?**
   - A. Business days after the received day, up to and including today. Received Friday, seen Monday = 1.
   - B. Both the received day and today count. Received Friday, seen Monday = 2.
   - C. Business days strictly between the two dates; neither end counts.
   - X. Other: send the report's formula or two worked examples.
   - **Pick: A.** It is the usual "days waiting" count, and same-day requests come out as 0. It must match the report
     exactly, so please confirm it against one real row in the report.

3. **What if a request arrived on a weekend or a holiday?**
   - A. Its age starts counting on the next business day.
   - B. Treat it as if it arrived on the previous business day.
   - X. Other / whatever the report does.
   - **Pick: A.** It follows from the 2A rule with no special case.

4. **What does "over 5" mean?**
   - A. Age greater than 5 (6 or more).
   - B. Age 5 or more.
   - X. Other.
   - **Pick: A.** "Over 5" reads as greater than 5. Please confirm against the report, because this edge is exactly
     where the screen and the report would disagree.

5. **Which date is "today"?**
   - A. Today's date on the server clock, in one fixed zone. Which zone? (e.g. `America/Chicago` for TX-01)
   - B. Today in each tenant's own zone.
   - C. The date of the nightly export the data came from, as the report does.
   - X. Other.
   - **Pick: A, with the zone set in `application.yml`.** It is simple and testable with a JDK `Clock`, and right now
     there is one tenant. Pick C if the screen must show exactly the report's numbers for the same day.

6. **What are the JSON field names the reviewer screen will read?**
   - A. `ageBusinessDays` (number) and `overFiveBusinessDays` (boolean).
   - B. `age` and `overdue`, matching the report's AGE column.
   - C. Whatever the screen team has already coded against: please send it.
   - X. Other.
   - **Pick: C if they exist, otherwise A.** Names are a contract with the screen, and A says what the values mean.

7. **Should the API version change?**
   - A. 1.0.3. Fields are added, existing ones are untouched.
   - B. 1.1.0. It is a new capability in the response.
   - C. Leave it at 1.0.2.
   - X. Other.
   - **Pick: B.** Adding response fields is a backward-compatible feature, which is a minor bump under semver.
     Today the pom says 1.0.2 and the repo has no tags.
