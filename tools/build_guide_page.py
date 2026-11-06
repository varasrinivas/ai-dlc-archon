"""Build archon-end-to-end-guide.html: the course's two real runs as one runbook, from a bare machine to the merge.

Part A sets up the machine, Part B is "one request, one repo" (request-to-pr), Part C is "one bug, two repos"
(fix-across-repos). Every command is the one recorded in the run's setup-steps.json / steps.json (paths mapped to
$JRUN / $MRUN, the run id to $RUN, messages quoted for bash), plus the few things setup_java_run.py and
setup_multirepo_run.py did in Python (copying the team's files, splitting the starter), written out as shell. Every
"Check" box quotes lines of the real output, and each is asserted here. The narrative run pages tell the story;
this page is the one to follow at a keyboard.

Usage: py -3.12 tools/build_guide_page.py              (writes the page)
       py -3.12 tools/build_guide_page.py --emit java   (prints Part B's setup as one bash script, to test it)
       py -3.12 tools/build_guide_page.py --emit multirepo
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import archon_step  # noqa: E402
import setup_multirepo_run as MR  # noqa: E402
from pagekit import CLAUDE_MAP, E, ROOT, card, claude_facts, io, note, page, phase, plain, rail, scrub, see, step, strip_ansi, table, write, you  # noqa: E402

DATA = ROOT / "tools" / "data"
HW = ROOT / "archon-hello-world-java"


def load(p):
    return {s["label"]: s for s in json.loads(Path(p).read_text(encoding="utf-8"))}


JS, JR = load(HW / "java-run/setup-steps.json"), load(HW / "java-run/steps.json")
MS, MRS = load(HW / "multirepo-run/setup-steps.json"), load(HW / "multirepo-run/steps.json")
PRE = load(DATA / "setup/prereq-steps.json")
CLI = json.loads((DATA / "cli/cli.json").read_text(encoding="utf-8"))
INSTALL = scrub(strip_ansi((DATA / "cli/install.txt").read_text(encoding="utf-8-sig")))
RERUN = json.loads((DATA / "java/rerun-2026-11-06.json").read_text(encoding="utf-8"))
PROBE = json.loads((DATA / "setup/bash-probe.json").read_text(encoding="utf-8"))
VERSION = re.search(r"Archon CLI v([\d.]+)", CLI["version"]["out"]).group(1)
COURSE_URL = "https://github.com/varasrinivas/ai-dlc-archon"
STARTER = "https://github.com/varasrinivas/aidlc-priorauth-api"
assert MR.STARTER == STARTER and VERSION == "0.13.2"

JRID = re.search(r"Run id: (\w+)", JR["run"]["stdout"]).group(1)
MRID = re.search(r"Run id: (\w+)", MRS["run"]["stdout"]).group(1)
OCC = json.loads(JR["wait-1"]["stdout"])["attention"]["occurrence"]


def x(s):
    return E(s)


# ---------- commands: recorded ones, mapped for a reader's shell ----------
def bashq(s):
    """Quote one argument for bash: single quotes when it has none, else double quotes with \\ " $ ` escaped."""
    if "'" not in s:
        return f"'{s}'"
    assert "!" not in s, "history expansion would bite inside double quotes"
    return '"' + re.sub(r'([\\"$`])', r"\\\1", s) + '"'


def paths(t, quote=True):
    """The run folders become "$JRUN" / "$MRUN" (double-quoted: a home folder may have a space), with forward
    slashes (Git Bash eats unquoted backslashes)."""
    t = scrub(t)
    t = re.sub(r"C:[\\/]work[\\/](archon-java|archon-multirepo)((?:[\\/][\w.\-]+)*)",
               lambda m: ("$JRUN" if m.group(1) == "archon-java" else "$MRUN") + m.group(2).replace("\\", "/"), t)
    if not quote:
        return t
    t = re.sub(r"'(\$[JM]RUN[^']*)'", r'"\1"', t)
    return re.sub(r'(?<!")(\$[JM]RUN[\w./\-]*)', r'"\1"', t)


# words before the free-text message: approve/reject <id> <msg>, answer <id> --occurrence <occ> --text <msg>
MSG_AT = {"approve": 4, "reject": 4, "answer": 7}


def split_message(c):
    """The recorded cmd is argv joined by spaces; the message is the last argv element. -> (head words, message)."""
    w = c.split(" ")
    sub = w[2]
    if sub in MSG_AT:
        n = MSG_AT[sub]
    else:  # run <workflow> [--flag | --adopt <id>]... <message>
        assert sub == "run", c
        n = 4
        while w[n].startswith("--"):
            n += 2 if w[n] == "--adopt" else 1
    return w[:n], " ".join(w[n:])


# Changes to the recorded commands, from re-running Part B from this page (6 Nov 2026):
#  - the agent names the branch: that run's was request-age/pending-list-age, so a hardcoded name failed the push, the merge
#    and the cleanup. The page reads it into $BRANCH once the agent has made it (steps 13 and 25).
#  - that run's code looped forever on asOf=+999999999-12-31 (no 500): curl without a timeout waited 18 min.
#  - "verify on main" grepped stale surefire reports left by the branch build; a failed merge left its clone behind.
JB, MB = "request-age/pending-age", "fix/holidays-across-years"
HARDEN = {
    ("java", "fix-run"): [(JB, "$BRANCH")],
    ("java", "jar-check"): [('curl -s -i "localhost', 'curl -s -i --max-time 20 "localhost')],
    ("java", "jar-check-2"): [('curl -s -i "localhost', 'curl -s -i --max-time 20 "localhost')],
    ("java", "push-by-hand"): [(JB, '"$BRANCH"')],
    ("java", "merge"): [("set -e\n", "set -e\nrm -rf meena-priorauth-api\n"), (f"origin/{JB}", '"origin/$BRANCH"'), (f'"Merge {JB}:', '"Merge $BRANCH:')],
    ("java", "complete"): [(JB, '"$BRANCH"')],
    ("java", "verify-main"): [("./scripts/verify.sh", "rm -rf priorauth-api/target\n./scripts/verify.sh")],
    ("java", "cleanup"): [(JB, '"$BRANCH"')],
    ("multirepo", "jar-check"): [('curl -s "localhost:8092/requests/pending?asOf', 'curl -s --max-time 20 "localhost:8092/requests/pending?asOf')],
    ("multirepo", "merge"): [(f"origin/{MB}", '"origin/$BRANCH"'), (f'"Merge {MB}:', '"Merge $BRANCH:')],
    ("multirepo", "complete"): [(MB, '"$BRANCH"')],
    ("multirepo", "cleanup"): [(MB, '"$BRANCH"')],
}
BRANCH_SET = 'BRANCH=$(git -C priorauth-api branch --show-current)   # the branch the agent made\necho "BRANCH=$BRANCH"'


def harden(s, c):
    which = "java" if "archon-java" in s["cwd"] else "multirepo"
    for old, new in HARDEN.get((which, s["label"]), []):
        n = c.count(old)
        assert n >= 1 and (n == 1 or old.startswith("curl")), (which, s["label"], old, n)
        c = c.replace(old, new)
    return c


