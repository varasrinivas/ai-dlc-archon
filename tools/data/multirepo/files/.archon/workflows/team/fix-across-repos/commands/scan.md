---
description: Read the bug report and both repos; write what a planner needs to know. Changes nothing.
---
The bug: $USER_MESSAGE

Read the bug report it names (in docs-in/) and anything attached next to it. Then read both repos
named in CLAUDE.md: each one's build file and version, the classes the bug touches, their tests, and
the data files. Check each repo's tags and current branch.

Write $ARTIFACTS_DIR/scan.md with:
- each repo: what it is, its version, how it is built and tested, and how the two depend on each other;
- the cause of the bug as far as the code shows it, with the file and method in each repo;
- what is missing (data, rules), and which repo it belongs in;
- risks: callers in either repo, and tests that a change could break.

Do not change any file in either repo or in the workspace. Return a five-line summary.
