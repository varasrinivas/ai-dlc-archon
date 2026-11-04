# priorauth-api

The API the reviewer screen reads: `GET /requests/pending` returns the requests a reviewer still has to act on, oldest first.
Spring Boot 4.1, Java 21, Maven. No database in this cut: the nightly export is packed into the jar.

```
mvn test                 # the tests
mvn spring-boot:run      # then: curl http://localhost:8080/requests/pending
```
