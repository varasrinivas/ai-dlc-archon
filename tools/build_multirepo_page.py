"""Build archon-hello-world-java/archon-two-repos-run.html: one bug fixed across two repos with an Archon folder project.

Everything comes from the course's real two-repo run (4 Nov 2026, Archon 0.13.2, Claude Code on a claude.ai login),
copied into archon-hello-world-java/multirepo-run/ by capture_multirepo_run.py: setup-steps.json and steps.json (every
command and what came back), nodes.json (per node: time, tokens, cost), artifacts/ (what the run wrote), git/<repo>/
(each repo's commits and diffs), storage.txt (the folder project's folders under ~/.archon). The team's files are
tools/data/multirepo/files/. The asserts tie the page's numbers to that data.

Usage: py -3.12 tools/build_multirepo_page.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli_parse import workflow_nodes  # noqa: E402
from diagrams import workflow_dag  # noqa: E402
from pagekit import (CLAUDE_MAP, E, ROOT, card, claude_facts, disk, gate, io, multirepo_facts, note, page, phase, plain, rail, see, shell_group,  # noqa: E402
                     step, table, tabs, write, you)
from setup_multirepo_run import AGING_POM, AGING_README, API_DEP  # noqa: E402

DEST = ROOT / "archon-hello-world-java"
RUN = DEST / "multirepo-run"
FILES = ROOT / "tools" / "data" / "multirepo" / "files"
S = {s["label"]: s for s in json.loads((RUN / "steps.json").read_text(encoding="utf-8"))}
SETUP = {s["label"]: s for s in json.loads((RUN / "setup-steps.json").read_text(encoding="utf-8"))}
NODES = json.loads((RUN / "nodes.json").read_text(encoding="utf-8"))
RID = "5138e1be8e01d39ed631d192df3bb2c1"
ART = RUN / "artifacts" / RID
WF_PATH = ".archon/workflows/team/fix-across-repos/fix-across-repos.yaml"
WF_TEXT = (FILES / WF_PATH).read_text(encoding="utf-8")
WFN = workflow_nodes(WF_TEXT)
CLI = json.loads((ROOT / "tools/data/cli/cli.json").read_text(encoding="utf-8"))
REPOS = ("priorauth-aging", "priorauth-api")
GIT = {r: RUN / "git" / r for r in REPOS}
PATCH = {r: next(GIT[r].glob("commit-*.patch")) for r in REPOS}
COMMIT = {r: PATCH[r].stem.split("-")[1] for r in REPOS}
STAT = {r: (GIT[r] / "diffstat.txt").read_text(encoding="utf-8").strip() for r in REPOS}

# ---------- facts the page states, checked against the data ----------
multirepo_facts(CLI)
assert NODES[RID]["workflow"] == "fix-across-repos"
assert len(WFN) == 10 and sum(1 for n in WFN if n["kind"] == "wait") == 2
assert "fix-across-repos                         ok" in SETUP["validate"]["stdout"]
assert "verify: passed" in SETUP["verify-before"]["stdout"]
BEFORE = SETUP["bug-before"]["stdout"]
for a in ('"id":"PA-10231"', '"ageBusinessDays":63', '"ageBusinessDays":60', '"ageBusinessDays":57'):
    assert a in BEFORE, a
assert "--dry-run cannot be combined with --folder" in S["dry-run"]["stderr"]
assert "Simulation outcome: paused" in S["dry-run-plain"]["stdout"] and "PAUSED    approve-plan (wait)" in S["dry-run-plain"]["stdout"]
assert 'Registered folder project "priorauth-workspace"' in S["run"]["stdout"] and f"Run id: {RID}" in S["run"]["stdout"]
assert "_folder" in S["run"]["stdout"]
W1 = json.loads(S["wait-1"]["stdout"])["attention"]
assert W1["nodeId"] == "approve-plan" and "fix/holidays-across-years" in W1["message"] and "62 bd" in W1["message"]
assert "PA-10244 60 bd and PA-10263 57 bd" in W1["message"], "the plan's miscount that Meena corrected"
APP_PLAN = S["approve-plan"]["cmd"].split(RID + " ", 1)[1]
assert "PA-10244 59, PA-10263 56" in APP_PLAN
assert "Folder project — running in place (no worktree isolation)." in S["approve-plan"]["stdout"]
assert "Loop node 'implement' completed after 1 iteration" in S["approve-plan"]["stdout"]
W2 = json.loads(S["wait-2"]["stdout"])["attention"]
assert W2["nodeId"] == "approve-change" and W2["message"].startswith("Review verdict: READY")
assert "the API test expects 62 / 59 / 56; the plan said 62 / 60 / 57" in W2["message"]
JAR = S["jar-check"]["stdout"]
assert "BOOT-INF/lib/priorauth-aging-1.0.1.jar" in JAR
for a in ('"ageBusinessDays":62', '"ageBusinessDays":59', '"ageBusinessDays":56', '"ageBusinessDays":7,', '"ageBusinessDays":4,', '"ageBusinessDays":1,'):
    assert a in JAR, a
APP_CHANGE = S["approve-change"]["cmd"].split(RID + " ", 1)[1]
PUSH = S["approve-change"]["stdout"]
for r in REPOS:
    assert f"{r}: open the PR fix/holidays-across-years -> main" in PUSH
assert "Workflow completed successfully." in PUSH
assert "Status: completed" in S["get"]["stdout"] and "(live)" in S["get"]["stdout"]
assert "folder\tpriorauth-workspace\t_folder/priorauth-workspace" in S["project-list"]["stdout"]
assert "No codebases registered." in S["isolation-list"]["stdout"]
assert '2 contained repo(s): priorauth-aging, priorauth-api' in S["doctor"]["stdout"]
assert "no active isolation environment" in S["complete"]["stdout"]
assert "verify on main: passed" in S["after-merge"]["stdout"] and "workspace clean" in S["after-merge"]["stdout"]
assert "v1.0.1" in S["after-merge"]["stdout"] and "v1.2.1" in S["after-merge"]["stdout"]
assert S["cleanup"]["stdout"].count("Deleted branch fix/holidays-across-years") == 2
for r in REPOS:
    assert COMMIT[r] in S["remote-branches"]["stdout"], r
# The AI-DLC course's run of the same bug on the same two repos (step 16), checked when that course is checked out next to this one.
AIDLC = ROOT.parent / "ai-dlc-execution" / "aidlc-hello-world-java" / "graphify-multirepo-run"
if AIDLC.exists():
    _ad = {f: (AIDLC / f).read_text(encoding="utf-8") for f in ("aging.diff", "api.diff", "code-log.txt", "workspace-log.txt")}
    assert "+  <version>2.0.0</version>" in _ad["aging.diff"] and "+    public Set<LocalDate> forTenant(String tenantId, LocalDate receivedAt, LocalDate asOf) {" in _ad["aging.diff"]
    assert "+  <version>1.2.1</version>" in _ad["api.diff"] and "+      <version>2.0.0</version>" in _ad["api.diff"] and "PendingRequestsController.java" in _ad["api.diff"]
    assert all(f'ageBusinessDays").value({n})' in _ad["api.diff"] for n in (62, 59, 56))
    assert _ad["code-log.txt"].count("(HEAD -> request-age/new-year-holiday)") == 2
    assert all(s in _ad["workspace-log.txt"] for s in ("Reverse Engineering approved (Kiran Rao)", "Code Generation approved (Meena Iyer)", "Build and Test approved (Meena Iyer)"))
assert "+  <version>1.0.1</version>" in PATCH["priorauth-aging"].read_text(encoding="utf-8")
assert "holidays-TX-01-2027.json" in STAT["priorauth-aging"]
API_PATCH = PATCH["priorauth-api"].read_text(encoding="utf-8")
assert "+  <version>1.2.1</version>" in API_PATCH and "+      <version>1.0.1</version>" in API_PATCH
assert "src/main" not in STAT["priorauth-api"], "the API's code did not change"
ROWS = [n for n in NODES[RID]["nodes"] if n["event"] == "node_complete"]
COST = sum(n["cost"] or 0 for n in ROWS)
assert abs(COST - 2.1466) < 0.01, COST
assert "$2.1466047" in PUSH
AI_ROWS = [n for n in ROWS if n["cost"]]
assert [n["node"] for n in AI_ROWS] == ["scan", "plan", "implement", "review"]
IMPL = (ART / "implementation.md").read_text(encoding="utf-8")
assert "ClassNotFoundException: org.codehaus.plexus.classworlds.launcher.Launcher" in IMPL
STORAGE = (RUN / "storage.txt").read_text(encoding="utf-8")
for d in ("_folder/priorauth-workspace/artifacts/", "_folder/priorauth-workspace/logs/", "_folder/priorauth-workspace/workflow-source/"):
    assert d in STORAGE, d
assert "worktrees" not in STORAGE


def x(s):
    return E(s)


def fold(t):
    """Fold Spring Boot's test log and banner out of an output."""
    out, n = [], 0
    for line in t.splitlines():
        if re.match(r"^\s*(20\d\d-\d\d-\d\dT|\d\d:\d\d:\d\d\.\d+ \[main\]|\s*\.\s+____|\s*/\\\\|\s*\( \(|\s*\\\\/|\s*'  \||\s*=+\|_\||\s*:: Spring Boot)", line):
            n += 1
            continue
        if n:
            out.append(f"… ({n} lines of the Spring Boot test log)")
            n = 0
        out.append(line)
    if n:
        out.append(f"… ({n} lines of the Spring Boot test log)")
    return "\n".join(out)


