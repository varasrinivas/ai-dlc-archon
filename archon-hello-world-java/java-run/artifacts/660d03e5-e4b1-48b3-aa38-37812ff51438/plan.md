# Plan: request age on the pending list (priorauth-api). BLOCKED on open questions

Request: `docs-in/request.md` (Ravi Menon, 13 Oct). Make `GET /requests/pending` carry each row's business-day
age and the over-5 flag, "same rule as the report: weekends and our holidays do not count. Nothing else changes."

This plan stops at the open questions, as the planning rules require: the age rule and the holiday dates are
data the request points to ("same rule as the report", "our holidays") but neither this repo nor any project
document contains them. The full design is not written; below is what I checked and what the design will be once
the questions are answered.

## What I verified this session (main @ 83f027e, tree clean)

- `PendingRequestsController.pending()` maps `RequestStore.pending()` through `PendingRequestResponse::from`.
  No parameters. `PendingRequestResponse` is a record `(id, tenantId, service, status, receivedAt)`.
- `PriorAuthRequest` has `tenantId` and `receivedAt` (`LocalDate`). `isPending()` covers PENDED and IN_REVIEW.
- Sample data (`data/requests.sample.json`): pending rows are PA-10231 (rcvd 2026-10-01), PA-10244 (10-06),
  PA-10263 (10-09), all tenant TX-01.
- The repo has **no** holiday data, no business-day code, no clock bean, and no `priorauth.*` configuration.
  It has no `architecture.md`, `engineering.md` or direction document, and no `.archon/sdlc/policy/rulings.md`.
  The pack's default `rulings.md` records no rulings.
- The nightly report whose rule this must match is not in this repo. I found nothing in the workspace that is
  clearly its source.
- `pom.xml` is version 1.0.2 with no tags. JDK `java.time` covers the date arithmetic, so no new dependency is
  needed.
- **Earlier attempt on this same request:** `request-age/age-api` (local and `origin`, commits f3a465d and
  d6288f5, unmerged) already implements it. That attempt also adds things the request did not ask for: an
  `?asOf=` parameter with 400 handling, an `ageLabel` field (`"7 bd OVER 5"`), a configurable
  `priorauth.aging.threshold-days`, a `Clock` bean, and a `ProblemDetail` exception handler. Its rule is: count
  business days *after* `receivedAt` up to and including today; Mon–Fri only; skip the tenant's holidays from
  `data/holidays-<tenant>-<year>.json`; a missing file means weekends only, with a warning; over-limit means age
  > 5. Its TX-01 2026 holidays are 01-01, 01-19, 02-16, 05-25, 07-03, 09-07, 10-12, 11-11, 11-26, 11-27, 12-25.
  The run artifacts that recorded where those answers came from are not available to this run, so I cannot
  confirm the attempt matches the report.

## Open questions (Q1 blocks)

**Q1. What is the report's age rule, and where do "our holidays" come from? (blocks)**
Four facts are open: whether the received day counts, whether "over 5" means > 5 or >= 5, which dates are
holidays and for which tenants, and what to do for a tenant or year with no holiday data.
- A: Adopt the rule and the TX-01 2026 holiday list on `request-age/age-api` (listed above), once someone
  confirms they match the nightly report. Cost: the API keeps its own copy of the calendar, which can drift from
  the report's copy.
- B: Point the API at the report's own holiday source so both read the same data. Cost: depends on that source,
  and could add a dependency or a runtime read that the plan would have to name.
- X: Other.

This is a person's call because no project document covers the rule or the dates, and neither the code nor a
spike can settle them: they are business data held outside this repo. Guessing would ship a flag that disagrees
with the report, which is the outcome the request exists to avoid.
Line for the direction document: "Request age = business days after receivedAt through today (server zone),
Mon–Fri minus the tenant's holidays from <source>; overLimit when age > 5; no holiday data means weekends only."

**Q2. How does this run relate to the unmerged `request-age/age-api` branch? (does not block)**
CLAUDE.md says one request = one run = one branch = one PR, and that branch already exists for this request.
My choice, which is cheap to reverse: deliver only what the request names. That means adding two fields to each
row, `ageBusinessDays` (int) and `overLimit` (boolean), with "today" taken from an injected `Clock`. It means no
`asOf`, no `ageLabel` and no configurable threshold, because the request says "Nothing else changes" and
CLAUDE.md says no options nobody asked for. Ship it as a new commit set on a fresh `request-age/<slug>` branch
cut from main, and treat the earlier branch as superseded.
- Alternative: review and merge the existing branch as is. Cost: it ships the extra `asOf`/`ageLabel` surface.

This meets none of the blocking conditions: nothing on that branch is shipped. The owner should still see it.
Line for the direction document: "A re-run of a request whose branch exists replaces that branch unless the run
message says to build on it."

## Design once Q1 is answered (direction only, not final)

- A new `RequestAge` component (package `api`) that counts business days from `receivedAt` to today, using
  `java.time` and the holiday set Q1 settles.
- Add `ageBusinessDays` and `overLimit` to the `PendingRequestResponse` record and its `from(...)`.
  `PendingRequestsController` passes in today from a `Clock` bean so tests can pin 2026-10-13.
- Tests: a unit test for the counting rule covering the weekend, a holiday, the received day, and the
  threshold boundary at 5 and 6. Extend `PendingRequestsControllerTest` with the sample worked as of
  2026-10-13. Verify with `./scripts/verify.sh`. No change to `pom.xml`.

**Contract addition (for the PR body):** the pending-list JSON gains two fields. Every existing field keeps its
name, type and meaning, and the order and filter do not change.

## What I skipped or did not check

I did not see the nightly report's code or data. I did not read the earlier run's questions or requirements
artifacts, because they are not present. I did not run the earlier branch's tests.
