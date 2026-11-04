# priorauth workspace

The team's workspace for the reviewer screen's backend. Two code repos, each a git repo of its own with its own
remote, cloned side by side in this folder (this folder's own git repo ignores them):

| Repo               | What it is                                                                 | Version | Verify with           |
|--------------------|----------------------------------------------------------------------------|---------|-----------------------|
| `priorauth-aging/` | the request-aging library: business days, tenant holiday calendars (`src/main/resources/data/holidays-<tenant>-<year>.json`), the age badge. `com.acmehealth:priorauth-aging` | 1.0.0 | `./scripts/verify.sh` |
| `priorauth-api/`   | the Spring Boot 4.1 API the reviewer screen reads (`GET /requests/pending`); depends on priorauth-aging | 1.2.0 | `./scripts/verify.sh` |

Both are Java 21 and Maven. This folder is an Archon **folder project**: the team's workflows live in
`.archon/workflows/`, requests and bug reports in `docs-in/`. Archon runs here in place: it makes no worktree,
branch or pull request. The workflow and you do the git, in each repo.

## How we work across the two repos

- Tests only through `./scripts/verify.sh` (`scripts\verify.cmd` by hand on Windows): it installs priorauth-aging,
  then tests priorauth-api against it. Never ad hoc.
- Git per repo: in each repo the change touches, branch `fix/<slug>` from `main` (the same name in both), and commit
  there. Never commit code in this workspace folder, never push (the workflow's last node does), never touch a repo
  the plan does not name.
- A change to priorauth-aging ships as a new version of it (patch for a fix that keeps its API, minor for an
  addition, major for a breaking change). priorauth-api depends on that version in the same change, and bumps its own.
- Release order: priorauth-aging's PR is merged first, then priorauth-api's.
- Before proposing a version, check each repo's tags and its `pom.xml`.
- Write what a person must read (scan, plan, review) into `$ARTIFACTS_DIR`, not into a repo.

## How to change code

1. Ask, don't assume. If something is unclear, say so in the plan; state the assumptions you make.
2. Smallest complete change. Prefer what already exists (this codebase, the JDK, an installed dependency) over new
   code; no features, options or abstractions nobody asked for. Deleting beats adding.
3. Surgical. Touch only what the approved plan names and match the surrounding style. Mention unrelated problems,
   don't fix them.
4. Prove it. New branching, parsing, money or security logic gets a test; run the verify script before saying done.
5. Never cut validation at trust boundaries, error handling that prevents data loss, security, accessibility, or
   anything the request asked for.
6. End each summary with what you skipped or did not check, and any risk.