def nd(node):
    return next(n for n in ROWS if n["node"] == node)


def chip(node):
    r = nd(node)
    s = round((r["ms"] or 0) / 1000)
    t = f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"
    return t + (f" · ${r['cost']:.2f}" if r["cost"] else "")


def cmd(win, mac=None, tag="PowerShell", mac_tag="Terminal"):
    return you(x(win), x(mac if mac is not None else win), tag, mac_tag if mac is not None else tag)


def progress(label):
    return "\n".join(ln for ln in S[label]["stderr"].splitlines() if re.match(r"^\[(?!workflow)[\w-]+\] ", ln))


def art(name):
    return (ART / name).read_text(encoding="utf-8")


def team(rel):
    return (FILES / rel).read_text(encoding="utf-8")


def ages(json_text):
    rows = json.loads(json_text)
    return "\n".join(f'{r["id"]}  received {r["receivedAt"]}  {r["ageLabel"]}' for r in rows)


def jar_json(after):
    i = JAR.index(after) + len(after)
    return JAR[i:].strip().splitlines()[0]


SHORT = RID[:8]
WS_TREE = """priorauth-workspace/                 <b>the folder project</b>: a git repo of its own (the team's files)
├── <span class="n">.archon/config.yaml</span>              assistant: claude
├── <span class="n">.archon/workflows/team/fix-across-repos/</span>
│   ├── <span class="n">fix-across-repos.yaml</span>        <span class="m">10 nodes, 2 waits</span>
│   └── <span class="n">commands/scan.md, implement.md</span>
├── <span class="n">CLAUDE.md</span>                        the repo map and the rules across both repos
├── <span class="n">scripts/verify.sh</span>, verify.cmd    install priorauth-aging, then test priorauth-api
├── <span class="n">docs-in/bug-report.md</span>            Ravi's report, with holidays-TX-01-2027.json
├── <span class="n">.gitignore</span>                       /priorauth-aging/ and /priorauth-api/ are not part of it
├── priorauth-aging/                 <b>repo 1</b>: the aging library 1.0.0, its own git and remote
└── priorauth-api/                   <b>repo 2</b>: the API 1.2.0, depends on priorauth-aging 1.0.0"""