def command(s):
    c = s["cmd"]
    if not s["sh"] and c.startswith("archon workflow ") and c.split(" ")[2] in ("run", *MSG_AT):
        head, msg = split_message(c)
        assert s["label"] != "fix-run" or "'" in msg, "the fix message must stay double-quoted so $BRANCH expands"
        c = " ".join(head) + " " + bashq(msg)
    c = harden(s, c)
    for rid in (JRID, MRID):
        c = c.replace(rid, "$RUN")
    c = c.replace(OCC, "$OCC")
    c = paths(c).strip()
    if s["sh"] and ("\n" in c or c.startswith("set ")):
        c = "(\n" + c + "\n)"  # the recorded script ran under bash -c: a subshell keeps its cd and set -e out of your terminal
    return c


def script(items):
    """items: steps dicts or (cwd, literal) pairs -> one bash block with a cd wherever the folder changes."""
    out, cwd = [], None
    for it in items:
        if isinstance(it, dict):
            d, c = paths(it["cwd"], quote=False), command(it)
        else:
            d, c = it
        if d and d != cwd:
            out.append(f'cd "{d}"')
            cwd = d
        out.append(c)
    return "\n".join(out)


def cmd(win, mac=None):
    return you(x(win), x(win if mac is None else mac), "Git Bash", "Terminal")


# ---------- checks: lines of the real output, asserted ----------
def text_of(s):
    return scrub(strip_ansi(s["stdout"] + "\n" + s["stderr"]))


def lines(s, *subs):
    """The first line containing each of subs (asserted), in output order."""
    t = text_of(s).splitlines()
    picked = []
    for sub in subs:
        i = next((i for i, ln in enumerate(t) if sub in ln), None)
        assert i is not None, (s["label"], sub)
        picked.append(i)
    return "\n".join(t[i].rstrip() for i in sorted(set(picked)))


def check(s, *subs, tag=None, extra=""):
    body = lines(s, *subs) + extra
    return see(x(body), tag or f"real · {s['seconds']:g} s", "Check: you see")


def attention(s, n=6):
    a = json.loads(s["stdout"])["attention"]
    head = "\n".join(a["message"].strip().splitlines()[:n])
    return see(x(f'"nodeId": "{a["nodeId"]}",  "form": "{a["form"]}",  "occurrence": "{a["occurrence"]}"\n"message":\n{head}\n…'),
               f"real · waited {s['seconds']:g} s", "Check: wait returns")


def cost(s):
    return float(re.search(r"Cost: \$([\d.]+)", s["stdout"]).group(1))


def short(t, n=150):
    return "\n".join(ln if len(ln) <= n else ln[:n] + " …" for ln in t.splitlines())


# ---------- facts this page states ----------
for label in ("claude-version", "git-version", "bash-version", "java-version", "mvn-version", "curl-version", "archon-version"):
    assert PRE[label]["exit"] == 0, label
assert 'openjdk version "21' in PRE["java-version"]["stdout"] and "Apache Maven 3.9" in PRE["mvn-version"]["stdout"]
assert "All checks passed." in CLI["doctor"]["out"] and "Checksum verified" in INSTALL
env = archon_step.env()
assert "ANTHROPIC_API_KEY" not in env and env["ARCHON_TELEMETRY_DISABLED"] == "1" and env["JAVA_HOME"] == archon_step.JDK
assert "bash executable not found" in PROBE["without"] and PROBE["validate_catches_it"] is False
assert "--dry-run cannot be combined with --folder" in MRS["dry-run"]["stderr"]
assert "Rejected but failed to resume" in JR["reject-change"]["stderr"] and "Workflow cancelled" in JR["reject-change"]["stdout"]
assert "no active isolation environment" in JR["complete"]["stdout"] and "no active isolation environment" in MRS["complete"]["stdout"]
COST = {"request-to-pr": cost(JR["reject-change"]), "archon-implement": cost(JR["fix-run"]), "archon-plan": cost(JR["archon-plan"]),
        "fix-across-repos": cost(MRS["approve-change"])}
assert [round(v, 2) for v in COST.values()] == [3.73, 0.63, 0.83, 2.15], COST
MIN = {k: round(sum(s["seconds"] for s in v.values()) / 60) for k, v in (("java", JR), ("multirepo", MRS))}
SLOWEST = max(JR.values(), key=lambda s: s["seconds"])
assert SLOWEST["label"] == "approve-plan"
IMPL = (HW / "multirepo-run/artifacts" / MRID / "implementation.md").read_text(encoding="utf-8")
assert "ClassNotFoundException: org.codehaus.plexus.classworlds.launcher.Launcher" in IMPL
PLIST = JR["project-list"]["stdout"]
assert "_local/priorauth-api" in PLIST and "folder\tjava-workspace" in PLIST

# ---------- the bits setup_*.py did in Python, as shell ----------
J_COPY = ('mkdir -p "$JRUN/remotes" "$JRUN/build/java-workspace"\n'
          'cp -R "$COURSE/tools/data/java/files/." "$JRUN/build/java-workspace/"')
M_FIRST = 'mkdir -p "$MRUN/remotes" "$MRUN/build"'
MOVED = [f for f in MS["starter-files"]["stdout"].split() if f.startswith((MR.PKG, MR.TPKG, MR.DATA))]
assert len(MOVED) == 6 and MS["api-split"]["cmd"] == "git rm -q " + " ".join(MOVED)
M_SPLIT = (f"git ls-files {MR.PKG} {MR.TPKG} '{MR.DATA}*' | while read -r f; do\n"
           '  mkdir -p "../priorauth-aging/${f%/*}" && cp "$f" "../priorauth-aging/$f"\ndone\n'
           "cp .gitignore ../priorauth-aging/\n"
           f"cat > ../priorauth-aging/pom.xml <<'EOF'\n{MR.AGING_POM}EOF\n"
           f"cat > ../priorauth-aging/README.md <<'EOF'\n{MR.AGING_README}EOF")
ANCHOR = "    <!-- JUnit 5, AssertJ and MockMvc"
M_POM = (f"cat > ../api-dep.xml <<'EOF'\n{MR.API_DEP}EOF\n"
         f"awk 'index($0, \"{ANCHOR}\") == 1 {{ while ((getline l < \"../api-dep.xml\") > 0) print l }}\n"
         "     { sub(/\\r$/, \"\"); sub(/<version>1\\.1\\.0<\\/version>/, \"<version>1.2.0</version>\"); print }' pom.xml > pom.new\n"
         "mv pom.new pom.xml && rm ../api-dep.xml")
M_COPY = ('mkdir -p "$MRUN/build/priorauth-workspace"\n'
          'cp -R "$COURSE/tools/data/multirepo/files/." "$MRUN/build/priorauth-workspace/"')

J = lambda *labels: [JS[label] for label in labels]  # noqa: E731
M = lambda *labels: [MS[label] for label in labels]  # noqa: E731
JAVA_SETUP = [
    ("Code remote", [(None, J_COPY.split("\n")[0])] + J("remote-priorauth-api", "starter-log")),
    ("Workspace repo", [(None, J_COPY.split("\n", 1)[1])] + J("workspace-repo", "remote-java-workspace", "push-java-workspace") + [("$JRUN", 'rm -rf build')]),
    ("Clones", J("clone-workspace", "clone-priorauth-api", "identity", "tree")),
    ("Before", J("validate", "verify-before", "before")),
]
B = "$MRUN/build"
MULTI_SETUP = [
    ("Split", [(None, M_FIRST)] + M("starter", "starter-v110") + [(f"{B}/priorauth-api", M_SPLIT)] + M("aging-repo", "api-split")
     + [(f"{B}/priorauth-api", M_POM)] + M("api-repo")),
    ("Workspace + remotes", [(None, M_COPY)] + M("workspace-repo", "remote-priorauth-aging", "push-priorauth-aging", "remote-priorauth-api",
                                                 "push-priorauth-api", "remote-priorauth-workspace", "push-priorauth-workspace") + [("$MRUN", "rm -rf build")]),
    ("Clones", M("clone-workspace", "clone-priorauth-aging", "clone-priorauth-api", "identity", "tree")),
    ("Before", M("validate", "verify-before", "bug-before")),
]

