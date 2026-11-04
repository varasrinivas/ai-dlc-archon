---
description: Read the request and the code; write what a planner needs to know. Changes nothing.
---
The request: $USER_MESSAGE

Read the request file it names (in docs-in/), then the code in priorauth-api/ (the repo named in
CLAUDE.md): the build file, the entry points, the classes the request touches, the tests, the
configuration and the data files. Check the repo's current branch and its tags.

Write $ARTIFACTS_DIR/scan.md with:
- what the repo is and how it is built and tested (the verify command from CLAUDE.md);
- the classes and files the request touches, with one line each on what they do now;
- what is missing for the request (data, rules, configuration);
- risks: callers or tests that a change could break.

Do not change any file in priorauth-api or in the workspace. Return a five-line summary.