ST = []
# ================= Set up =================
def group(labels, tag="real", label="git returns"):
    c, o = shell_group(SETUP, labels)
    return io(cmd(c, None, "Git Bash"), see(x(fold(o)), tag, label))


MOVED = [f for f in SETUP["starter-files"]["stdout"].split() if "/aging/" in f or "/data/holidays-" in f]
assert len(MOVED) == 6, MOVED
ST.append(step(1, "Set up", "--setup", "ours", "Split the starter: a library and an API",
               "The same split as the AI-DLC course's two-repo run: the aging package of priorauth-api 1.1.0 becomes the library priorauth-aging 1.0.0, and the API 1.2.0 depends on it.", "Meena · 5 min",
               group(["starter", "starter-v110", "aging-repo", "api-split", "api-repo"])
               + plain("Between the commands, six files move from the API to the new library (the script copies them before <code>git init</code> in <code>priorauth-aging</code>, and <code>git rm</code> takes them out of the API): " + ", ".join(f"<code>{x(f.split('/')[-1])}</code>" for f in MOVED) + ". The library gets its own <code>pom.xml</code> and README; the API's <code>pom.xml</code> gains one dependency and moves to 1.2.0.")
               + tabs("split", [("priorauth-aging/pom.xml", "priorauth-aging/pom.xml", "the library, 1.0.0", "xml", AGING_POM),
                                ("priorauth-aging/README.md", "priorauth-aging/README.md", "what the library is", "md", AGING_README),
                                ("priorauth-api/pom.xml (added)", "priorauth-api/pom.xml", "the dependency the API gains", "xml", API_DEP)])
               + note("The public starter's tags are deleted before the split: <code>v1.1.0</code> there is the AI-DLC answer key. The new tags <code>v1.0.0</code> (library) and <code>v1.2.0</code> (API) are the versions this run starts from.")))

ST.append(step(2, "Set up", "--setup", "ours", "The team's workspace: a git repo of its own",
               "The workspace holds the team's files only: .archon/, CLAUDE.md, the check, the bug report. Its .gitignore leaves the two code repos out.", "Meena · 2 min",
               group(["workspace-repo"])
               + note("<code>git update-index --chmod=+x</code> marks <code>verify.sh</code> executable for every clone: on Windows git does not see the file mode. The files themselves are step 5's tabs.")))

ST.append(step(3, "Set up", "--setup", "ours", "Remotes for all three, standing in for GitHub",
               "Three bare repos play GitHub, so every push in the run is a real push to a remote.", "Meena · 1 min",
               group(["remote-priorauth-aging", "push-priorauth-aging", "remote-priorauth-api", "push-priorauth-api", "remote-priorauth-workspace", "push-priorauth-workspace"])
               + note("On a real team these are three GitHub repos, and the clone URLs in step 4 are theirs. Each code repo keeps its own history, branches and pull requests; the workspace repo changes only when the team's process does.")))

ST.append(step(4, "Set up", "--setup", "ours", "Kiran's machine: the workspace, then each repo inside it",
               "Clone the workspace first, then the two code repos into it, and check the workflow.", "Kiran · 3 min",
               group(["clone-workspace", "clone-priorauth-aging", "clone-priorauth-api", "identity", "tree"])
               + disk(WS_TREE, "On disk: Kiran's workspace")
               + io(cmd("archon validate workflows fix-across-repos", None, "any shell"), see(x(SETUP["validate"]["stdout"].strip()), "real", "Archon returns"))
               + note("<code>git status --ignored</code> in the workspace shows the two repos as <code>!!</code>, ignored: the workspace's git never sees their files. The workspace as it is after the run, with both repos at their merged <code>main</code>, is in the course repo: <code>archon-hello-world-java/multirepo-workspace/</code>.")))