JDK_WIN = "/" + archon_step.JDK[0].lower() + archon_step.JDK[2:].replace("\\", "/")
SESSION_WIN = f"""unset ANTHROPIC_API_KEY                # every run on your claude.ai login, never an API key
export ARCHON_TELEMETRY_DISABLED=1
export JAVA_HOME="{JDK_WIN}"   # your JDK 21
export PATH="$JAVA_HOME/bin:$PATH"
# only if Git is not under C:\\Program Files\\Git (the course's was on D:):
export ARCHON_BASH_PATH="D:\\Program Files\\Git\\bin\\bash.exe"
export COURSE=C:/work/ai-dlc-archon JRUN=C:/work/archon-java MRUN=C:/work/archon-multirepo"""
SESSION_MAC = """unset ANTHROPIC_API_KEY                # every run on your claude.ai login, never an API key
export ARCHON_TELEMETRY_DISABLED=1
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
export PATH="$JAVA_HOME/bin:$PATH"
export COURSE=$HOME/work/ai-dlc-archon JRUN=$HOME/work/archon-java MRUN=$HOME/work/archon-multirepo"""

if "--emit" in sys.argv:
    which = sys.argv[sys.argv.index("--emit") + 1]
    groups = JAVA_SETUP if which == "java" else MULTI_SETUP
    sys.stdout.reconfigure(encoding="utf-8")
    print("set -e\n" + "\n".join(script(items) for _, items in groups))
    sys.exit(0)


def jr(*labels):
    return script([JR[label] for label in labels])


def mr(*labels):
    return script([MRS[label] for label in labels])


# The run id and the wait's occurrence, picked out of what the commands print (the same sed, checked on the real output).
RUN_SED = "sed -n 's/^Run id: //p' | tr -d '\\r'"
OCC_SED = """sed -n 's/.*"occurrence": *"\\([^"]*\\)".*/\\1/p' | tr -d '\\r'"""
assert re.search(r"(?m)^Run id: (.*)$", JR["run"]["stdout"]).group(1) == JRID
assert re.findall(r'"occurrence": *"([^"]*)"', JR["wait-1"]["stdout"]) == [OCC]


def started(run_steps, label):
    """The run command, keeping its output and setting RUN from it."""
    c = script([run_steps[label]]).split("\n")
    return "\n".join(c[:-1] + [f"out=$({c[-1]})", 'echo "$out"', f'RUN=$(echo "$out" | {RUN_SED})', 'echo "RUN=$RUN"'])


def link(page_, n, text="the full output and why"):
    return f'<a href="archon-hello-world-java/{page_}.html#s{n:02d}">{text}</a>'


RUNP, TWOP = "archon-hello-world-java-run", "archon-two-repos-run"
S, STEPS, PH = [], [], {}


def add(n, part, color, chip, title, why, who, body, short_):
    assert n == len(S) + 1
    S.append(step(n, part, color, chip, title, why, who, body))
    STEPS.append((n, short_))
    PH[n] = (part, color)


# ================= Part A: your machine =================
A = "Your machine"
pre = PRE
add(1, A, "--setup", "once", "What you need before Archon",
    "Archon drives Claude Code; the runs build and test a Spring Boot repo. Five tools, each checked by one command.", "you · 10 min",
    table(["Tool", "Why", "The course's machine (real)"], [
        ["Claude Code, signed in to claude.ai", "every agent node of a workflow is a Claude Code session", f"<code>{x(pre['claude-version']['stdout'].strip())}</code>"],
        ["git (on Windows: Git for Windows, with Git Bash)", "the workspace and code repos; Git Bash runs every <code>bash:</code> node and every command on this page", f"<code>{x(pre['git-version']['stdout'].strip())}</code><br><code>{x(pre['bash-version']['stdout'].strip())}</code>"],
        ["JDK 21", "priorauth-api is Java 21 (the machine's default java was 11)", f"<code>{x(pre['java-version']['stdout'].splitlines()[0])}</code>"],
        ["Maven 3.9", "<code>scripts/verify.sh</code> is <code>mvn -q test</code>", f"<code>{x(pre['mvn-version']['stdout'].splitlines()[0])}</code>"],
        ["curl", "the hand checks of the packaged jar", f"<code>{x(pre['curl-version']['stdout'].split(' (')[0])}</code>"]])
    + io(cmd("claude --version\ngit --version\nbash --version | head -1\njava -version\nmvn -v | head -1\ncurl --version | head -1"),
         see(x("\n".join([pre["claude-version"]["stdout"].strip(), pre["git-version"]["stdout"].strip(), pre["bash-version"]["stdout"].strip(),
                          pre["java-version"]["stdout"].splitlines()[0], pre["mvn-version"]["stdout"].splitlines()[0], pre["curl-version"]["stdout"].split(" (")[0]])),
             "real · 5 Nov 2026, Windows 10", "Check: you see"))
    + note("Run <code>claude</code> once and sign in with your claude.ai account before anything else: Archon brings no model and no login of its own. On Windows, open <b>Git Bash</b> for every command on this page except the installer; on macOS, Terminal. The macOS commands are the documented equivalents; the course ran on Windows."),
    "What you need")

add(2, A, "--setup", "once", "Install Archon, then check it",
    "One installer, then version and doctor: everything is wired before you spend a token.", "you · 5 min",
    io(you("irm https://archon.diy/install.ps1 | iex", "curl -fsSL https://archon.diy/install | bash", "PowerShell (this one only)", "Terminal"),
       see(x(INSTALL.strip()), f"real · Archon {VERSION}, Windows, provider claude", "The installer returns"), stack=True)
    + io(cmd("archon version\narchon doctor"),
         see(x(CLI["version"]["out"].strip() + "\n…\n" + "\n".join(ln for ln in CLI["doctor"]["out"].splitlines()
                                                                  if any(k in ln for k in ("claude:", "Assistant login", "Database", "Bundled defaults", "All checks passed")))),
             "real", "Check: you see"))
    + note("Open a new terminal after the install: it adds <code>~/.archon/bin</code> to your user PATH. Answer <code>claude</code> when it asks for providers. Every line of both outputs is explained on the <a href='archon-workspace-setup.html#s01'>setup page, steps 1–2</a>."),
    "Install, doctor")

