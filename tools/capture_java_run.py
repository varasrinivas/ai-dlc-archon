"""Copy the course's real run from D:\\tmp\\archon-java and ~/.archon into archon-hello-world-java/ (no Claude, seconds).

  java-run/setup-steps.json, steps.json   every scripted command (setup_java_run.py, archon_step.py), paths mapped
  java-run/logs/<run-id>.jsonl            each run's transcript, paths mapped
  java-run/artifacts/<run-id>/            the files each run wrote to $ARTIFACTS_DIR (engine-internal .archon/ left out)
  java-run/nodes.json                     per run, per node: kind of event, duration, tokens, cost (from the transcripts)
  java-run/git/                           the branch graph, the diff main..request-age/age-api, its stat
  java-workspace/                         the repo as it is at the end of the branch (git archive, no .git)

Usage: py -3.12 tools/capture_java_run.py
"""
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pagekit import scrub, strip_ansi  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "archon-hello-world-java"
RUNDIR = DEST / "java-run"
WS = DEST / "java-workspace"
ORIGIN = Path(r"D:\tmp\archon-java\origin.git")
PROJ = Path.home() / ".archon" / "workspaces" / "_local" / "priorauth-api"
BRANCH = "request-age/age-api"


def git(*args):
    return subprocess.run(["git", "-C", str(ORIGIN)] + list(args), capture_output=True, encoding="utf-8", errors="replace", check=True).stdout


def clean_steps(src, dest):
    steps = json.loads(Path(src).read_text(encoding="utf-8"))
    for s in steps:
        for k in ("cmd", "cwd", "stdout", "stderr"):
            s[k] = scrub(strip_ansi(s[k]))
    dest.write_text(json.dumps(steps, indent=1, ensure_ascii=False), encoding="utf-8")
    return steps


def node_table(rows):
    out = []
    for r in rows:
        if r.get("type") not in ("node_complete", "node_skipped", "node_failed"):
            continue
        e = r.get("execution") or {}
        spend, timing = e.get("spend") or {}, e.get("timing") or {}
        tok = (spend.get("tokens") or {}).get("value")
        cost = (spend.get("costUsd") or {}).get("value")
        if r["type"] == "node_skipped" and not timing:
            continue  # a resume replaying a finished node
        out.append({"node": r.get("step"), "event": r["type"], "ts": r.get("ts"), "ms": timing.get("durationMs"),
                    "input": tok and tok.get("input"), "output": tok and tok.get("output"), "cost": cost})
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if RUNDIR.exists():
        shutil.rmtree(RUNDIR)
    (RUNDIR / "logs").mkdir(parents=True)
    clean_steps(ROOT / "tools/data/java/setup-steps.json", RUNDIR / "setup-steps.json")
    steps = clean_steps(ROOT / "tools/data/java/run-steps.json", RUNDIR / "steps.json")
    print("steps:", [s["label"] for s in steps])

    nodes = {}
    for log in sorted((PROJ / "logs").glob("*.jsonl")):
        text = scrub(log.read_text(encoding="utf-8"))
        (RUNDIR / "logs" / log.name).write_text(text, encoding="utf-8")
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        start = next(r for r in rows if r.get("type") == "workflow_start")
        nodes[log.stem] = {"workflow": start["workflow_name"], "message": start.get("content"), "start": start["ts"],
                           "end": rows[-1].get("ts"), "events": len(rows), "nodes": node_table(rows)}
    (RUNDIR / "nodes.json").write_text(json.dumps(nodes, indent=1, ensure_ascii=False), encoding="utf-8")
    print("runs:", {k: v["workflow"] for k, v in nodes.items()})

    for run in (PROJ / "artifacts" / "runs").iterdir():
        for f in run.rglob("*"):
            rel = f.relative_to(run)
            if f.is_file() and rel.parts[0] != ".archon":
                d = RUNDIR / "artifacts" / run.name / rel
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_text(scrub(f.read_text(encoding="utf-8")), encoding="utf-8")

    g = RUNDIR / "git"
    g.mkdir()
    (g / "graph.txt").write_text(git("log", "--graph", "--oneline", "--decorate", "--all"), encoding="utf-8")
    (g / "branch-log.txt").write_text(git("log", "--format=%h %an %ad%n    %s", "--date=format:%a %d %b %H:%M", f"main^1..{BRANCH}"), encoding="utf-8")
    (g / "diff.patch").write_text(git("diff", f"main^1..{BRANCH}"), encoding="utf-8")
    (g / "diffstat.txt").write_text(git("diff", "--stat=100", f"main^1..{BRANCH}"), encoding="utf-8")
    (g / "files.txt").write_text(git("ls-tree", "-r", "--name-only", BRANCH), encoding="utf-8")
    for c in git("rev-list", "--reverse", f"main^1..{BRANCH}").split():
        (g / f"commit-{c[:7]}.patch").write_text(git("show", "--stat=100", "--patch", c), encoding="utf-8")

    if WS.exists():
        shutil.rmtree(WS)
    WS.mkdir()
    tar = subprocess.run(["git", "-C", str(ORIGIN), "archive", "--format=tar", BRANCH], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(WS, filter="data")
    print("java-workspace:", sum(1 for p in WS.rglob("*") if p.is_file()), "files")


if __name__ == "__main__":
    main()