ST.append(step(5, "Set up", "--setup", "the bug", "Read the bug report and the workflow",
               "Ravi's report is the input; the workflow is written for a folder project, so the git in each repo is in its prompts and bash nodes.", "Kiran · 3 min",
               tabs("bug", [("bug-report.md", "docs-in/bug-report.md", "Ravi, 17 Oct · real input (from the AI-DLC course)", "md", team("docs-in/bug-report.md")),
                            ("fix-across-repos.yaml", WF_PATH, "the team's workflow", "yaml", WF_TEXT),
                            ("implement.md", ".archon/workflows/team/fix-across-repos/commands/implement.md", "each implement pass's prompt", "md", team(".archon/workflows/team/fix-across-repos/commands/implement.md")),
                            ("scan.md", ".archon/workflows/team/fix-across-repos/commands/scan.md", "the scan node's prompt", "md", team(".archon/workflows/team/fix-across-repos/commands/scan.md")),
                            ("CLAUDE.md", "CLAUDE.md", "the workspace's rules", "md", team("CLAUDE.md")),
                            ("verify.sh", "scripts/verify.sh", "the one check", "bash", team("scripts/verify.sh"))])
               + workflow_dag(WFN, "fix-across-repos: the 10 nodes this run goes through", {
                   "scan": "step 8", "plan": "step 8", "approve-plan": "step 9", "implement": "step 10", "checks": "step 11",
                   "review": "step 11", "approve-change": "step 13", "push": "step 13"})
               + plain("Compared with the one-repo workflow, three things moved into the YAML: the implement prompt says <i>which repos</i> and <i>which branch in each</i>, the checks node loops over both repos, and the push node pushes a branch only where there are commits. Archon does none of it for a folder project.")))

ST.append(step(6, "Set up", "--setup", "before", "Before the run: it builds, and the bug shows",
               "The check passes on main, and the jar gives the numbers Ravi complained about.", "Kiran · 2 min",
               io(cmd("./scripts/verify.sh\ncd priorauth-api; mvn -q -DskipTests package\njava -jar target/priorauth-api-1.2.0.jar\ncurl \"localhost:8080/requests/pending?asOf=2027-01-05\"", None, "Git Bash"),
                  see(x("verify: passed\n\n" + ages(BEFORE.strip().splitlines()[-1])), "real", "verify and the API return"))
               + note("1 January 2027 lies inside all three requests' periods, so with New Year's Day counted as a working day every age is one too high. The 2026 holiday file is the only one the library ships.")))

ST.append(step(7, "Set up", "--setup", "free check", "Dry-run it: not with --folder",
               "A dry run walks the graph with stub outputs, no model and no cost. For a folder project it has to run without the flag.", "Kiran · 1 min",
               io(cmd('archon workflow run fix-across-repos --folder --dry-run --default-stubs "Fix the bug in docs-in/bug-report.md"', None, "any shell"),
                  see(x(S["dry-run"]["stderr"].strip()), "real", "Archon returns"))
               + io(cmd('archon workflow run fix-across-repos --dry-run --default-stubs "Fix the bug in docs-in/bug-report.md"', None, "any shell"),
                    see(x("…\nPAUSED    approve-plan (wait) — durable wait\n…\n" + S["dry-run-plain"]["stdout"].strip().splitlines()[-2] + "\n" + S["dry-run-plain"]["stdout"].strip().splitlines()[-1]), f"real · {S['dry-run-plain']['seconds']}s", "Archon returns"))
               + note("Without <code>--folder</code> the dry run treats the workspace (a git repo) as an ordinary repo, which is fine for checking the graph: a dry run registers nothing and creates no run. <code>archon project list</code> was the same before and after.")))

# ================= Plan =================
ST.append(step(8, "Plan", "--plan", "start", "Start the run from the workspace root",
               "The first run with --folder registers the folder project; Archon then works in place, with no worktree.", f"Kiran · scan {chip('scan')} · plan {chip('plan')}",
               io(cmd('archon workflow run fix-across-repos --folder --detach "Fix the bug in docs-in/bug-report.md (Ravi, 17 Oct): New Year\'s Day counted as a working day"', None, "any shell"),
                  see(x(S["run"]["stdout"].strip()), "real", "Archon returns"))
               + tabs("plan", [("scan.md", "$ARTIFACTS_DIR/scan.md", "what the scan found in both repos", "md", art("scan.md")),
                               ("plan.md", "$ARTIFACTS_DIR/plan.md", "the plan, per repo", "md", art("plan.md"))])
               + note("<code>_folder/priorauth-workspace</code>: the run's transcript and artifacts live under the folder project in <code>~/.archon/workspaces/</code>, not under either repo. The scan read both repos from the root, found the cause in the library (<code>HolidayCalendar</code> loads only one year's file) and saw that the API needs only the new version.")))