add(3, A, "--setup", "every terminal", "Set up the shell the runs use",
    "Exactly what the course's runner (tools/archon_step.py) set for every command: no API key, telemetry off, JDK 21 first, Git Bash found. Plus three folder names this page uses.", "you · 1 min",
    you(x(SESSION_WIN), x(SESSION_MAC), "Git Bash", "Terminal")
    + table(["Line", "Why"], [
        ["<code>unset ANTHROPIC_API_KEY</code>", "if the key is set, Claude Code may use it instead of your claude.ai login; the course ran every Claude call on the login"],
        ["<code>ARCHON_TELEMETRY_DISABLED=1</code>", "Archon sends anonymous usage events by default (<a href='archon-workspace-setup.html#s03'>what is sent</a>)"],
        ["<code>JAVA_HOME</code>, <code>PATH</code>", "Maven and <code>java -jar</code> must find 21, not an older default"],
        ["<code>ARCHON_BASH_PATH</code>", "Windows only, and only if Git is not where Archon looks (step 4 of Troubleshooting below); <code>archon validate</code> does not catch it"],
        ["<code>COURSE</code>, <code>JRUN</code>, <code>MRUN</code>", "the course clone (next step) and one folder per run: every command below uses them, so a new terminal needs this block again"]], "kv"),
    "The shell")

add(4, A, "--setup", "once", "Get the course's files",
    "The team's files for both runs (workflows, prompts, CLAUDE.md, verify scripts, the request, the bug report) are in the course repo. Clone it once.", "you · 1 min",
    cmd(f'git clone -q {COURSE_URL} "$COURSE"\nls "$COURSE/tools/data/java/files" "$COURSE/tools/data/multirepo/files"')
    + table(["Folder in the course repo", "Becomes"], [
        ["<code>tools/data/java/files/</code>", "the team workspace of Part B: <code>.archon/workflows/team/request-to-pr/</code>, <code>CLAUDE.md</code>, <code>scripts/verify.*</code>, <code>docs-in/request.md</code>, <code>.gitignore</code>, <code>.gitattributes</code>, <code>.archon/config.yaml</code>"],
        ["<code>tools/data/multirepo/files/</code>", "the team workspace of Part C: the same with <code>fix-across-repos</code> and <code>docs-in/bug-report.md</code>"],
        ["<code>archon-hello-world-java/java-workspace/</code>, <code>multirepo-workspace/</code>", "what each workspace looks like after its run and merge: compare yours with them"]], "kv")
    + note("The course repo checks every file out with LF line endings (its <code>.gitattributes</code>), so <code>verify.sh</code> runs under bash even with <code>core.autocrlf=true</code>. To write the files by hand instead, one here-string per file: <a href='archon-workspace-setup.html#s06'>setup page, step 6</a>."),
    "The course's files")

# ================= Part B: one request, one repo =================
P = "One request, one repo"
C = "--build"
g = dict(JAVA_SETUP)
add(5, P, C, "set up", "A remote for the code repo: the public starter",
    "A bare repo on your disk stands in for GitHub, so every push in the run is real and you need no GitHub account. Main only, no tags: tag v1.1.0 is the answer key.", "Meena · 1 min",
    cmd(script(g["Code remote"])) + check(JS["starter-log"], "d9aa178", "0")
    + note("On a real team this is your GitHub repo: skip the bare clone and clone from GitHub in step 7. <code>git tag | wc -l</code> printing <code>0</code> means the agent cannot find the finished answer in the repo."),
    "Code repo's remote")

add(6, P, C, "set up", "The team's workspace: a git repo of its own, pushed",
    "The workspace holds what people wrote for Archon. Copy the team's files, commit them, and push them to a second bare remote.", "Meena · 2 min",
    cmd(script(g["Workspace repo"])) + check(JS["workspace-repo"], "request-to-pr.yaml", "scripts/verify.sh", "docs-in/request.md", extra="\n" + JS["push-java-workspace"]["stdout"].strip())
    + note("<code>git update-index --chmod=+x</code> marks <code>verify.sh</code> executable for every clone (Windows git does not see file modes). Git's <code>LF will be replaced by CRLF</code> warnings are harmless. The files, one by one: <a href='archon-workspace-setup.html#s06'>setup page, step 6</a>."),
    "Workspace repo")

add(7, P, C, "set up", "Kiran's machine: the workspace, then the code repo inside it",
    "Two clones, one folder: the workspace first, priorauth-api inside it. The workspace's .gitignore leaves the code repo out.", "Kiran · 1 min",
    cmd(script(g["Clones"])) + check(JS["identity"], "!! priorauth-api/") + check(JS["tree"], "d9aa178 (HEAD -> main", "<version>1.0.2</version>", tag="real")
    + note("<code>!! priorauth-api/</code>: the workspace's git ignores the code repo, which keeps its own git and remote. The local identity is the one the agent's commits carry; set yours."),
    "Clones")

add(8, P, C, "before", "Before the run: valid, green, and no age yet",
    "The workflow validates, verify.sh passes on v1.0.2 (3 tests), and the pending list has no age field.", "Kiran · 2 min",
    cmd(script(g["Before"])) + check(JS["validate"], "request-to-pr", "Results: 1 valid") + check(JS["verify-before"], "verify: passed", tag="real · verify.sh")
    + see(x(short(JS["before"]["stdout"].strip())), "real · the API at v1.0.2", "Check: you see")
    + note("<code>verify.sh</code> takes a minute or two the first time: Maven downloads its dependencies. The API check builds the jar, starts it on port 8092, calls it once and stops it."),
    "Before the run")

add(9, P, C, "free", "Dry-run the workflow",
    "No model call, no run recorded: the graph walks to its first wait with every agent node stubbed.", "Kiran · 1 min",
    cmd(jr("dry-run")) + check(JR["dry-run"], "STUBBED   scan", "PAUSED    answer (wait)", "Simulation outcome: paused")
    + note("No <code>--folder</code> here: Archon refuses <code>--dry-run</code> with <code>--folder</code> (Part C, step 24, shows the error)."),
    "Dry run")

add(10, P, C, "the run", "Start the run, then wait for its questions",
    "<code>--folder</code> registers the workspace as a folder project and runs in place; <code>--detach</code> returns at once; <code>wait</code> blocks until the run needs a person.", "Kiran · 2 min",
    cmd(started(JR, "run") + "\n" + f'w=$({command(JR["wait-1"])})\necho "$w"\nOCC=$(echo "$w" | {OCC_SED})')
    + check(JR["run"], 'Registered folder project "java-workspace"', "Started 'request-to-pr' in the background.", "Run id:")
    + attention(JR["wait-1"], 4)
    + note(f"<code>RUN</code> is the run id (the course's was <code>{JRID}</code>) and <code>OCC</code> the pause's <code>occurrence</code>: every later command names them, so keep this terminal (or set both again by hand). The scan and the questions took {JR['wait-1']['seconds']:g} s. The seven questions: {link(RUNP, 7, 'run page, step 7')}."),
    "Run, wait")
S[-1] = S[-1].replace("</section>", note('Every agent node of the run (<code>scan</code>, <code>questions</code>, <code>write-requirements</code>, <code>plan</code>, each <code>implement</code> pass, <code>review</code>) is one Claude Code session in this workspace, with your login; the bash nodes and the waits start none. What each workflow field hands that session: <a href="#claude">What each AI node hands Claude Code</a>.') + "</section>", 1)
assert S[-1].count('href="#claude"') == 1

