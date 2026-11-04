"""Build the Java run's folder D:\\tmp\\archon-java from scratch (no Claude):

  remotes/priorauth-api.git    a bare copy of the public starter (main = v1.0.2, no tags), standing in for GitHub
  remotes/java-workspace.git   the team's workspace repo: .archon/, CLAUDE.md, scripts/verify.*, docs-in/request.md
  java-workspace/              Kiran's clone of the workspace, with priorauth-api cloned inside it

The same layout as the AI-DLC course's java-workspace/ (a workspace folder around the code repo) and as this course's
two-repo run: the workspace is an Archon folder project. The bare repos stand in for GitHub so pushes are real.
Records every command in tools/data/java/setup-steps.json. Usage: py -3.12 tools/setup_java_run.py
"""
import shutil
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from archon_step import run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FILES = ROOT / "tools" / "data" / "java" / "files"
STEPS = ROOT / "tools" / "data" / "java" / "setup-steps.json"
RUN = Path(r"D:\tmp\archon-java")
REMOTES, BUILD = RUN / "remotes", RUN / "build"
WS = RUN / "java-workspace"
STARTER = "https://github.com/varasrinivas/aidlc-priorauth-api"
MEENA = "git -c user.name='Meena Iyer' -c user.email=meena@acme-health.example"

BEFORE = """set -u
cd priorauth-api
mvn -q -DskipTests package
java -jar target/priorauth-api-1.0.2.jar --server.port=8092 > ../../app-before.log 2>&1 &
pid=$!
for i in $(seq 90); do curl -s -o /dev/null localhost:8092/requests/pending && break; sleep 1; done
echo '$ curl "http://localhost:8092/requests/pending?asOf=2026-10-13"'
curl -s 'localhost:8092/requests/pending?asOf=2026-10-13'; echo
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
    wsb = BUILD / "java-workspace"

    # 1. The code repo's remote: the public starter, main only (no answer-key tag for the AI to find).
    run(STEPS, "remote-priorauth-api", REMOTES, ["git", "clone", "-q", "--bare", "--single-branch", "--no-tags", STARTER, "priorauth-api.git"])
    run(STEPS, "starter-log", REMOTES / "priorauth-api.git", "git log --oneline -3 && git tag | wc -l", sh=True)

    # 2. The team's workspace: a git repo of its own that ignores the code repo cloned inside it.
    for f in sorted(p for p in FILES.rglob("*") if p.is_file()):
        dest = wsb / f.relative_to(FILES)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
    run(STEPS, "workspace-repo", wsb, f"git init -q -b main && git add -A && git update-index --chmod=+x scripts/verify.sh && {MEENA} commit -q -m 'The java workspace: CLAUDE.md, verify scripts, the request-to-pr workflow, the request' && git ls-files", sh=True)

    # 3. Its remote, standing in for GitHub; push main.
    bare = REMOTES / "java-workspace.git"
    run(STEPS, "remote-java-workspace", REMOTES, ["git", "init", "-q", "--bare", "-b", "main", str(bare)])
    run(STEPS, "push-java-workspace", wsb, f"git remote add origin '{bare.as_posix()}' && git push -q -u origin main 2>&1 && git log --oneline", sh=True)
    rm(BUILD)

    # 4. Kiran's machine: clone the workspace, then the code repo inside it.
    run(STEPS, "clone-workspace", RUN, ["git", "clone", "-q", str(bare), "java-workspace"])
    run(STEPS, "clone-priorauth-api", WS, ["git", "clone", "-q", str(REMOTES / "priorauth-api.git"), "priorauth-api"])
    run(STEPS, "identity", WS, "for d in . priorauth-api; do git -C $d config user.name 'Kiran Rao'; git -C $d config user.email kiran@acme-health.example; done; git status --short --ignored", sh=True)
    run(STEPS, "tree", WS, "ls -a; echo '== priorauth-api'; git -C priorauth-api log --oneline --decorate -3; grep -m2 -n '<version>' priorauth-api/pom.xml", sh=True)

    # 5. Before the run: the workflow is valid, the code builds, and the request is not there yet.
    run(STEPS, "validate", WS, ["archon", "validate", "workflows", "request-to-pr"])
    s = run(STEPS, "verify-before", WS, "./scripts/verify.sh && echo 'verify: passed'; grep -h 'Tests run' priorauth-api/target/surefire-reports/*.txt", sh=True, timeout=900)
    assert "verify: passed" in s["stdout"], "the starter doesn't build"
    run(STEPS, "before", WS, BEFORE, sh=True, timeout=600)


if __name__ == "__main__":
    main()