ST.append(step(9, "Plan", "--plan", "wait 1", "Approve the plan, with a correction",
               "The plan is right about the code and the versions, and wrong about two of the expected numbers.", f"Meena · {chip('approve-plan')} to answer",
               io(cmd(f"archon workflow wait {SHORT}… --json", None, "any shell"),
                  see(x(W1["message"]), "real · approve-plan", "The run is waiting"))
               + gate("Approved with a correction: Meena Iyer", x(APP_PLAN), "archon workflow approve &lt;run&gt; \"…\"")
               + plain("New Year's Day is in every one of the three periods, so all three ages drop by one: 62, 59, 56. The plan said 62, 60, 57. In this workflow a reject cancels the run, so Meena approves and puts the correction in the approval text, which the implement prompt reads as <code>$approve-plan.output.text</code>.")))

# ================= Build =================
ST.append(step(10, "Build", "--build", "in place", "Implement in both repos, in the live checkouts",
               "The agent branches and commits in each repo itself; the loop ends when ./scripts/verify.sh passes.", f"Archon · implement {chip('implement')}",
               see(x(progress("approve-plan") + "\nLoop node 'implement' completed after 1 iteration"), "real", "Archon returns, after the approval")
               + tabs("impl", [("implementation.md", "$ARTIFACTS_DIR/implementation.md", "what the agent did, per repo", "md", IMPL),
                               ("priorauth-aging", f"priorauth-aging · commit {COMMIT['priorauth-aging']}", "the fix, a test, the 2027 file, 1.0.1", "diff", PATCH["priorauth-aging"].read_text(encoding="utf-8")),
                               ("priorauth-api", f"priorauth-api · commit {COMMIT['priorauth-api']}", "the new version, one test, 1.2.1", "diff", API_PATCH)])
               + table(["Repo", "Branch", "Commit", "Change"], [
                   ["priorauth-aging", "<code>fix/holidays-across-years</code>", f"<code>{COMMIT['priorauth-aging']}</code>", "1.0.0 → 1.0.1: every year's holiday file is loaded; the 2027 file added; 3 tests"],
                   ["priorauth-api", "<code>fix/holidays-across-years</code>", f"<code>{COMMIT['priorauth-api']}</code>", "1.2.0 → 1.2.1: depends on aging 1.0.1; one test for 2027-01-05; no code change"]], "kv")
               + note("One Claude Code session did all of this, from the workspace root: to it the two repos are two folders. Its tool calls, and the files it edited in each repo: <a href='#claude'>What each AI node handed Claude Code</a>.")
               + note("Archon's own check passed: the loop's <code>until_bash: ./scripts/verify.sh</code> ran in Archon's shell. Inside the agent's session, Git Bash's <code>mvn</code> failed to start (<code>ClassNotFoundException: …classworlds.launcher.Launcher</code>), so the agent ran <code>scripts\\verify.cmd</code> for its own check, as CLAUDE.md allows on Windows, and said so. Nothing ran in a worktree: these are Kiran's own clones, switched to the new branch.")))

ST.append(step(11, "Build", "--review", "checks + review", "Checks, then a second reader",
               "The checks node runs the workspace check and shows each repo's branch; the review node reads both diffs.", f"Archon · checks {chip('checks')} · review {chip('review')}",
               see(x(fold(W2["message"].split("Checks:", 1)[1].strip().split("\n\nApprove to push")[0])), "real · the checks node", "Archon returns")
               + tabs("rev", [("review.md", "$ARTIFACTS_DIR/review.md", "verdict READY", "md", art("review.md"))])
               + note("The reviewer recounted the ages on its own and agreed with Meena's numbers. What it did not check: the packaged jar, which is where the new <code>classpath*:</code> lookup could behave differently from the tests.")))

# ================= Ship =================
ST.append(step(12, "Ship", "--ship", "by hand", "Check the packaged jar by hand",
               "Meena asked for it at the plan: the jar must find both years' files inside the library jar.", "Kiran · 1 min",
               io(cmd("cd priorauth-api; mvn -q -DskipTests package\njava -jar target/priorauth-api-1.2.1.jar\ncurl \"localhost:8080/requests/pending?asOf=2027-01-05\"\ncurl \"localhost:8080/requests/pending?asOf=2026-10-13\"", None, "Git Bash"),
                  see(x("BOOT-INF/lib/priorauth-aging-1.0.1.jar\n\nasOf=2027-01-05\n" + ages(jar_json("asOf=2027-01-05:")) + "\n\nasOf=2026-10-13\n" + ages(jar_json("asOf=2026-10-13:"))), "real", "the jar returns"))
               + note("62, 59, 56 on 5 Jan 2027 (63, 60, 57 before), and still 7, 4, 1 on 13 Oct 2026: the 2026 holidays still load. The same three numbers as the AI-DLC course's answer for 13 Oct.")))

