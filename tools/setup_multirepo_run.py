"""Build the two-repo run's folder D:\\tmp\\archon-multirepo from scratch (no Claude):

  remotes/priorauth-aging.git      the request-aging library 1.0.0, split out of the public starter at v1.1.0
  remotes/priorauth-api.git        the starter at v1.1.0 without the aging package, depending on the library: 1.2.0
  remotes/priorauth-workspace.git  the team's workspace: .archon/, CLAUDE.md, scripts/verify.*, docs-in/
  priorauth-workspace/             Kiran's clone of the workspace, with both repos cloned inside it

The same two-repo split as the AI-DLC course's "Two repos, one graph" run (ai-dlc-execution/tools/
setup_graphify_multirepo.py), and the same bug report, so the two runs can be compared. The bare repos stand in
for GitHub so pushes are real. Records every command in tools/data/multirepo/setup-steps.json.
Usage: py -3.12 tools/setup_multirepo_run.py
"""
import shutil
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from archon_step import run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FILES = ROOT / "tools" / "data" / "multirepo" / "files"
STEPS = ROOT / "tools" / "data" / "multirepo" / "setup-steps.json"
RUN = Path(r"D:\tmp\archon-multirepo")
REMOTES, BUILD = RUN / "remotes", RUN / "build"
WS = RUN / "priorauth-workspace"
STARTER = "https://github.com/varasrinivas/aidlc-priorauth-api"
PKG, TPKG = "src/main/java/com/acmehealth/priorauth/aging/", "src/test/java/com/acmehealth/priorauth/aging/"
DATA = "src/main/resources/data/holidays-"
MEENA = "git -c user.name='Meena Iyer' -c user.email=meena@acme-health.example"

AGING_POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <!-- The same parent as priorauth-api, so both repos use the same Spring and Jackson versions. -->
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.1.1</version>
    <relativePath/>
  </parent>

  <groupId>com.acmehealth</groupId>
  <artifactId>priorauth-aging</artifactId>
  <version>1.0.0</version>
  <name>priorauth-aging</name>
  <description>Request aging for prior auth: business days, tenant holiday calendars, the age badge. A library; priorauth-api depends on it.</description>

  <properties>
    <java.version>21</java.version>
  </properties>

  <dependencies>
    <!-- Spring core (for @Service and classpath resources) and Jackson (to read the holiday files). -->
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter</artifactId>
    </dependency>
    <dependency>
      <groupId>tools.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
    </dependency>
    <!-- JUnit 5 and AssertJ for the tests. Test scope: never shipped. -->
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
"""

AGING_README = """# priorauth-aging

