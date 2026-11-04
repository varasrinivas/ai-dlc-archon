**#priorauth-reviewers** · Ravi Menon (nurse manager) · Sat 17 Oct 2026, 09:40

Kiran, the new age badge is great, but I think it breaks in January. Payer ops just sent the 2027 holiday list for TX-01 (attached as `holidays-TX-01-2027.json`), so I tried the screen with a January date: `GET /requests/pending?asOf=2027-01-05`.

PA-10231 (received 1 Oct) shows an age one higher than the nightly report gives for the same day, and so do the other pending ones. It looks like New Year's Day is being counted as a working day. The nightly report is right; the screen should match it.

Can this be fixed before the year turns? Same rules as before: weekends and the tenant's holidays don't count.
