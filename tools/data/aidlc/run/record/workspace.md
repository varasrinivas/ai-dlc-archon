# Workspace Detection (AI-DLC stage 0.2)

Workspace: `C:\work\archon-aidlc\aidlc-workspace` (an Archon folder project; its own git repo, `main`, one commit `849abac`, clean).
Nothing was changed.

## Verdict

- **Greenfield: no.** There is application code (brownfield).
- **CI/CD pipeline: none.** No `.github/workflows`, Jenkinsfile, GitLab/Azure pipeline or similar in any repo. The only YAML in the code repo is `src/main/resources/application.yml` (Spring config). The `.archon/workflows/*.yaml` files are Archon agent workflows, not CI/CD.

## Repos

| Repo | Remote | Branch / HEAD | Tags | Version |
|------|--------|---------------|------|---------|
| `priorauth-api/` | https://github.com/varasrinivas/aidlc-priorauth-api | `main` @ `d9aa178` "priorauth-api 1.0.2: pending list for the reviewer screen", clean | none | `1.0.2` (pom.xml) |

The workspace repo ignores `/priorauth-api/` (separate clone).

### priorauth-api

- Spring Boot 4.1.1 (parent `spring-boot-starter-parent`), Java 21, Maven. groupId `com.acmehealth`.
- Dependencies: `spring-boot-starter-webmvc`; test: `spring-boot-starter-webmvc-test` (JUnit 5, AssertJ, MockMvc). Plugin: `spring-boot-maven-plugin`.
- No database: data is a JSON export packed in the jar (`src/main/resources/data/requests.sample.json`).
- Code (`com.acmehealth.priorauth`): `PriorAuthApiApplication`, `api/PendingRequestsController` (`GET /requests/pending`, oldest first), `api/PendingRequestResponse`, `model/PriorAuthRequest`, `store/RequestStore`.
- Tests: `api/PendingRequestsControllerTest`, `store/RequestStoreTest`.
- No Maven wrapper (`mvnw`); uses system Maven (3.9.16 found on PATH) and JDK 21.0.10 (Temurin).

## Build and test

- Verify (the only sanctioned way): `./scripts/verify.sh` from the workspace (`cd priorauth-api && mvn -q test`); Windows twin `scripts\verify.cmd`.
- Build: `mvn package` (runnable jar); run: `mvn spring-boot:run` → http://localhost:8080/requests/pending.

## Other workspace contents

- `.archon/config.yaml`; workflows `team/request-to-pr` (commands `scan.md`, `implement.md`) and `aidlc/aidlc-on-archon` (+ `scripts/state-init.ts`).
- `docs-in/request.md` (the incoming request).
- Branch pattern for work: `request-age/<slug>` from `main`, PR base `main`.

## Not checked

- Did not run the tests or build (change nothing); test pass state unknown.
- Did not read the request, workflow files or source bodies in detail.
- `priorauth-api/target/` exists (ignored build output) — stale or not, not inspected.