add(11, P, C, "gate 1 · answer", "Answer the seven questions",
    "One message answers all seven; the run goes on to write the requirements and pauses again for their approval.", "Kiran for Ravi and Meena · 2 min",
    cmd(jr("answer-1", "wait-2"))
    + check(JR["answer-1"], "Folder project — running in place (no worktree isolation).", "[write-requirements] Completed", "Workflow paused — waiting for approval.")
    + note(f"<code>answer</code>, <code>approve</code> and <code>reject</code> resume the run <b>in your terminal</b> and return only at the next pause: this one took {JR['answer-1']['seconds']:g} s. Use your own answers if you like; these are the course's, so your run can be compared with its pages ({link(RUNP, 8, 'step 8')})."),
    "Answer")

add(12, P, C, "gate 2 · requirements", "Reject the requirements once, then approve them",
    "A reject at this gate sends its text back to the writer: the loop writes revision 2 with the screen team's names.", "Meena · 3 min",
    cmd(jr("reject-requirements", "wait-3", "approve-requirements", "wait-4"))
    + check(JR["reject-requirements"], "Workflow paused — waiting for approval.") + attention(JR["wait-4"], 3)
    + note(f"Inside a <code>loop_group</code> a reject means \"again, with this\"; at the final gate (step 15) it means stop. Revision 1 and 2 side by side: {link(RUNP, 9, 'steps 9–10')}."),
    "Requirements")

add(13, P, C, "gate 3 · plan", "Approve the plan; implement, checks and review run",
    f"The longest command of the run ({SLOWEST['seconds']:g} s): the implement loop runs until verify.sh passes, a bash node checks the branch, a second agent reviews.", "Meena · 5 min",
    cmd(jr("approve-plan", "wait-5") + "\n" + BRANCH_SET)
    + check(JR["approve-plan"], "Loop node 'implement' completed after 1 iteration", "verify: passed", "a3972b4", "[review] Completed")
    + attention(JR["wait-5"], 1)
    + note(f"The agent made branch <code>request-age/pending-age</code> in priorauth-api and committed there; Archon made no branch or worktree. <code>BRANCH</code> keeps the name it chose for steps 16–18: in the re-run from this page it was <code>{RERUN['branch']}</code>. The review's verdict and the diff: {link(RUNP, 12, 'step 12')}."),
    "Plan, implement")

add(14, P, C, "by hand", "Check the packaged jar by hand",
    "Tests passed and the review said READY. Run the real jar on three dates before the last approval.", "Kiran · 1 min",
    cmd(jr("jar-check"))
    + see(x(short("\n".join(ln for ln in text_of(JR["jar-check"]).splitlines() if ln.startswith(("$ curl", "HTTP/1.1", "[{"))), 120)), "real · 10 s", "Check: you see")
    + note(f"7 OVER 5 / 4 / 1 as Ravi expects, an as-of before a received date is 400, but <code>asOf=+999999999-12-31</code> is a <b>500</b>. That is the reason for the next two steps ({link(RUNP, 13, 'step 13')}). In the re-run from this page the same date never answered: the code looped, using a full CPU core, so each curl now gives up after 20 s (<code>--max-time 20</code>) and prints nothing for that date. A hang is a defect too; reject it the same way."),
    "Jar check: a 500")

add(15, P, C, "gate 4 · change", "Reject the change: the run is cancelled",
    "At the last gate a reject runs <code>stop-change</code>. The CLI's message about resuming is misleading: the run is over, and the rejection is recorded.", "Meena · 1 min",
    cmd(jr("reject-change"))
    + check(JR["reject-change"], "Workflow cancelled", "Cost: $3.73", "Rejected but failed to resume", "bun run cli workflow resume")
    + note("Don't run the suggested <code>bun run cli workflow resume</code>: it is the source checkout's command, and there is nothing to resume. The fix is a new run that adopts this one. The reject text is the course's: say what your jar check showed (a 500, or no answer)."),
    "Reject: cancelled")

add(16, P, C, "the fix", "Fix it with <code>archon-implement</code>, adopting the run",
    "The bundled <code>archon-implement</code>, with Meena's decision as the message, on the same branch. Then verify and the jar again.", "Kiran · 3 min",
    cmd(jr("fix-run", "verify-fix", "jar-check-2"))
    + check(JR["fix-run"], "folder projects run in place; adoption carries provenance and $ADOPTED_RUN_DIR access only.", "Loop node 'implement' completed after 1 iteration", "Cost: $0.62")
    + check(JR["verify-fix"], "verify: passed", "RequestAgingTest", "PendingRequestsControllerTest", "RequestStoreTest", tag="real · 21 tests")
    + see(x("\n".join(ln for ln in text_of(JR["jar-check-2"]).splitlines() if ln.startswith(("$ curl", "HTTP/1.1")))), "real · both bad dates now 400", "Check: you see")
    + note(f"Write the decision into the message, naming what you saw; it names <code>$BRANCH</code>, so the agent stays on the right branch. An adopted run can read the old run's files through <code>$ADOPTED_RUN_DIR</code>, but it does not inherit the reject text. Commit <code>4ea9e9d</code>: {link(RUNP, 15, 'step 15')}."),
    "Fix (adopt)")

add(17, P, C, "ship", "Push by hand, and look at what the run left",
    "The run was cancelled before its push node, so Kiran pushes. Then the read-only commands: runs, the run, its artifacts and log, the project, doctor.", "Kiran · 2 min",
    cmd(jr("push-by-hand", "runs", "get", "artifacts", "logs-text", "project-list", "isolation-list", "doctor", "remote-branch"))
    + check(JR["push-by-hand"], "[new branch]      request-age/pending-age")
    + check(JR["get"], "Status: cancelled", "Cost: $3.73", "Worktree:", "Adopted by:", tag="real · workflow get")
    + check(JR["isolation-list"], "No codebases registered.", tag="real · isolation list")
    + check(JR["doctor"], '"java-workspace" (runs in place) — 1 contained repo(s): priorauth-api', tag="real · doctor")
    + note(f"\"Worktree … (live)\" is the workspace itself: a folder project has no worktree. Open the PR from <code>request-age/pending-age</code> now (the course had no <code>gh</code> login, so step 18 merges by hand). Every output: {link(RUNP, 16, 'steps 16–17')}."),
    "Push, inspect")

add(18, P, C, "after", "Merge, then tidy up by hand",
    "Meena's merge stands in for the PR merge. archon complete finds nothing to clean in a folder project; verify on main; Kiran deletes his branch.", "Meena, Kiran · 2 min",
    cmd(jr("merge", "complete", "verify-main", "cleanup"))
    + check(JR["merge"], "Merge request-age/pending-age", "4ea9e9d", "a3972b4", tag="real · git log --graph")
    + check(JR["complete"], "no active isolation environment", tag="real · archon complete")
    + check(JR["verify-main"], "verify on main: passed", "workspace clean", tag="real")
    + check(JR["cleanup"], "Deleted branch request-age/pending-age", tag="real"),
    "Merge, tidy")

add(19, P, C, "optional", "The same request through the bundled archon-plan",
    "On main after the merge, Archon's own planner finds the request already met and stops without a pause.", "Kiran · 3 min",
    cmd(jr("archon-plan")) + check(JR["archon-plan"], "Loop-group node 'cycle' completed after 1 iteration", "Status: completed", "Cost: $0.82")
    + note(f"Its summary names the merge commit (<code>4ca6b6a</code>) and plans no change. A plan before the change, and how it compares: {link(RUNP, 19, 'step 19')}."),
    "archon-plan")

