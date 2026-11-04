# Questions — request age on the pending list (API)

1. **Which holidays, and where do they come from?** The repo has no holiday list. "Our holidays" is defined wherever the nightly report gets them.
   - A. Copy the report's list of dates into `application.yml` (`priorauth.holidays: [2026-01-01, ...]`). Please paste the dates and the years they cover.
   - B. Read the same file or table the report reads at runtime. Please say where it is.
   - C. Compute US federal holidays in code.
   - X. Other.
   - **Pick A**: it's the smallest change and needs no new dependency or data source. It's correct only if the dates match the report, so please also confirm whether **Mon 2026-10-12** is a holiday. It changes the sample answers.

2. **How is age counted?** (the report's exact rule)
   - A. Business days after the received date, up to and including today. The received day doesn't count, so a request received today is 0.
   - B. Business days from the received date through today, both included, so a request received today is 1.
   - C. Business days from the received date up to but not including today.
   - X. Other, or "match the report's code at <location>".
   - **Pick A**: it's the usual "days waiting" count and gives 0 on the day of arrival. Please confirm it matches the report. On 2026-10-13, PA-10244 (received Tue 10-06) is 5 under A and 6 under B, without the 10-12 holiday.

3. **What does "over 5" mean?**
   - A. Strictly more than 5 business days (`age > 5`).
   - B. 5 or more (`age >= 5`).
   - X. Other threshold.
   - **Pick A**: "over 5" reads as strictly greater. This decides PA-10244's flag in the sample.

4. **What should the JSON fields be called, and what types?** The screen team has to read them.
   - A. `ageBusinessDays` (integer) and `overFiveBusinessDays` (boolean).
   - B. The same names the nightly report uses, e.g. `age` and `over5`. Please give them.
   - C. Names the reviewer-screen team specifies.
   - X. Other.
   - **Pick B** if the report's names are known, since the request asks for "the same" age and flag. Otherwise A.

5. **Which date is "today"?**
   - A. The date in a fixed business time zone, e.g. `America/Chicago` for tenant TX-01. Please name the zone.
   - B. The server's default time zone.
   - C. UTC.
   - X. Other.
   - **Pick A**: a server running on UTC turns to tomorrow during the US evening and would age requests early. Tests will pin the date with an injected `Clock` either way.

6. **Is the rule the same for every tenant?** The sample only has TX-01.
   - A. One holiday list and one threshold for all tenants.
   - B. A holiday list per tenant.
   - X. Other.
   - **Pick A**: the request says "our holidays", and nothing suggests per-tenant rules. Per-tenant lists would add configuration nobody asked for.