Request aging for the prior-auth reviewer screen, as a library: `BusinessDays` (business days between two dates),
`HolidayCalendar` (a tenant's holidays, from `src/main/resources/data/holidays-<tenant>-<year>.json`) and `AgeBadge`
(the age and the over-limit flag). `priorauth-api` depends on it (`com.acmehealth:priorauth-aging`).

Build and install it locally before building the API: `mvn -q install`.
Split out of priorauth-api 1.1.0 (the `aging` package and its tests, unchanged).
"""

API_DEP = """    <!-- Request aging (business days, tenant holidays, the age badge): our library, repo priorauth-aging. -->
    <dependency>
      <groupId>com.acmehealth</groupId>
      <artifactId>priorauth-aging</artifactId>
      <version>1.0.0</version>
    </dependency>
"""

BUG_BEFORE = """set -u
cd priorauth-api
mvn -q -DskipTests package
java -jar target/priorauth-api-1.2.0.jar --server.port=8091 > ../../app-before.log 2>&1 &
pid=$!
for i in $(seq 90); do curl -s -o /dev/null localhost:8091/requests/pending && break; sleep 1; done
curl -s 'localhost:8091/requests/pending?asOf=2027-01-05'; echo
kill $pid
"""


def rm(path):
    def onerr(func, p, _):
        Path(p).chmod(stat.S_IWRITE)
        func(p)
    if path.exists():
        shutil.rmtree(path, onerror=onerr)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rm(RUN)
    REMOTES.mkdir(parents=True)
    BUILD.mkdir()
    if STEPS.exists():
        STEPS.unlink()
    api, aging, wsb = BUILD / "priorauth-api", BUILD / "priorauth-aging", BUILD / "priorauth-workspace"

    # 1. Split the public starter at v1.1.0: the aging package becomes a library (1.0.0); the API depends on it (1.2.0).
    run(STEPS, "starter", BUILD, ["git", "clone", "-q", STARTER, "priorauth-api"])
    run(STEPS, "starter-v110", api, "git switch -q -C main v1.1.0 && git remote remove origin && git tag | xargs git tag -d >/dev/null && git log --oneline -1", sh=True)
    moved = [f for f in run(STEPS, "starter-files", api, ["git", "ls-files"], echo=False)["stdout"].split()
             if f.startswith((PKG, TPKG, DATA))]
    assert len(moved) == 6, moved
    for f in moved:
        (aging / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(api / f, aging / f)
    (aging / "pom.xml").write_text(AGING_POM, encoding="utf-8", newline="\n")
    (aging / "README.md").write_text(AGING_README, encoding="utf-8", newline="\n")
    shutil.copyfile(api / ".gitignore", aging / ".gitignore")
    run(STEPS, "aging-repo", aging, f"git init -q -b main && git add -A && {MEENA} commit -q -m 'priorauth-aging 1.0.0: the aging package, split from priorauth-api 1.1.0' && git tag v1.0.0 && git log --oneline", sh=True)
    run(STEPS, "api-split", api, ["git", "rm", "-q", *moved])
    pom = (api / "pom.xml").read_text(encoding="utf-8")
    anchor = "    <!-- JUnit 5, AssertJ and MockMvc"
    assert anchor in pom and pom.count("<version>1.1.0</version>") == 1
    (api / "pom.xml").write_text(pom.replace(anchor, API_DEP + anchor, 1).replace("<version>1.1.0</version>", "<version>1.2.0</version>", 1),
                                 encoding="utf-8", newline="\n")
    run(STEPS, "api-repo", api, f"git add pom.xml && {MEENA} commit -q -m 'Move request aging to the priorauth-aging library (1.0.0); depend on it' && git tag v1.2.0 && git log --oneline -3", sh=True)

    # 2. The team's workspace: a git repo of its own that ignores the code repos cloned inside it.
    for f in sorted(p for p in FILES.rglob("*") if p.is_file()):
        dest = wsb / f.relative_to(FILES)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
    run(STEPS, "workspace-repo", wsb, f"git init -q -b main && git add -A && git update-index --chmod=+x scripts/verify.sh && {MEENA} commit -q -m 'The priorauth workspace: CLAUDE.md, verify scripts, the fix-across-repos workflow' && git ls-files", sh=True)

    # 3. Bare repos standing in for GitHub; push main and the version tags.
    for name, src in (("priorauth-aging", aging), ("priorauth-api", api), ("priorauth-workspace", wsb)):
        bare = REMOTES / f"{name}.git"
        run(STEPS, f"remote-{name}", RUN, ["git", "init", "-q", "--bare", "-b", "main", str(bare)])
        run(STEPS, f"push-{name}", src, f"git remote add origin '{bare.as_posix()}' && git push -q -u origin main --tags 2>&1", sh=True)
    rm(BUILD)

    # 4. Kiran's machine: clone the workspace, then each code repo inside it.
    run(STEPS, "clone-workspace", RUN, ["git", "clone", "-q", str(REMOTES / "priorauth-workspace.git"), "priorauth-workspace"])
    for name in ("priorauth-aging", "priorauth-api"):
        run(STEPS, f"clone-{name}", WS, ["git", "clone", "-q", str(REMOTES / f"{name}.git"), name])
    run(STEPS, "identity", WS, "for d in . priorauth-aging priorauth-api; do git -C $d config user.name 'Kiran Rao'; git -C $d config user.email kiran@acme-health.example; done; git status --short --ignored", sh=True)
    run(STEPS, "tree", WS, "ls -a; for d in priorauth-aging priorauth-api; do echo \"== $d\"; git -C $d log --oneline --decorate; grep -m2 -n '<version>' $d/pom.xml; done", sh=True)

    # 5. Before the run: the workflow is valid, the workspace builds, and the bug shows.
    run(STEPS, "validate", WS, ["archon", "validate", "workflows", "fix-across-repos"])
    s = run(STEPS, "verify-before", WS, "./scripts/verify.sh && echo 'verify: passed'", sh=True, timeout=900)
    assert "verify: passed" in s["stdout"], "the split workspace doesn't build"
    run(STEPS, "bug-before", WS, BUG_BEFORE, sh=True, timeout=600)


if __name__ == "__main__":
    main()
