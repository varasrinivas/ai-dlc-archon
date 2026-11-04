"""Capture the real Archon CLI output the introduction and setup pages quote (no Claude, seconds).

Needs Archon installed (~/.archon/bin/archon.exe) and the workspace from setup_java_run.py (D:\\tmp\\archon-java\\java-workspace).
Writes tools/data/cli/cli.json ({label: {cmd, exit, out}}), inventory.json (every file under ~/.archon, with sizes),
and bundled/ (the sdlc pack's YAML at the installed release's tag, read from a shallow clone of the Archon repo).

Usage: py -3.12 tools/capture_cli.py [<archon-source-clone>]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from archon_step import ARCHON, env  # noqa: E402
from pagekit import scrub, strip_ansi  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "data" / "cli"
REPO = Path(r"D:\tmp\archon-java\java-workspace")  # the team workspace (a folder project), priorauth-api inside it
HOME = Path.home() / ".archon"

CMDS = [
    ("version", ["version"]),
    ("help", ["help"]),
    ("help-workflow-run", ["workflow", "run", "--help"]),
    ("doctor", ["doctor"]),
    ("telemetry", ["telemetry", "status"]),
    ("workflow-list", ["workflow", "list"]),
    ("workflow-list-json", ["workflow", "list", "--json"]),
    ("validate", ["validate", "workflows"]),
    ("validate-commands", ["validate", "commands"]),
    ("project-list", ["project", "list"]),
    ("tier-list", ["ai", "tier", "list"]),
    ("plugin-list", ["plugin", "list"]),
    ("isolation-list", ["isolation", "list"]),
    ("runs", ["workflow", "runs"]),
]


def archon(args, cwd=REPO):
    p = subprocess.run([ARCHON] + args, cwd=cwd, env=env(), capture_output=True, encoding="utf-8", errors="replace")
    return p.returncode, scrub(strip_ansi(p.stdout + (("\n" + p.stderr) if p.stderr.strip() else "")))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    for label, args in CMDS:
        code, out = archon(args)
        data[label] = {"cmd": "archon " + " ".join(args), "exit": code, "out": out}
        print(f"{label:22} exit={code} {len(out)} chars")
    # Every bundled workflow's full description (what `workflow list <name> --full` prints).
    p = subprocess.run([ARCHON, "workflow", "list", "--json"], cwd=REPO, env=env(), capture_output=True, encoding="utf-8")
    data["workflow-list-json"]["out"] = p.stdout  # stdout only: the discovery line goes to stderr
    names = [w["name"] for w in json.loads(p.stdout)["workflows"]]
    data["full"] = {n: archon(["workflow", "list", n, "--full"])[1] for n in names}
    # Outside a git repo, workflow commands refuse to run (the setup page shows this).
    code, out = archon(["workflow", "list"], cwd=Path.home())
    data["outside-repo"] = {"cmd": "archon workflow list", "exit": code, "out": out}
    (OUT / "cli.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")

    inv = []
    for p in sorted(HOME.rglob("*")):
        if p.is_file():
            rel = p.relative_to(HOME).as_posix()
            inv.append({"path": rel, "bytes": p.stat().st_size})
    (OUT / "inventory.json").write_text(json.dumps(inv, indent=1), encoding="utf-8")
    print("inventory:", len(inv), "files")

    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if src:
        dest = OUT / "bundled"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src / ".archon" / "workflows" / "sdlc", dest, ignore=shutil.ignore_patterns("fixtures", "*.test.*"))
        commit = subprocess.run(["git", "-C", str(src), "log", "-1", "--format=%h %s"], capture_output=True, text=True).stdout.strip()
        (dest / "SOURCE.txt").write_text(f"coleam00/Archon {commit}\n", encoding="utf-8")
        print("bundled:", sum(1 for _ in dest.rglob("*.yaml")), "yaml files from", commit)


if __name__ == "__main__":
    main()
