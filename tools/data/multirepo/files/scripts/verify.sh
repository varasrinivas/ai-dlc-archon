#!/usr/bin/env bash
# The one verification command for this workspace. Archon runs it in loop until_bash and bash nodes.
# priorauth-api depends on priorauth-aging: install the library (the version its pom names), then test the API.
set -euo pipefail
cd "$(dirname "$0")/.."
(cd priorauth-aging && mvn -q install)
(cd priorauth-api && mvn -q test)
