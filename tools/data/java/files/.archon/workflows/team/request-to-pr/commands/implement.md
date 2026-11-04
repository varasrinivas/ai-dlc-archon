---
description: Implement the approved plan; one pass of the implement loop.
---
The request: $USER_MESSAGE

Implement the approved plan in $ARTIFACTS_DIR/plan.md against $ARTIFACTS_DIR/requirements.md,
following CLAUDE.md. Notes from the person who approved the plan: $approve-plan.output.text

If an earlier pass ran, this is what it reported (fix what it left failing):
$LOOP_PREV_OUTPUT

Run ./scripts/verify.sh. When it passes, commit the change on the current branch with a message
that names the request and the requirement IDs. Write $ARTIFACTS_DIR/implementation.md: the files
changed, the tests added, the verify result, and what you skipped or did not check.
Return the verify result and the commit hash.
