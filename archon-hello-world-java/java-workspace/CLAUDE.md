# priorauth-api

A Spring Boot 4.1 REST API on Java 21, built with Maven. It serves the pending list the reviewer screen reads.
Work on it is run through Archon: the team's workflows live in `.archon/workflows/`, requests in `docs-in/`.

| Owns                              | Verify with              | Branch pattern     | PR base |
|-----------------------------------|--------------------------|--------------------|---------|
| the API the reviewer screen reads | `./scripts/verify.sh`    | request-age/<slug> | main    |

## How we run Archon here

- One request = one run of `request-to-pr` = one branch = one PR. Name the request file in the run message.
- Tests only through `./scripts/verify.sh` (`scripts\verify.cmd` by hand on Windows); never ad hoc.
- Never add a dependency to pom.xml without saying so in the plan.
- Write what a person must read (scan, questions, requirements, plan, review) into `$ARTIFACTS_DIR`, not into the repo.
- Commit the code on the run's branch when the checks pass; pushing is the workflow's last node, opening the PR is ours.
- Before proposing a version or a tag, check the existing tags and the version in pom.xml.

## How to change code

1. Ask, don't assume. If something is unclear, put it in the questions; state the assumptions you make.
2. Smallest complete change. Prefer what already exists (this codebase, the JDK, an installed dependency) over new code; no features, options or abstractions nobody asked for. Deleting beats adding.
3. Surgical. Touch only what the approved plan names and match the surrounding style. Mention unrelated problems, don't fix them.
4. Prove it. New branching, parsing, money or security logic gets a test; run the verify script before saying done.
5. Never cut validation at trust boundaries, error handling that prevents data loss, security, accessibility, or anything the request asked for.
6. End each summary with what you skipped or did not check, and any risk.
