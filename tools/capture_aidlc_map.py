"""Check the aidlc-on-archon workflow with Archon itself: validate it, then dry-run it once per AI-DLC scope.

Rebuilds D:\\tmp\\archon-aidlc\\aidlc-workspace from the course's java workspace (archon-hello-world-java/java-workspace/,
priorauth-api inside, each its own git repo) plus the generated workflow, and records every command in
tools/data/aidlc/steps.json (labels: validate, stubs-init, dry-<scope> for each of the 11 scopes, dry-feature-pipeline,
dry-poc-greenfield).

The dry runs use --exec-code, so the bash nodes and the state-init script really run (state-init decides which stages
run; code-generation-verify runs the project's real scripts/verify.sh); the agent nodes and the gates are stubbed
(tools/data/aidlc/stubs*.yaml: workspace detection's answer, every gate approved). No model is called, nothing costs.

Usage: py -3.12 tools/make_aidlc_workflow.py; py -3.12 tools/capture_aidlc_map.py
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aidlc_map import DATA, INIT_KIND, ROOT, SCOPE_ORDER, SLUGS, WF_FILE  # noqa: E402
from archon_step import env, run  # noqa: E402

BASE = Path(r"D:\tmp\archon-aidlc")
WS = BASE / "aidlc-workspace"
STEPS = DATA / "steps.json"
MSG = "Implement the request in docs-in/request.md"


def stubs(name, greenfield=False, pipeline=False):
    summary = ("No application code yet." if greenfield else
               "One Spring Boot repo, priorauth-api; scripts/verify.sh runs its tests; " + ("a CI pipeline in .github/workflows." if pipeline else "no CI pipeline."))
    lines = ["# Dry-run stubs: what workspace detection would answer, and every gate approved.",
             "workspace-detection:", f"  greenfield: {str(greenfield).lower()}", f"  has_pipeline: {str(pipeline).lower()}",
             f"  repos: [{'' if greenfield else 'priorauth-api'}]", f'  summary: "{summary}"']
    for s in SLUGS:
        if s not in INIT_KIND:
            lines += [f"{s}-gate:", "  decision: approve", '  text: ""']
    path = DATA / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def git(cwd, *a):
    subprocess.run(["git", "-c", "user.name=Kiran Rao", "-c", "user.email=kiran@example.com", *a], cwd=cwd, check=True, env=env())


def setup():
    if BASE.exists():
        shutil.rmtree(BASE, onexc=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
    shutil.copytree(ROOT / "archon-hello-world-java" / "java-workspace", WS)
    shutil.copytree(WF_FILE.parent, WS / ".archon" / "workflows" / "aidlc" / "aidlc-on-archon")
    for d in (WS / "priorauth-api", WS):
        git(d, "init", "-q", "-b", "main")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "starting point")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    setup()
    if STEPS.exists():
        STEPS.unlink()
    plain = stubs("stubs.yaml")
    run(STEPS, "validate", WS, ["archon", "validate", "workflows", "aidlc-on-archon"])
    run(STEPS, "stubs-init", WS, ["archon", "workflow", "run", "aidlc-on-archon", "--dry-run", "--stubs-init", str(BASE / "stubs-init.yaml"), MSG])
    shutil.copy(BASE / "stubs-init.yaml", DATA / "stubs-init.yaml")
    for scope in SCOPE_ORDER:
        run(STEPS, f"dry-{scope}", WS, ["archon", "workflow", "run", "aidlc-on-archon", "--dry-run", "--exec-code", "--stubs", str(plain),
                                        "--default-stubs", "--input", f"scope={scope}", MSG], timeout=600, echo=False)
        print(f"dry-{scope} done")
    run(STEPS, "dry-feature-pipeline", WS, ["archon", "workflow", "run", "aidlc-on-archon", "--dry-run", "--exec-code", "--stubs",
                                            str(stubs("stubs-pipeline.yaml", pipeline=True)), "--default-stubs", "--input", "scope=feature", MSG], timeout=600, echo=False)
    run(STEPS, "dry-poc-greenfield", WS, ["archon", "workflow", "run", "aidlc-on-archon", "--dry-run", "--exec-code", "--stubs",
                                          str(stubs("stubs-greenfield.yaml", greenfield=True)), "--default-stubs", "--input", "scope=poc", MSG], timeout=600, echo=False)
    print("wrote", STEPS)


if __name__ == "__main__":
    main()
