---
description: Implement the approved plan in priorauth-api; one pass of the implement loop.
---
The request: $USER_MESSAGE

Implement the approved plan in $ARTIFACTS_DIR/plan.md against $ARTIFACTS_DIR/requirements.md,
following CLAUDE.md. Notes from the person who approved the plan: $approve-plan.output.text

If an earlier pass ran, this is what it reported (fix what it left failing):
$LOOP_PREV_OUTPUT

In priorauth-api: switch to the branch request-age/<slug> named in CLAUDE.md's pattern (create it
from main if it does not exist yet), make the change, and commit it there with a message that names
the request and the requirement IDs. Do not commit in the workspace folder and do not push.

Run ./scripts/verify.sh from the workspace root. Write $ARTIFACTS_DIR/implementation.md: the branch,
the files changed, the tests added, the commit, the verify result, and what you skipped or did not
check. Return the verify result and the commit hash.