# ================= Part C: one bug, two repos =================
P = "One bug, two repos"
C = "--review"
g = dict(MULTI_SETUP)
add(20, P, C, "set up", "Split the starter: a library and an API",
    "The course's bug spans two repos, so the starter at v1.1.0 is split: the aging package becomes priorauth-aging 1.0.0, and priorauth-api 1.2.0 depends on it.", "Meena · 2 min",
    cmd(script(g["Split"]))
    + check(MS["starter-v110"], "49fe266") + check(MS["aging-repo"], "priorauth-aging 1.0.0", tag="real") + check(MS["api-repo"], "c2dc5d4", tag="real")
    + note("The copy, the two heredocs and the <code>awk</code> pom edit are what <code>tools/setup_multirepo_run.py</code> did in Python; written as shell they give the same trees as the course's remotes, byte for byte (checked with <code>git rev-parse v1.2.0^{tree}</code>); your commit ids differ, because commits carry their date. The six moved files: "
           + ", ".join(f"<code>{x(Path(f).name)}</code>" for f in MOVED) + "."),
    "Split the starter")

add(21, P, C, "set up", "The workspace repo, and three remotes",
    "The team's files for the two-repo run, committed; a bare remote each for the library, the API and the workspace, pushed with their tags.", "Meena · 1 min",
    cmd(script(g["Workspace + remotes"])) + check(MS["workspace-repo"], "fix-across-repos.yaml", "docs-in/bug-report.md", "docs-in/holidays-TX-01-2027.json"),
    "Workspace, remotes")

add(22, P, C, "set up", "Kiran's machine: the workspace, then each repo inside it",
    "Three clones in one folder. CLAUDE.md is the repo map: which repo holds what, the release order, git per repo.", "Kiran · 1 min",
    cmd(script(g["Clones"])) + check(MS["identity"], "!! priorauth-aging/", "!! priorauth-api/")
    + check(MS["tree"], "tag: v1.0.0", "tag: v1.2.0", "<version>1.0.0</version>", "<version>1.2.0</version>", tag="real"),
    "Clones")

add(23, P, C, "before", "Before the run: it builds, and the bug shows",
    "verify.sh installs the library, then tests the API. The jar on 2027-01-05 gives 63/60/57: New Year's Day counted as a working day.", "Kiran · 3 min",
    cmd(script(g["Before"])) + check(MS["validate"], "fix-across-repos", "Results: 1 valid") + check(MS["verify-before"], "verify: passed", tag="real · verify.sh")
    + see(x(short(MS["bug-before"]["stdout"].strip(), 400)), "real · the 1.2.0 jar, asOf=2027-01-05", "Check: you see")
    + note("Ravi's bug report (<code>docs-in/bug-report.md</code>) says the ages are one too high; the 2027 holiday file he attached is <code>docs-in/holidays-TX-01-2027.json</code>."),
    "Before: the bug")

add(24, P, C, "free", "Dry-run it: not with <code>--folder</code>",
    "The first try is refused; a plain dry run works and registers nothing.", "Kiran · 1 min",
    cmd(mr("dry-run", "dry-run-plain")) + check(MRS["dry-run"], "Error: --dry-run cannot be combined with --folder.")
    + check(MRS["dry-run-plain"], "PAUSED    approve-plan (wait)", "Simulation outcome: paused", tag="real"),
    "Dry run")

add(25, P, C, "gate 1 · plan", "Start the run; approve the plan with a correction",
    "Scan and plan find the cause in the library. The plan miscounts two ages; Meena approves with the right numbers instead of rejecting (a reject here cancels).", "Kiran, Meena · 6 min",
    cmd(started(MRS, "run") + "\n" + "\n".join(command(MRS[label]) for label in ("wait-1", "approve-plan", "wait-2")) + "\n" + BRANCH_SET)
    + check(MRS["run"], 'Registered folder project "priorauth-workspace"', "Run id:")
    + attention(MRS["wait-1"], 3)
    + check(MRS["approve-plan"], "Loop node 'implement' completed after 1 iteration", "074d524", "8d65a37", "Workflow paused — waiting for approval.", tag=f"real · {MRS['approve-plan']['seconds']:g} s")
    + note(f"The course's run id was <code>{MRID}</code>. One branch, <code>fix/holidays-across-years</code>, in each repo, made and committed by the agent. Why approve-with-correction and not reject: {link(TWOP, 9, 'two-repo page, step 9')}."),
    "Run, plan")

add(26, P, C, "gate 2 · change", "Check the jar by hand, then approve: one branch pushed per repo",
    "The 1.2.1 jar carries priorauth-aging 1.0.1 and gives 62/59/56 on 2027-01-05, still 7/4/1 on 2026-10-13. Approve, and the push node pushes both branches.", "Kiran, Meena · 2 min",
    cmd(mr("jar-check", "approve-change"))
    + see(x(short("\n".join(ln for ln in text_of(MRS["jar-check"]).splitlines() if ln.startswith(("BOOT-INF", "asOf", "[{"))), 210)), "real · 10 s", "Check: you see")
    + check(MRS["approve-change"], "priorauth-aging: open the PR fix/holidays-across-years -> main", "priorauth-api: open the PR fix/holidays-across-years -> main",
            "Workflow completed successfully.", "Cost: $2.14", tag="real"),
    "Jar, approve, push")

add(27, P, C, "after", "What a folder project leaves behind",
    "Archon's view of the finished run, and the two branches on the remotes.", "Kiran · 1 min",
    cmd(mr("get", "artifacts", "logs-text", "project-list", "isolation-list", "doctor", "remote-branches"))
    + check(MRS["get"], "Status: completed", "Worktree:", tag="real · workflow get")
    + check(MRS["doctor"], "2 contained repo(s): priorauth-aging, priorauth-api", tag="real · doctor")
    + check(MRS["remote-branches"], "refs/heads/fix/holidays-across-years", tag="real"),
    "Inspect")

add(28, P, C, "after", "Merge in release order; tidy up by hand",
    "The library first (tag v1.0.1), then the API (v1.2.1). verify on main, then delete the branches.", "Meena, Kiran · 2 min",
    cmd('rm -rf "$MRUN/meena" && mkdir -p "$MRUN/meena"\n' + mr("merge", "complete", "after-merge", "cleanup"))
    + check(MRS["merge"], "== priorauth-aging", "317874b", "== priorauth-api", "e7b9a6d", tag="real")
    + check(MRS["after-merge"], "v1.0.1", "v1.2.1", "verify on main: passed", "workspace clean", tag="real")
    + check(MRS["cleanup"], "Deleted branch fix/holidays-across-years", tag="real")
    + note(f"Open both PRs before this on a real team; merge the library's first, because the API's pom names its new version. The same bug through AWS AI-DLC: {link(TWOP, 16, 'two-repo page, step 16')}."),
    "Merge, tidy")