ST.append(step(13, "Ship", "--ship", "wait 2", "Approve; one branch pushed per repo",
               "The push node pushes a branch only where there are commits, library first.", f"Meena · push {chip('push')}",
               gate("Approved: Meena Iyer", x(APP_CHANGE), "archon workflow approve &lt;run&gt; \"…\"")
               + see(x(PUSH.split("Use from the workspace root. NOT for: a change to one repo only (run request-to-pr inside that repo).", 1)[1].strip()), "real", "Archon returns")
               + note("Two pull requests to open, one per repo, and in order: priorauth-aging's first, because priorauth-api 1.2.1 needs aging 1.0.1 to be published. No <code>gh</code> login here, so the merge in step 15 stands in for both.")))

# ================= After =================
ST.append(step(14, "After", "--setup", "the record", "What a folder project leaves behind",
               "No worktree, no branch of Archon's: a run row, a transcript, artifacts and the captured workflow source.", "Kiran · 2 min",
               io(cmd(f"archon workflow get {SHORT}…\narchon project list\narchon isolation list\narchon doctor", None, "any shell"),
                  see(x(S["get"]["stdout"].strip() + "\n\n" + S["project-list"]["stdout"].strip() + "\n\n" + S["isolation-list"]["stdout"].strip() + "\n\n"
                        + "\n".join(ln for ln in S["doctor"]["stdout"].splitlines() if "Folder project" in ln or "All checks" in ln)), "real", "Archon returns"))
               + disk(x(STORAGE.strip()), "On disk: ~/.archon/workspaces/ for this project")
               + note("<code>workflow get</code> calls the workspace itself the worktree, marked <i>(live)</i>. <code>isolation list</code> has nothing to show, in odd words. <code>doctor</code> names the two repos the folder holds.")))

ST.append(step(15, "After", "--setup", "merge", "Merge in release order; tidy up by hand",
               "Meena merges the library first and tags it, then the API. Archon has nothing to complete: Kiran deletes his own branches.", "Meena, Kiran · 3 min",
               see(x(S["merge"]["stdout"].strip()), "real", "git: Meena's merges")
               + io(cmd("archon complete fix/holidays-across-years", None, "any shell"), see(x(S["complete"]["stdout"].strip()), "real", "Archon returns"))
               + io(cmd("git -C priorauth-aging switch main; git -C priorauth-aging pull\ngit -C priorauth-api switch main; git -C priorauth-api pull\n./scripts/verify.sh\ngit -C priorauth-aging branch -d fix/holidays-across-years\ngit -C priorauth-api branch -d fix/holidays-across-years", None, "Git Bash"),
                    see(x(S["after-merge"]["stdout"].strip() + "\n" + S["cleanup"]["stdout"].strip()), "real", "git returns"))
               + note("In the one-repo run <code>archon complete</code> removed the worktree and the local branch. Here there is no isolation environment, so it finds nothing: the branches were the agent's and Kiran's, and so is the tidy-up.")))

ST.append(step(16, "After", "--setup", "compare", "The same bug in AI-DLC and in Archon",
               "Both runs started from the same two repos at the same versions, with the same bug report.", "read · 3 min",
               table(["", "AI-DLC (28 Oct 2026)", "Archon folder project (this run)"], [
                   ["Where the process lives", "the workspace's <code>aidlc/</code> and the plugin's stages", "the workspace's <code>.archon/workflows/</code>, written by the team"],
                   ["Git in each repo", "the agent: a branch <code>request-age/new-year-holiday</code> in both", "the agent: a branch <code>fix/holidays-across-years</code> in both; the push node pushed them"],
                   ["People's approvals", "Reverse Engineering (Kiran), Code Generation and Build and Test (Meena)", "the plan, with a correction, and the change (Meena)"],
                   ["The library's fix", "<code>forTenant</code> got the period as arguments: <b>2.0.0</b> (breaking)", "<code>forTenant</code> kept its signature: <b>1.0.1</b> (patch)"],
                   ["The API's change", "1.2.1: the controller passes the period; depends on aging 2.0.0", "1.2.1: depends on aging 1.0.1; no code change"],
                   ["Record", "<code>aidlc/</code>, committed with the workspace", "artifacts + transcript under <code>~/.archon/workspaces/_folder/</code>, not committed"],
                   ["Result on 2027-01-05", "62 / 59 / 56 (its API test)", "62 / 59 / 56 (its API test, and the jar by hand)"]])
               + plain(f'Two correct fixes of different size: the graph showed AI-DLC\'s planner a caller in the other repo and it changed the method; Archon\'s planner kept the method and changed what it loads. AI-DLC\'s run: <a href="../../ai-dlc-execution/aidlc-hello-world-java/aidlc-graphify.html#gx-two-repos">Two repos, one graph</a>.')))

STEPS = [(1, "Split the starter in two"), (2, "The workspace repo"), (3, "Remotes for all three"), (4, "Kiran's clones"),
         (5, "Bug report and workflow"), (6, "Before: the bug shows"), (7, "Dry-run, not with --folder"),
         (8, "Start from the root"), (9, "Approve, with a correction"), (10, "Implement in both repos"), (11, "Checks and review"),
         (12, "Check the jar by hand"), (13, "Approve; push both"), (14, "What it leaves behind"), (15, "Merge; tidy up"), (16, "AI-DLC vs Archon")]
