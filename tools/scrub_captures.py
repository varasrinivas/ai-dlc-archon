"""Scrub this machine's identity out of the raw captures, in place, so the repo can be public.

The pages were always scrubbed at build time (pagekit.scrub); the captures under tools/data/ and
archon-hello-world-java/java-run/ were not. This maps, in every tracked text file there:
  the Windows user folder -> C:\\Users\\you     the run folder D:\\tmp\\archon-java -> C:\\work\\archon-java
  other D:\\tmp folders   -> C:\\work           the hostname -> your-pc, "started by <user>" -> "started by you"
  a Claude scratchpad      -> C:\\work\\scratch   the Claude projects slug -> ...-you-...
Backslashes may be escaped any number of times (JSON in JSONL in JSON), so separators are matched as runs.
Idempotent: run it after every new capture (capture_cli.py, capture_java_run.py, archon_step.py).
Usage: py -3.12 tools/scrub_captures.py [--check]
"""
import getpass
import re
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ("tools/data/", "archon-hello-world-java/java-run/")
USER = getpass.getuser()
HOST = socket.gethostname()
S = r"(\\+|/)"  # one separator, escaped any number of times (or a forward slash)

RULES = [
    # a Claude Code scratchpad: <home>\AppData\Local\Temp\claude\<hash>\<session>\scratchpad -> C:\work\scratch
    (re.compile(rf"C:{S}Users\1{re.escape(USER)}\1AppData\1Local\1Temp\1claude\1[0-9a-f]+\1[0-9a-f-]+\1scratchpad", re.I),
     lambda m: f"C:{m[1]}work{m[1]}scratch"),
    (re.compile(rf"C:{S}Users\1you\1AppData\1Local\1Temp\1claude\1[0-9a-f]+\1[0-9a-f-]+\1scratchpad", re.I),
     lambda m: f"C:{m[1]}work{m[1]}scratch"),
    (re.compile(rf"([A-Za-z]):{S}Users\2{re.escape(USER)}\b", re.I), lambda m: f"{m[1]}:{m[2]}Users{m[2]}you"),
    (re.compile(rf"/([cC])/Users/{re.escape(USER)}\b"), lambda m: f"/{m[1]}/Users/you"),
    (re.compile(rf"D:{S}tmp\1archon-java\b", re.I), lambda m: f"C:{m[1]}work{m[1]}archon-java"),
    (re.compile(r"/d/tmp/archon-java\b"), lambda m: "/c/work/archon-java"),
    (re.compile(rf"D:{S}tmp\b", re.I), lambda m: f"C:{m[1]}work"),
    (re.compile(r"/d/tmp\b"), lambda m: "/c/work"),
    (re.compile(rf"\bUsers-{re.escape(USER)}-", re.I), lambda m: "Users-you-"),
    (re.compile(r"\b[A-Za-z]--tmp-"), lambda m: "C--work-"),
    (re.compile(rf"\bstarted by {re.escape(USER)}\b"), lambda m: "started by you"),
    (re.compile(re.escape(HOST), re.I), lambda m: "your-pc"),
]
# What must not survive anywhere in those folders.
LEAKS = re.compile(rf"Users{S}{re.escape(USER)}\b|D:{S}tmp\b|/d/tmp\b|{re.escape(HOST)}|\\Temp\\+claude\\|started by {re.escape(USER)}\b", re.I)


def tracked():
    out = subprocess.run(["git", "ls-files", "-z", *DIRS], cwd=ROOT, capture_output=True, check=True).stdout
    return [ROOT / p for p in out.decode().split("\0") if p]


def scrub(text):
    for rx, fn in RULES:
        text = rx.sub(fn, text)
    return text


def main():
    check = "--check" in sys.argv
    changed, dirty = [], []
    for f in tracked():
        raw = f.read_bytes()
        if b"\0" in raw[:4096]:
            continue  # binary
        text = raw.decode("utf-8")
        new = scrub(text)
        if new != text:
            changed.append(f)
            if not check:
                f.write_bytes(new.encode("utf-8"))
        for m in LEAKS.finditer(new):
            dirty.append(f"{f.relative_to(ROOT)}: ...{new[max(0, m.start() - 40):m.end() + 40]!r}...")
    verb = "would change" if check else "changed"
    print(f"{verb} {len(changed)} file(s)")
    for f in changed:
        print("  ", f.relative_to(ROOT))
    if dirty:
        print("still leaking:", *dirty[:20], sep="\n  ")
        sys.exit(1)
    if check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
