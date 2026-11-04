"""Build the run's folder D:\\tmp\\archon-java from scratch (no Claude):

  origin.git      a bare copy of the public starter (main = v1.0.2), standing in for GitHub so pushes are real
  priorauth-api/  Kiran's clone: the starter + the team's files from tools/data/java/files/, committed and pushed

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
STARTER = "https://github.com/varasrinivas/aidlc-priorauth-api"


def rm(path):
    def onerr(func, p, _):
        Path(p).chmod(stat.S_IWRITE)
        func(p)
    if path.exists():
        shutil.rmtree(path, onerror=onerr)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rm(RUN)
    RUN.mkdir(parents=True)
    if STEPS.exists():
        STEPS.unlink()
    repo = RUN / "priorauth-api"
    # The stand-in for GitHub: a bare repo with main only (no answer-key tag for the AI to find).
    run(STEPS, "origin", RUN, ["git", "clone", "-q", "--bare", "--single-branch", "--no-tags", STARTER, "origin.git"])
    run(STEPS, "clone", RUN, ["git", "clone", str(RUN / "origin.git"), "priorauth-api"])
    run(STEPS, "identity", repo, "git config user.name 'Kiran Rao' && git config user.email kiran@acme-health.example", sh=True)
    for f in sorted(p for p in FILES.rglob("*") if p.is_file()):
        rel = f.relative_to(FILES)
        dest = repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
    run(STEPS, "chmod", repo, ["git", "update-index", "--add", "--chmod=+x", "scripts/verify.sh"])
    run(STEPS, "team-files", repo, "git add -A && git status --short", sh=True)
    run(STEPS, "validate", repo, ["archon", "validate", "workflows", "request-to-pr"])
    run(STEPS, "commit", repo, ["git", "commit", "-q", "-m", "Add the team's Archon files: CLAUDE.md, verify scripts, request-to-pr workflow"])
    run(STEPS, "push", repo, ["git", "push", "-q", "origin", "main"])
    run(STEPS, "verify-before", repo, "./scripts/verify.sh && echo 'verify: passed'", sh=True, timeout=600)


if __name__ == "__main__":
    main()
