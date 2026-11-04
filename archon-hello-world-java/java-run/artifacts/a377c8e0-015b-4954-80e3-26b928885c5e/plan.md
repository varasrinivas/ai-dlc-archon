# Plan: request age on the pending list (API), docs-in/request.md

## Problem

Ravi Menon (UM Nurse Manager) asks that `GET /requests/pending` in priorauth-api return the same business-day age
and over-5 flag as the nightly report, so the reviewer screen can show them. Weekends and the tenant's holidays do
not count. Nothing else is to change.

## Finding: priorauth-api `main` already delivers this

I checked this against the code in this session, not against the request text:

- `priorauth-api` `main` = `origin/main` = `4ca6b6a` "Merge request-age/pending-age: request age on the pending list",
  merged 2026-11-04 18:00 +0530 by Meena Iyer. It contains `a3972b4` "Pending list: business-day age, over-limit flag
  and label (asOf)" and `4ea9e9d` "Pending list: asOf after today is a 400". Its working tree is clean.
- `PendingRequestResponse` (record) keeps every field it had at `d9aa178` (`id, tenantId, service, status,
  receivedAt`) and adds `ageBusinessDays` (int), `overLimit` (boolean) and `ageLabel` (String, e.g. `"7 bd OVER 5"`).
- `RequestAging.ageBusinessDays(tenantId, receivedAt, asOf)` counts the days d with receivedAt < d <= asOf that are
  not Saturday, Sunday, or a holiday from `data/holidays-<tenant>-<yyyy>.json`.
  `overLimit(age)` is `age > priorauth.aging.threshold-days`, and `application.yml` sets that to `5`. This is the
  "over 5" flag.
- `PendingRequestsController.pending` computes the age as of today from an injected `Clock`, or as of an optional
  `asOf` query parameter. It returns 400 when `asOf` is after today, before any pending row's `receivedAt`, or
  malformed.
- I checked the worked example by hand against the TX-01 2026 calendar (2026-10-12 is a holiday), as of Tue
  2026-10-13:
  - PA-10231 (received Thu 10-01) = 7, over the limit.
  - PA-10244 (received 10-06) = 4.
  - PA-10263 (received 10-09) = 1.

  `PendingRequestsControllerTest.agesAsOfWorkedCheck` asserts exactly these values.
- `./scripts/verify.sh` (run from the workspace this session): exit 0, and all of `RequestAgingTest`,
  `PendingRequestsControllerTest` and `RequestStoreTest` pass.

The request was written on 13 Oct, before this merge, and the merge landed just before this run. The code that
asked for it is now on `main`.

## Approach

**Decision: make no code change.** The implementer creates no `request-age/<slug>` branch and no commit, and pushes
nothing. The workflow's `push` node already prints "nothing to push" when `main..HEAD` is empty.

- **What settled it:** the code above and the passing verify run.
  - CLAUDE.md "How to change code" 2: *"Smallest complete change … Deleting beats adding."*
  - CLAUDE.md "How to change code" 3: *"Touch only what the approved plan names."*
- **Strongest alternative, rejected:** re-implement or "polish" the feature on a new branch, for example by
  renaming fields or adding a top-level `asOf` to the response. That would change a contract that has just shipped,
  for no stated need, and the request says "Nothing else changes."
- **Second alternative, rejected:** a branch that only bumps the version (1.0.2 → 1.0.3) so the screen picks up a
  release. Nobody asked for a version or tag. The repo has no tags (`git ls-remote --tags origin` returns nothing),
  and `pom.xml` is `<version>1.0.2</version>`, the same as before the feature. Release practice is not stated
  anywhere, so I raise it as a non-blocking question below.

## Steps

1. In `priorauth-api`, confirm `git rev-parse HEAD origin/main` both print `4ca6b6a…` and that
   `git status --short` is empty. If `main` has moved, re-read `PendingRequestResponse` and confirm that
   `ageBusinessDays` and `overLimit` are still present before continuing.
2. From the workspace root, run `./scripts/verify.sh` (or `scripts\verify.cmd` on Windows). It must exit 0. Expected:
   `PendingRequestsControllerTest.agesAsOfWorkedCheck` asserts 7/4/1, `true/false/false`, and
   `"7 bd OVER 5"/"4 bd"/"1 bd"`.
3. Create no branch and no commit. Leave `main` checked out. The `push` node then reports "nothing to push".
4. In the run's summary for the operator, state the following:
   - the request is already satisfied by `4ca6b6a` on `main`;
   - the JSON fields the screen should read are `ageBusinessDays`, `overLimit` and `ageLabel`;
   - the operator checks below remain.

## Contract coverage

| Request item | Delivered by (already on main) | Step that confirms it |
|---|---|---|
| Pending list carries business-day age | `PendingRequestResponse.ageBusinessDays`, `RequestAging.ageBusinessDays` | 1, 2 |
| Carries the over-5 flag | `PendingRequestResponse.overLimit`, `RequestAging.overLimit`, `threshold-days: 5` | 1, 2 |
| Weekends and our holidays do not count | `RequestAging.ageBusinessDays` filters on SAT/SUN and the tenant calendar; tested in `RequestAgingTest` and the worked check | 2 |
| Same rule as the nightly report | The worked check matches the business-day rule. The report's own code is not in this workspace, so parity is an operator check (below) | 4 |
| Nothing else changes | The existing fields are unchanged and in the same order. The list is still pending-only and oldest first (`listsPendingRequestsOldestFirst`) | 2, 3 (no new change) |
| CLAUDE.md: tests only via verify script; no pom dependency; no push from the agent | Nothing is added; only verify is run | 2, 3 |

## Validation

Validation is `./scripts/verify.sh`. I add no new tests, because no code changes.

Operator checks, for the run summary or PR body. These are outside this repo, or need a live environment:

- **Report parity:** compare the nightly report's AGE for the same rows with this API's `ageBusinessDays`, for the
  same as-of day. In particular, check that the received day is excluded and the as-of day is counted.
- **Deployment:** "The reviewer screen still shows nothing" can only change once a build containing `4ca6b6a` is
  deployed, and once the screen reads `ageBusinessDays`, `overLimit` and `ageLabel`. Both are outside priorauth-api.

## Risks and rollback

There is no new risk from this run, because it changes nothing. These risks belong to the merged feature, for
awareness:

- `Clock.systemDefaultZone()` makes "today" the server's zone, so near midnight the date can differ from the TX-01
  business day.
- Holidays exist only for 2026; see `discoveries/plan.json`.

Rollback of the feature itself, if it were ever needed, is `git revert -m 1 4ca6b6a` in priorauth-api. This run does
not do that.

## Out of scope

- No change to field names or shapes, the `asOf` behaviour, the threshold, or the holiday data.
- No version bump or tag, and no front-end (reviewer screen) work.
- No 2027 holiday calendar. That is a discovery, not this request, and the dates are a business decision.

## Open questions (non-blocking)

1. **Release a version for the screen?** `pom.xml` is still 1.0.2 and the repo has no tags, although the response
   gained three fields.
   - Options:
     - (A) leave it to the team's release process (my choice; it costs nothing now);
     - (B) bump to 1.0.3 in a follow-up request.
   - Why non-blocking: none of the person-call conditions holds, because nothing in the request asks for a release.
   - Line for the direction doc: "A response-field addition to priorauth-api bumps the patch version in the same PR,
     or: versions are bumped only at release."
