"""Copy the real express run of aidlc-on-archon into tools/data/aidlc/run/ (scrubbed).

The run (5 Nov 2026, Archon 0.13.2, Claude Code on the claude.ai login): capture_aidlc_map.py's setup() rebuilt
D:\\tmp\\archon-aidlc\\aidlc-workspace, priorauth-api was replaced by a fresh clone of the public starter (main = v1.0.2,
no tags; the course's java-workspace copy already has the feature merged), then every command went through
`py -3.12 tools/archon_step.py tools/data/aidlc/run-steps.json <label> <workspace> -- ...`. Labels: run wait-1
approve-reverse-engineering wait-2 reject-requirements wait-3 approve-requirements wait-4 jar-check reject-code wait-5
jar-check-2 approve-code wait-6 approve-build-and-test get.

Writes run/steps.json, run/log.jsonl (the transcript), run/nodes.json (per node: event, duration, tokens, cost),
run/record/ (what the stages wrote to $ARTIFACTS_DIR/record), run/git/ (priorauth-api: log, diffstat, diff, per commit).

Usage: py -3.12 tools/capture_aidlc_run.py; then py -3.12 tools/scrub_captures.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aidlc_map import DATA  # noqa: E402
from capture_java_run import clean_steps, node_table  # noqa: E402
from pagekit import scrub  # noqa: E402

RUN_ID = "152af46d5da132b8c79dcb76acaac528"
WS = Path(r"D:\tmp\archon-aidlc\aidlc-workspace")
REPO = WS / "priorauth-api"
PROJ = Path.home() / ".archon" / "workspaces" / "_folder" / "aidlc-workspace"
OUT = DATA / "run"
BRANCH = "request-age/pending-list-age"


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, encoding="utf-8", errors="replace", check=True).stdout


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    steps = clean_steps(DATA / "run-steps.json", OUT / "steps.json")
    print("steps:", [s["label"] for s in steps])

    text = scrub((PROJ / "logs" / f"{RUN_ID}.jsonl").read_text(encoding="utf-8"))
    (OUT / "log.jsonl").write_text(text, encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    start = next(r for r in rows if r.get("type") == "workflow_start")
    nodes = {"workflow": start["workflow_name"], "message": start.get("content"), "start": start["ts"],
             "end": rows[-1].get("ts"), "events": len(rows), "nodes": node_table(rows)}
    (OUT / "nodes.json").write_text(json.dumps(nodes, indent=1, ensure_ascii=False), encoding="utf-8")

    rec = PROJ / "artifacts" / "runs" / RUN_ID / "record"
    for f in rec.rglob("*"):
        if f.is_file():
            d = OUT / "record" / f.relative_to(rec)
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_text(scrub(f.read_text(encoding="utf-8")), encoding="utf-8")

    g = OUT / "git"
    g.mkdir()
    rng = f"main..{BRANCH}"
    (g / "branch-log.txt").write_text(git("log", "--reverse", "--format=%h %s", rng), encoding="utf-8")
    (g / "diffstat.txt").write_text(git("diff", "--stat=100", rng), encoding="utf-8")
    (g / "diff.patch").write_text(git("diff", rng), encoding="utf-8")
    (g / "main.txt").write_text(git("log", "--format=%h %s", "main"), encoding="utf-8")
    for c in git("rev-list", "--reverse", rng).split():
        (g / f"commit-{c[:7]}.patch").write_text(git("show", "--stat=100", "--patch", c), encoding="utf-8")
    print("wrote", OUT, "nodes:", len(nodes["nodes"]))


if __name__ == "__main__":
    main()
