# Implementation: asOf after today is a 400

## What changed
- `priorauth-api/src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java`: today is read once from the
  injected `Clock`. A non-null `asOf` after today is rejected with 400 (`ResponseStatusException`, reason
  "asOf <asOf> is after today <today>"), checked before the existing asOf-before-receivedAt 400. A missing or empty asOf
  still defaults to today.
- `PendingRequestsControllerTest`: added `asOfAfterTodayIs400` (2026-10-14 when today is the fixed 2026-10-13, and
  `+999999999-12-31`, which used to be a 500 from the overflow in `RequestAging.ageBusinessDays` at `asOf.plusDays(1)`)
  and `emptyAsOfIsToday` (`asOf=` returns today's ages 7/4/1).

## Deviations
- None. FR11 itself isn't in the repo or this run's artifacts, so I went by the operator's statement of it
  ("caller error, 400").

## Validation
- With the controller fix stashed, `bash ./scripts/verify.sh` failed: `asOfAfterTodayIs400:104 Status expected:<400> but was:<200>`.
  `emptyAsOfIsToday` passed already, because it pins down behaviour that was already correct.
- With the fix at HEAD `4ea9e9d` on a clean tree, `bash ./scripts/verify.sh` exits 0 (21 tests, 0 failures).

## Commits (priorauth-api, branch request-age/pending-age, not pushed)
- `4ea9e9d` Pending list: asOf after today is a 400

## Not checked / risk
- "Today" comes from the application `Clock` (UTC in tests; the zone in production is whatever the `Clock` bean uses).
  Near midnight, a caller in a different zone could see their own "today" rejected as future. I didn't check the
  production Clock bean's zone.
- The project defines no separate lint or format command, so none was run.