PH = {n: ("Set up", "--setup") for n in range(1, 8)} | {n: ("Plan", "--plan") for n in (8, 9)} | {n: ("Build", "--build") for n in (10, 11)} |      {n: ("Ship", "--ship") for n in (12, 13)} | {n: ("After", "--setup") for n in (14, 15, 16)}
assert len(ST) == len(STEPS)

hero = f'''<section class="hero" id="top">
  <div>
    <h1>One bug, two repos, one Archon run, for real.</h1>
    <p class="lead">The age badge counts New Year's Day as a working day. The cause is in the aging library; the API has to move to the fixed version. Kiran runs the team's workflow from a <b>folder project</b>, a workspace that holds both repos: the agent fixes the library and bumps the API, each in its own branch, Meena approves twice, and a branch is pushed in each repo. Every command and reply below is real.</p>
    <div class="facts">
      <div><b>2</b>repos, one run, in place</div>
      <div><b>10</b>nodes, 2 of them waits</div>
      <div><b>1</b>pass of the implement loop</div>
      <div><b>2</b>branches pushed, library first</div>
      <div><b>${COST:.2f}</b>reported cost (API prices; claude.ai plan)</div>
      <div><b>0</b>worktrees: Archon made none</div>
    </div>
  </div>
  <aside class="slack" aria-label="The bug report, as it arrived in Slack">
    <div class="slack__bar"><span># priorauth-reviewers</span><span>Sat 17 Oct</span></div>
    <div class="slack__body">
      <div class="slack__who"><i>RM</i><div><b>Ravi Menon</b><span>Nurse Manager, Utilization Management · 09:40</span></div></div>
      <p>Kiran, the new age badge is great, but I think it breaks in January. I tried the screen with <code>asOf=2027-01-05</code>: PA-10231 shows an age one higher than the nightly report, and so do the other pending ones. It looks like New Year's Day is being counted as a working day.</p>
    </div>
  </aside>
</section>
'''
# What each AI node handed Claude Code: the shared mapping (asserted against tools/data/docs/), and, from the transcript,
# each session: its prompt, new or continued, its tool calls, and the files it edited in each repo.
claude_facts()
CC = []
for _ln in next((RUN / "logs").glob(f"{RID}*.jsonl")).read_text(encoding="utf-8").splitlines():
    _d = json.loads(_ln)
    if _d.get("type") == "node_start" and _d["execution"]["node"]["kind"] in ("agent", "loop"):
        _n, _b = _d["execution"]["node"], _d["execution"]["binding"]
        assert _b["provider"] == "claude" and not _n.get("skills")
        _cmd = _n.get("command") or (_n.get("source") or {}).get("name")
        assert not _cmd or _cmd.startswith("__archon_pack__project:team:fix-across-repos::"), _cmd
        CC.append({"node": _d["step"], "src": f"<code>command: {_cmd.rsplit('::', 1)[1]}</code> (the team's <code>commands/</code>)" if _cmd else "<code>prompt:</code> in the YAML",
                   "origin": _b["sessionOrigin"], "tools": {}, "edits": {r: set() for r in REPOS}})
    if _d.get("type") == "provider_event" and _d["event"].get("type") == "tool_call":
        _e = _d["event"]
        CC[-1]["tools"][_e["name"]] = CC[-1]["tools"].get(_e["name"], 0) + 1
        _fp = (_e.get("rawInput") or {}).get("file_path", "").replace("\\", "/")
        for r in REPOS:
            if _e["name"] in ("Edit", "Write") and f"/{r}/" in _fp:
                CC[-1]["edits"][r].add(_fp.split(f"/{r}/", 1)[1])
    if _d.get("type") == "provider_event" and _d["event"].get("type") == "subtask":
        assert _d["event"].get("taskType") in ("local_bash", None), _d["event"]
assert [(c["node"], c["origin"]) for c in CC] == [("scan", "fresh"), ("plan", "resumed"), ("implement", "fresh"), ("review", "fresh")], CC
assert not any({"Skill", "Task", "Agent"} & set(c["tools"]) for c in CC)
assert [c["node"] for c in CC if any(c["edits"].values())] == ["implement"]
EDITS = CC[2]["edits"]
for r in REPOS:  # the files the session edited are the files of that repo's commit
    assert EDITS[r] and all(f"b/{f}" in PATCH[r].read_text(encoding="utf-8") for f in EDITS[r]), (r, EDITS[r])
assert not re.search(r"^\s*(skills|agents|hooks|mcp|plugins):", WF_TEXT, re.M) and not any(p.parts[0] == ".claude" for p in (q.relative_to(FILES) for q in FILES.rglob("*")))
CC_STEP = {"scan": 8, "plan": 8, "implement": 10, "review": 11}
cc_rows = [[f"<code>{c['node']}</code>, step {CC_STEP[c['node']]}", c["src"], {"fresh": "new", "resumed": "continued <code>scan</code>'s"}[c["origin"]],
            ", ".join(f"{k} {v}" for k, v in sorted(c["tools"].items(), key=lambda kv: -kv[1])),
            "<br>".join(f"{r}: {len(c['edits'][r])}" for r in REPOS if c["edits"][r]) or "none (artifacts only)"] for c in CC]
