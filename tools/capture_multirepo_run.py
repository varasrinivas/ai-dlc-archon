"""Copy the course's real two-repo run from D:\\tmp\\archon-multirepo and ~/.archon into
archon-hello-world-java/multirepo-run/ (no Claude, seconds):

  setup-steps.json, steps.json   every scripted command (setup_multirepo_run.py, archon_step.py), paths mapped
  logs/<run-id>.jsonl            the run's transcript, paths mapped
  artifacts/<run-id>/            the files the run wrote to $ARTIFACTS_DIR (engine-internal .archon/ left out)
  nodes.json                     per node: kind of event, duration, tokens, cost (from the transcript)
  git/<repo>/                    per code repo: the graph, the fix's commit as a patch, the diff and stat from the
                                 version before (v1.0.0 / v1.2.0) to the merge (v1.0.1 / v1.2.1)
  storage.txt                    the folder project's own folders under ~/.archon/workspaces/_folder/
  ../multirepo-workspace/        the team workspace at its main with priorauth-aging/ and priorauth-api/ inside it,
                                 each at its main after the merge (git archive, no .git): real, buildable files

Then run tools/scrub_captures.py --check (this folder is in its list).
Usage: py -3.12 tools/capture_multirepo_run.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from capture_java_run import archive, clean_steps, node_table  # noqa: E402
from pagekit import scrub  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNDIR = ROOT / "archon-hello-world-java" / "multirepo-run"
WSDIR = ROOT / "archon-hello-world-java" / "multirepo-workspace"
REMOTES = Path(r"D:\tmp\archon-multirepo\remotes")
PROJ = Path.home() / ".archon" / "workspaces" / "_folder" / "priorauth-workspace"
REPOS = {"priorauth-aging": ("v1.0.0", "v1.0.1"), "priorauth-api": ("v1.2.0", "v1.2.1")}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(REMOTES / f"{repo}.git"), *args], capture_output=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if RUNDIR.exists():
        shutil.rmtree(RUNDIR)
    (RUNDIR / "logs").mkdir(parents=True)
    clean_steps(ROOT / "tools/data/multirepo/setup-steps.json", RUNDIR / "setup-steps.json")
    steps = clean_steps(ROOT / "tools/data/multirepo/run-steps.json", RUNDIR / "steps.json")
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

    for repo, (before, after) in REPOS.items():
        g = RUNDIR / "git" / repo
        g.mkdir(parents=True)
        (g / "graph.txt").write_text(git(repo, "log", "--graph", "--oneline", "--decorate", "--all"), encoding="utf-8")
        (g / "diff.patch").write_text(git(repo, "diff", f"{before}..{after}"), encoding="utf-8")
        (g / "diffstat.txt").write_text(git(repo, "diff", "--stat=100", f"{before}..{after}"), encoding="utf-8")
        fix = git(repo, "rev-parse", f"{after}^2").strip()  # the branch's commit, the merge's second parent
        (g / f"commit-{fix[:7]}.patch").write_text(git(repo, "show", "--stat=100", "--patch", fix), encoding="utf-8")

    (RUNDIR / "storage.txt").write_text(
        "\n".join(str(p.relative_to(PROJ.parent.parent)).replace("\\", "/") + ("/" if p.is_dir() else "")
                  for p in sorted(PROJ.rglob("*")) if len(p.relative_to(PROJ).parts) <= 3) + "\n", encoding="utf-8")
    print("captured into", RUNDIR.relative_to(ROOT))
    archive(REMOTES / "priorauth-workspace.git", WSDIR, {r: REMOTES / f"{r}.git" for r in REPOS})


if __name__ == "__main__":
    main()
