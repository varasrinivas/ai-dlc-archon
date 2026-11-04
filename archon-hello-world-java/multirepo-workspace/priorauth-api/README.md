# priorauth-api

The API the reviewer screen reads: `GET /requests/pending` returns the requests a reviewer still has to act on, oldest first,
each with its age in business days and an over-limit flag (`?asOf=YYYY-MM-DD` to pin the date; default today).
An `asOf` before a request's received date is the caller's error: 400.
Spring Boot 4.1, Java 21, Maven. No database in this cut: the nightly export is packed into the jar.

```
mvn test                 # the tests
mvn spring-boot:run      # then: curl "http://localhost:8080/requests/pending?asOf=2026-10-13"
```

Changed by AI-DLC intent `261013-request-age-api` (see `../aidlc/spaces/default/intents/261013-request-age-api/`).