ccard = card("claude", "What each AI node handed Claude Code",
             f"<p>Archon's Claude provider starts Claude Code through the Claude Agent SDK, with Kiran's claude.ai login: <b>each AI node, and each loop pass, is one Claude Code session</b>, and in a folder project its folder is the workspace root, so <b>one session sees both repos</b>. The run started {len(CC)}. From its transcript (real):</p>"
             + table(["Node", "Its prompt", "Session", "Tool calls", "Files it changed with Edit or Write"], cc_rows)
             + note("One <code>implement</code> session changed both repos: it made the branch in each (<code>git checkout -b</code>), edited the files of both commits, and committed in each, all because <code>commands/implement.md</code> and the workspace's <code>CLAUDE.md</code> say so. Nothing in Claude Code knows about repos: to it they are two folders. No session called <code>Skill</code> or <code>Task</code>: the workflow names no <code>skills:</code> or <code>agents:</code>, and the workspace has no <code>.claude/</code> folder. The transcript's <i>subtasks</i> are the agent's background shell commands, not subagents.")
             + "<p style=\"margin-top:14px\"><b>What each workflow field hands the session</b> (the third column is the one-repo run's <code>request-to-pr</code>; <code>fix-across-repos</code> uses the same fields):</p>"
             + table(["In the workflow", "What Claude Code gets", "In the course's run"], [list(r_) for r_ in CLAUDE_MAP], "kv")
             + note("Checked against the Archon 0.13.2 docs (workflow language, skills, hooks, authoring commands, security). More: <a href=\"../archon-introduction.html#s11\">the introduction, step 11</a>; where Claude Code's own files go in a workspace: <a href=\"../archon-workspace-setup.html#claude\">the setup page</a>."))
yourself = card("yourself", "Run it yourself", f"""<ol>
<li>Set up Archon as on the <a href="../archon-workspace-setup.html">setup page</a> (steps 1–4), with JDK 21, Maven and Git Bash.</li>
<li>Take the workspace from the course repo: <code>archon-hello-world-java/multirepo-workspace/</code> holds the team's files and both repos as they are after the run (library 1.0.1, API 1.2.1). To start where the run started, do steps 1–4 instead: they build the two repos from the public starter at <code>v1.1.0</code> (the course's <code>tools/setup_multirepo_run.py</code> runs exactly those commands).</li>
<li>Make each folder a git repo with a remote (steps 2–4), and run <code>archon workflow run fix-across-repos --folder …</code> from the workspace root.</li>
<li>Answer the two waits. Check the plan's numbers: the course's plan miscounted two of them.</li></ol>
{note("Your run id, times, cost and commit hashes will differ. The course's transcript is in <code>archon-hello-world-java/multirepo-run/logs/</code>, its artifacts in <code>multirepo-run/artifacts/</code>, each repo's diff in <code>multirepo-run/git/</code>.")}""")
real = card("real", "What is real here", """<p>Everything in the Archon and git boxes is real output, setup included, from the course's run on Windows (4 Nov 2026, Archon 0.13.2, Claude Code on a claude.ai plan), captured by <code>tools/archon_step.py</code> and copied by <code>tools/capture_multirepo_run.py</code>. Local paths are mapped to <code>C:\\Users\\you</code> and <code>C:\\work</code>; long Spring Boot logs are folded.</p>
<p>Not run: opening the two pull requests (no <code>gh</code> login; the repos' remotes are local bare repos standing in for GitHub). The merges are plain <code>git merge --no-ff</code>, standing in for merging the PRs. The people are fictional; their answers were typed by the course author. The reported cost is Archon's API-price equivalent; the run used a claude.ai plan.</p>""")

main = (hero + phase("--setup", "Set up", "steps 1–7 · the two repos, the workspace, the clones, the bug, a dry run") + "".join(ST[0:7])
        + phase("--plan", "Plan", "steps 8–9 · start from the root, approve the plan") + "".join(ST[7:9])
        + phase("--build", "Build", "steps 10–11 · fix in both repos, check, review") + "".join(ST[9:11])
        + phase("--ship", "Ship", "steps 12–13 · check by hand, push a branch per repo") + "".join(ST[11:13])
        + phase("--setup", "After", "steps 14–16 · the record, the merges, AI-DLC") + "".join(ST[13:16])
        + yourself + ccard + real)
footer = ('<footer class="foot">Archon, two repos · Archon 0.13.2 · <a href="archon-hello-world-java-run.html">the one-repo run</a> · <a href="../archon-introduction.html#s10">introduction, step 10</a> · '
          '<a href="../archon-concepts-explained.html#places">concepts</a> · <a href="../index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Archon, Two Repos: Every Step", "One bug fixed across two repos with an Archon folder project, step by step: the workspace, the workflow, what you type, what Archon and Claude return, both waits, a branch per repo, and the merges. Real run, real output.",
             "Archon, two repos", "one bug · a folder project · real run", len(STEPS),
             rail(STEPS, PH, [("yourself", "Run it yourself"), ("claude", "What Claude Code got"), ("real", "What is real here")]), main, footer)
write(DEST / "archon-two-repos-run.html", html_)