# ================= reference =================
TROUBLE = [
    ["<code>bash executable not found at 'C:\\Program Files\\Git\\bin\\bash.exe'</code>, on the first bash node",
     "Git for Windows is installed somewhere Archon doesn't look; <code>archon validate</code> passes anyway (measured)",
     "<code>export ARCHON_BASH_PATH=\"&lt;your Git&gt;\\bin\\bash.exe\"</code> (step 3), or set it as a user variable"],
    ["<code>Error: --dry-run cannot be combined with --folder.</code>", "measured, step 24", "dry-run without <code>--folder</code>"],
    ["<code>answer</code> / <code>approve</code> seems to hang", f"it resumes the run in your terminal until the next pause (up to {SLOWEST['seconds']:g} s here)", "wait; or follow the transcript path <code>run</code> printed"],
    ["<code>Rejected but failed to resume … bun run cli workflow resume</code>", "a reject at the last gate cancels the run; the message is misleading (measured, step 15)", "start a new run with <code>--adopt $RUN</code> (step 16)"],
    ["An adopted run doesn't know what was decided", "it gets the old run's files via <code>$ADOPTED_RUN_DIR</code>, not the reject text", "write the decision into the new run's message"],
    ["<code>archon complete &lt;branch&gt;</code>: <code>Not found … no active isolation environment</code>", "expected: a folder project has no worktree to clean", "delete the branches yourself (steps 18, 28)"],
    ["<code>mvn</code> fails inside the agent's session with <code>ClassNotFoundException: …Launcher</code>", "seen in the two-repo run: Git Bash's <code>mvn</code> broke in the agent's shell; the agent ran <code>verify.cmd</code> and said so", "nothing to do; the checks node ran <code>verify.sh</code> and passed"],
    ["<code>verify.sh: $'\\r': command not found</code>", "the script got CRLF endings (<code>core.autocrlf=true</code>)", "keep the team's <code>.gitattributes</code> (<code>*.sh text eol=lf</code>); not hit in the course"],
    ["<code>release version 21 not supported</code> from Maven", "an older JDK first on PATH", "step 3's <code>JAVA_HOME</code> and <code>PATH</code>; not hit in the course"],
    ["the jar check prints nothing for <code>asOf=%2B999999999-12-31</code>", "measured in the re-run from this page: the code looped on the far date, using a full CPU core; before <code>--max-time</code> the curl waited 18 min", "a defect like the 500: reject (step 15) and say so in the fix's message"],
    [f"<code>{RERUN['guide_failed']['step 17']}</code>", f"the agent named the branch differently (measured: <code>{RERUN['branch']}</code>) and a command had the course's name", "use <code>$BRANCH</code> from step 13 (25), as every command here now does"],
    [f"the first run registers <code>{RERUN['project']}</code>, not <code>java-workspace</code>", "a folder project with that name already exists (an earlier run from another folder; measured)", "harmless: runs are kept per project"],
    ["the jar check can't start: port in use", "an earlier java is still running on 8091–8093", "stop it, or change <code>--server.port</code>"],
    ["<code>archon project list</code> shows old projects", "there is no <code>project remove</code> in 0.13.2 (the course's list has an older <code>_local/priorauth-api</code>)", "harmless; each run names its project"],
]
# What each AI node hands Claude Code: the shared mapping (asserted against tools/data/docs/), and what both runs' sessions did.
claude_facts()


def _sessions(log, rid):
    """The (node, session origin) of each agent/loop node start, and the tool calls, of one run's transcript."""
    starts, tools = [], {}
    for ln in log.read_text(encoding="utf-8").splitlines():
        d = json.loads(ln)
        if d.get("workflow_id") != rid:
            continue
        if d.get("type") == "node_start" and d["execution"]["node"]["kind"] in ("agent", "loop"):
            starts.append(d["step"])
        if d.get("type") == "provider_event" and d["event"].get("type") == "tool_call":
            tools[d["event"]["name"]] = tools.get(d["event"]["name"], 0) + 1
    assert starts and not set(tools) & {"Skill", "Task", "Agent"}, (rid, tools)
    return starts, tools


CC_RUNS = []
for _label, _dir, _rid, _wf, _ws in [("One request, one repo · <code>request-to-pr</code>", "java-run", JRID, "tools/data/java/files/.archon/workflows/team/request-to-pr/request-to-pr.yaml", "java-workspace"),
                                     ("One bug, two repos · <code>fix-across-repos</code>", "multirepo-run", MRID, "tools/data/multirepo/files/.archon/workflows/team/fix-across-repos/fix-across-repos.yaml", "multirepo-workspace")]:
    _log = next((HW / _dir / "logs").glob(f"{_rid}*.jsonl"))
    _starts, _tools = _sessions(_log, _rid)
    assert not re.search(r"^\s*(skills|agents|hooks|mcp|plugins):", (ROOT / _wf).read_text(encoding="utf-8"), re.M)
    assert not (HW / _ws / ".claude").exists() and (HW / _ws / "CLAUDE.md").exists()
    CC_RUNS.append([_label, f"{len(_starts)}: " + ", ".join(f"<code>{n}</code>" for n in _starts),
                    ", ".join(f"{k} {v}" for k, v in sorted(_tools.items(), key=lambda kv: -kv[1]))])
ref_claude = card("claude", "What each AI node hands Claude Code",
                  "<p>Archon's Claude provider uses the Claude Agent SDK, which starts Claude Code as a background process: <b>each agent node, and each loop pass, is one Claude Code session</b> in the workspace, with your claude.ai login. The node's fields decide what that session gets. The third column is the request-to-pr run (Part B).</p>"
                  + table(["In the workflow", "What Claude Code gets", "In the course's run"], [list(r_) for r_ in CLAUDE_MAP], "kv")
                  + "<p style=\"margin-top:14px\"><b>What the two runs' sessions did</b>, from their transcripts (real):</p>"
                  + table(["Run", "AI node runs, in order", "Tool calls"], CC_RUNS)
                  + note("Neither workflow names <code>skills:</code>, <code>agents:</code>, <code>hooks:</code> or <code>mcp:</code>, and neither workspace has a <code>.claude/</code> folder, so no session called <code>Skill</code> or <code>Task</code>: the one Claude Code file both runs relied on is the workspace's <code>CLAUDE.md</code>. Your own <code>~/.claude/</code> (its <code>CLAUDE.md</code>, agents and hooks) loads too unless <code>.archon/config.yaml</code> sets <code>settingSources: [project]</code> under <code>assistants.claude</code>. More: <a href=\"archon-introduction.html#s11\">the introduction, step 11</a>."))

ref_trouble = card("trouble", "Troubleshooting", "<p>Every symptom marked measured happened in the course's runs; the rest are what the setup guards against.</p>"
                   + table(["You see", "Why", "Do"], TROUBLE))
ref_cost = card("cost", "What it cost, how long it took", "<p>Reported by Archon at the end of each run (API-price equivalents; the course ran on a claude.ai plan, so nothing was billed per token). Time is the sum of the recorded commands, waits included.</p>"
                + table(["Run", "Workflow", "Reported cost", "Commands, in total"], [
                    ["One request, one repo", "<code>request-to-pr</code> (cancelled at the last gate)", f"${COST['request-to-pr']:.2f}", f"{MIN['java']} min, with the fix and archon-plan"],
                    ["", "<code>archon-implement</code> (the fix)", f"${COST['archon-implement']:.2f}", ""],
                    ["", "<code>archon-plan</code> (optional)", f"${COST['archon-plan']:.2f}", ""],
                    ["One bug, two repos", "<code>fix-across-repos</code>", f"${COST['fix-across-repos']:.2f}", f"{MIN['multirepo']} min"]]))
ref_again = card("again", "Start over", "<p>Each run's folders can be deleted and rebuilt from step 5 or step 20. Archon keeps the runs under <code>~/.archon/workspaces/_folder/&lt;workspace&gt;/</code> and the project in its database; a new first run from the same path reuses the project.</p>"
                 + cmd('rm -rf "$JRUN" "$MRUN"\narchon project list'))
