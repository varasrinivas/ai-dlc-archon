# java workspace

The team's workspace for the reviewer screen's backend. One code repo, a git repo of its own with its own remote,
cloned into this folder (this folder's own git repo ignores it):

| Repo             | What it is                                                                       | Verify with           | Branch pattern     | PR base |
|------------------|----------------------------------------------------------------------------------|-----------------------|--------------------|---------|
| `priorauth-api/` | the Spring Boot 4.1 REST API on Java 21 (Maven) the reviewer screen reads (`GET /requests/pending`) | `./scripts/verify.sh` | request-age/<slug> | main    |

This folder is an Archon **folder project**: the team's workflows live in `.archon/workflows/`, requests in
`docs-in/`. Archon runs here in place: it makes no worktree, branch or pull request. The workflow and you do the
git, in the code repo.

## How we run Archon here

- One request = one run of `request-to-pr` = one branch in priorauth-api = one PR. Name the request file in the run message.
- Tests only through `./scripts/verify.sh` (`scripts\verify.cmd` by hand on Windows), from this folder; never ad hoc.
- Git in the code repo: branch `request-age/<slug>` from `main` in priorauth-api and commit there. Never commit code
  in this workspace folder, never push (the workflow's last node does).
- Never add a dependency to pom.xml without saying so in the plan.
- Write what a person must read (scan, questions, requirements, plan, review) into `$ARTIFACTS_DIR`, not into a repo.
- Before proposing a version or a tag, check the repo's tags and the version in its pom.xml.

## How to change code

1. Ask, don't assume. If something is unclear, put it in the questions; state the assumptions you make.
2. Smallest complete change. Prefer what already exists (this codebase, the JDK, an installed dependency) over new code; no features, options or abstractions nobody asked for. Deleting beats adding.
3. Surgical. Touch only what the approved plan names and match the surrounding style. Mention unrelated problems, don't fix them.
4. Prove it. New branching, parsing, money or security logic gets a test; run the verify script before saying done.
5. Never cut validation at trust boundaries, error handling that prevents data loss, security, accessibility, or anything the request asked for.
6. End each summary with what you skipped or did not check, and any risk.
