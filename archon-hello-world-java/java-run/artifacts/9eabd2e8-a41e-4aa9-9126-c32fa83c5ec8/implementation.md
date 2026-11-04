# Implementation: review findings R-1, R-2 (request-age/age-api)

Source: review.md of the adopted run (cd54631b…), with the operator's decisions (Meena): R-1 option (a), R-2 add the test.

## Findings

- **R-1 — fixed.** `PendingRequestsController.pending` now computes `today = LocalDate.now(clock)` once; a parsed
  `asOf` after `today` throws 400 `"asOf <date> is after today <today>"` (new FR8 case) before any age is counted, so
  the day-by-day loop and the missing-holiday-file warning set can no longer be driven by a far-future date.
  `asOf` equal to today stays valid (existing `agesAsOfAGivenDate` uses 2026-10-13 = the pinned clock's today).
  Class search: `asOf`/`LocalDate.parse` on request input exists only in this controller — the one site changed.
  Operations the guard can refuse: only `GET /requests/pending?asOf=…`; tested with tomorrow (`asOfAfterTodayIs400`)
  and `+999999999-12-31` (`farFutureAsOfIs400`). Javadoc updated to say "not after today".
- **R-2 — fixed.** `emptyAsOfIs400` pins `asOf=` → 400 with a detail naming asOf.
- R-3, R-4 were notes outside the operator's request; not acted on (no change, review already records them).

Files: the plan's `PendingRequestsController.java` and `PendingRequestsControllerTest.java` only. No pom.xml change.

## Validation

`./scripts/verify.sh` → exit 0; 24 tests, 0 failures/errors/skips (PendingRequestsControllerTest 10, RequestAgeTest 9,
HolidayCalendarTest 3, RequestStoreTest 2).

## Commits

- `Reject an asOf after today, and pin the empty-asOf 400`

## Skipped / risk

- requirements.md (FR8) is not in the repo; it lives in the earlier run's artifacts and was not edited — the new
  400 case should be added to FR8 there by whoever owns that document.
- "Today" is the server zone's date; a screen in another zone near midnight could send its own "today" and get 400
  (same midnight caveat as A-08). Did not run `scripts\verify.cmd` or the packaged jar.
