"""Run one scripted command for a capture and append it to a steps.json (label, cmd, cwd, times, exit, output).

Usage:  py -3.12 tools/archon_step.py <steps.json> <label> <cwd> -- <cmd> [args...]
        py -3.12 tools/archon_step.py <steps.json> <label> <cwd> --sh "<bash script>"

Every call runs on the claude.ai login, never on an API key: ANTHROPIC_API_KEY is removed from the env.
Telemetry is off, JDK 21 is first on PATH (priorauth-api needs it; the machine's default java is 11),
and ARCHON_BASH_PATH points at Git Bash, which is not at a location Archon autodetects on this machine.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

JDK = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot"
BASH = r"D:\Program Files\Git\bin\bash.exe"
ARCHON = str(Path.home() / ".archon" / "bin" / "archon.exe")


def env():
    e = dict(os.environ)
    e.pop("ANTHROPIC_API_KEY", None)
    e["ARCHON_TELEMETRY_DISABLED"] = "1"
    e["JAVA_HOME"] = JDK
    e["PATH"] = JDK + r"\bin;" + str(Path(ARCHON).parent) + ";" + e["PATH"]
    e["ARCHON_BASH_PATH"] = BASH
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def run(steps_file, label, cwd, cmd, sh=False, timeout=None, echo=True):
    """Run cmd (list, or a bash script when sh=True) in cwd; record and return the step dict."""
    argv = [BASH, "-c", cmd] if sh else cmd
    if not sh and argv[0] == "archon":
        argv = [ARCHON] + argv[1:]
    t0 = time.strftime("%Y-%m-%dT%H:%M:%S")
    start = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, env=env(), capture_output=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        out, err, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as ex:
        out, err, code = (ex.stdout or b"").decode("utf-8", "replace") if isinstance(ex.stdout, bytes) else (ex.stdout or ""), "TIMEOUT", -1
    step = {"label": label, "cmd": cmd if sh else " ".join(cmd), "sh": sh, "cwd": str(cwd), "start": t0,
            "seconds": round(time.time() - start, 1), "exit": code, "stdout": out, "stderr": err}
    path = Path(steps_file)
    steps = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    steps = [s for s in steps if s["label"] != label] + [step]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(steps, indent=1, ensure_ascii=False), encoding="utf-8")
    if echo:
        print(f"[{label}] exit={code} {step['seconds']}s")
        sys.stdout.write(out[-6000:])
        if err.strip():
            sys.stdout.write("--- stderr ---\n" + err[-3000:])
    return step


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    steps_file, label, cwd = a[0], a[1], a[2]
    if a[3] == "--sh":
        run(steps_file, label, cwd, a[4], sh=True)
    else:
        assert a[3] == "--", "expected -- before the command"
        run(steps_file, label, cwd, a[4:])
