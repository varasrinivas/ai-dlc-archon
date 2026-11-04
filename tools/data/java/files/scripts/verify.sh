#!/usr/bin/env bash
# The one verification command for this repo. Archon runs it in loop until_bash and bash nodes.
set -uo pipefail
cd "$(dirname "$0")/.."
mvn -q test