R = RERUN
assert R["guards_ok"] == ["answer", "requirements.review-requirements", "approve-plan", "approve-change", "approve-change"]
assert R["jar_check_2_codes"] == ["200", "400", "400"] and R["fix_green"] and R["review"] == "READY" and R["requirements_iterations"] == 2
ref_rerun = card("rerun", "Re-run from this page", f"<p>On {R['date']} every command box of steps 3–19, as first published, ran in order in one Git Bash session in a fresh folder, with the same answers and decisions. Before each gate a check stopped the script if the run was paused anywhere else; it never was. The agents wrote other code, so the details differ, and the guide's commands changed where they had assumed the 4 Nov run's details.</p>"
    + table(["Step", "4 Nov (the Check boxes)", "6 Nov, from this page"], [
        ["10 · the project", "<code>java-workspace</code>", f"<code>{R['project']}</code> (the name was taken)"],
        ["12 · requirements", "rejected once, approved on revision 2", f"the same: {R['requirements_iterations']} iterations"],
        ["13 · branch, commit", "<code>request-age/pending-age</code>, <code>a3972b4</code>", f"<code>{R['branch']}</code>, <code>{R['commits']['feature']}</code>; review {R['review']}"],
        ["14 · far-future date", "500", "no answer: a busy loop, stopped by hand after 18 min"],
        ["16 · the fix", "<code>4ea9e9d</code>, both bad dates 400", f"<code>{R['commits']['fix']}</code>, codes {' / '.join(R['jar_check_2_codes'])}"],
        ["17–18 · push, merge, tidy", "worked", f"<b>failed</b>: the course's branch name was hardcoded (now <code>$BRANCH</code>); finished by hand with the fixed commands: merge <code>{R['finished_by_hand']['merge']}</code>, verify on main passed, {R['finished_by_hand']['tests_on_main']} tests"],
        ["18 · verify on main", "passed, 21 tests", "printed passed on the unmerged main, listing stale test reports; the step now deletes <code>target/</code> first"],
        ["reported cost", "$3.73 + $0.63 + $0.83", f"${R['costs']['request-to-pr']:.2f} + ${R['costs']['archon-implement']:.2f} + ${R['costs']['archon-plan']:.2f}"]])
    + "<p>The fixes are in every command above: <code>$BRANCH</code> (steps 13, 16–18, 25, 28), <code>--max-time 20</code> on the jar checks, <code>rm -rf priorauth-api/target</code> before verify on main, and merge steps that clear an earlier attempt's clone. Part C was not re-run end to end; its setup was (steps 20–23).</p>")
real = card("real", "What is real here", f"<p>Every command and every Check box is from the course's real runs with Archon {VERSION} and Claude Code on a claude.ai login, Windows 10, 4 Nov 2026 (the tool versions in step 1: 5 Nov). The commands are the recorded ones, changed where the re-run from this page (6 Nov) showed they depended on that run's details (<a href='#rerun'>Re-run from this page</a>), and with the run folders written as <code>$JRUN</code>/<code>$MRUN</code>, the run id as <code>$RUN</code>, and the recorded multi-line scripts in a subshell; the file copies and the starter split are the course's setup scripts written as shell, and Parts B and C's setup (steps 5–8, 20–23) was re-run from this page in a fresh folder on 5 Nov 2026: same trees as the course's remotes, same checks. Commit ids other than the starter's (<code>d9aa178</code>, <code>49fe266</code>) will differ on your machine. The macOS commands were not run. Your agent will word things differently, and may take another number of passes; the gates are where you decide. The cast (Ravi Menon, Kiran Rao, Meena Iyer) is fictional.</p>")

hero = f'''<section class="hero" id="top">
  <div>
    <h1>Archon, end to end: from a bare machine to two merged changes.</h1>
    <p class="lead">Everything the course's two real runs did, in order, at a keyboard: install and check the tools, set up the shell, then <b>one request in one repo</b> (Ravi's request-age feature through <code>request-to-pr</code>) and <b>one bug across two repos</b> (New Year's Day, through <code>fix-across-repos</code>). Every setup command is here, each followed by what the real run printed. Archon {VERSION}, Claude Code, Windows (Git Bash) and macOS.</p>
    <div class="facts">
      <div><b>{len(S)}</b>steps, every command included</div>
      <div><b>2</b>real runs, {MIN['java'] + MIN['multirepo']} min of commands</div>
      <div><b>6</b>gates answered by people</div>
      <div><b>3</b>repos, all with local remotes</div>
      <div><b>${sum(COST.values()):.2f}</b>reported, four runs</div>
      <div><b>0</b>GitHub accounts needed</div>
    </div>
  </div>
  <aside class="slack" aria-label="The path">
    <div class="slack__bar"><span>The path</span><span>{len(S)} steps</span></div>
    <div class="slack__body">
      <p style="margin:0 0 8px"><b>A · Your machine</b> (1–4)<br><span style="color:var(--ink-3)">Tools, Archon, the shell, the course's files. Once.</span></p>
      <p style="margin:0 0 8px"><b>B · One request, one repo</b> (5–19)<br><span style="color:var(--ink-3)">Remotes, workspace, four gates, a 500 found by hand, a fix, the merge.</span></p>
      <p style="margin:0"><b>C · One bug, two repos</b> (20–28)<br><span style="color:var(--ink-3)">Split the starter, two gates, a branch per repo, merge in release order.</span></p>
    </div>
  </aside>
</section>
'''
assert len(S) == 28
main = (hero + phase("--setup", "A · Your machine", "steps 1–4 · once per machine (step 3 in every terminal)") + "".join(S[0:4])
        + phase("--build", "B · One request, one repo", f"steps 5–19 · request-to-pr in java-workspace/ · the story: <a href='archon-hello-world-java/{RUNP}.html'>run page</a>")
        + "".join(S[4:19])
        + phase("--review", "C · One bug, two repos", f"steps 20–28 · fix-across-repos in priorauth-workspace/ · the story: <a href='archon-hello-world-java/{TWOP}.html'>two-repo page</a>")
        + "".join(S[19:28])
        + phase("--ship", "Reference", "what Claude Code gets, troubleshooting, cost, start over") + ref_claude + ref_trouble + ref_cost + ref_again + ref_rerun + real
        + plain("A stays done; B and C are independent. Each starts from an empty folder and ends with the change merged and verified on main, so you can run either one alone (after A), or both."))
footer = ('<footer class="foot">Archon end to end · Archon ' + VERSION + ' · <a href="archon-workspace-setup.html">setup, explained</a> · '
          f'<a href="archon-hello-world-java/{RUNP}.html">one request, one repo</a> · <a href="archon-hello-world-java/{TWOP}.html">one bug, two repos</a> · '
          '<a href="index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Archon End to End", f"Every command of the course's two real Archon {VERSION} runs, from installing the tools to the merge: one request in one repo, one bug across two repos, with the real output after each step.",
             "Archon end to end", "machine · one request · one bug · real output", len(STEPS),
             rail(STEPS, PH, [("claude", "What Claude Code gets"), ("trouble", "Troubleshooting"), ("cost", "Cost and time"), ("again", "Start over"), ("rerun", "Re-run from this page"), ("real", "What is real here")]), main, footer)
write(ROOT / "archon-end-to-end-guide.html", html_)
