#!/usr/bin/env bash
# The one verification command for this workspace. Archon runs it in loop until_bash and bash nodes.
set -euo pipefail
cd "$(dirname "$0")/../priorauth-api"
mvn -q test
