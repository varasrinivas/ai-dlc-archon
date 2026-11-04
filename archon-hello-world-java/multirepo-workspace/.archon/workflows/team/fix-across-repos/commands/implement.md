---
description: Fix the bug as planned, in each repo the plan names; one pass of the implement loop.
---
The bug: $USER_MESSAGE

Implement the approved plan in $ARTIFACTS_DIR/plan.md, following CLAUDE.md. Notes from the person
who approved the plan: $approve-plan.output.text

If an earlier pass ran, this is what it reported (fix what it left failing):
$LOOP_PREV_OUTPUT

In each repo the plan names: switch to the plan's branch (create it from main if it does not exist
yet), make that repo's change, and commit it there with a message that names the bug report. Do not
commit in the workspace folder, do not touch a repo the plan does not name, and do not push.

Run ./scripts/verify.sh from the workspace root. Write $ARTIFACTS_DIR/implementation.md: per repo,
the branch, the files changed, the tests added and the commit; the verify result; and what you
skipped or did not check. Return the verify result and each repo's commit hash.
