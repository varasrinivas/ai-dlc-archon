"""Build archon-hello-world-java/archon-hello-world-java-run.html: Ravi's request taken through Archon, step by step.

Everything comes from the course's real run (4 Nov 2026, Archon 0.13.2, Claude Code on a claude.ai login), copied into
archon-hello-world-java/java-run/ by capture_java_run.py: setup-steps.json and steps.json (every command typed and what
came back), nodes.json (per node: time, tokens, cost, from the transcripts), artifacts/ (what each run wrote), git/
(priorauth-api's commits and diffs), storage.txt (the folder project's folders under ~/.archon), and java-workspace/ (the
team workspace with priorauth-api inside it, after the merge). The asserts tie the page's numbers to that data.

Usage: py -3.12 tools/build_run_page.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli_parse import workflow_nodes  # noqa: E402
from diagrams import workflow_dag  # noqa: E402
from pagekit import (ARCHON_WORDS, CLAUDE_MAP, E, ROOT, card, claude_facts, disk, gloss, gate, io, note, page, phase, plain, rail, see, shell_group, step, table, tabs,  # noqa: E402
                     three, write, you)

DEST = ROOT / "archon-hello-world-java"
RUN = DEST / "java-run"
WS = DEST / "java-workspace"
API = WS / "priorauth-api"
S = {s["label"]: s for s in json.loads((RUN / "steps.json").read_text(encoding="utf-8"))}
SETUP = {s["label"]: s for s in json.loads((RUN / "setup-steps.json").read_text(encoding="utf-8"))}
NODES = json.loads((RUN / "nodes.json").read_text(encoding="utf-8"))
RID = next(k for k, v in NODES.items() if v["workflow"] == "request-to-pr")
FIX_ID = next(k for k, v in NODES.items() if v["workflow"] == "archon-implement")
PLAN_ID = next(k for k, v in NODES.items() if v["workflow"] == "archon-plan")
SHORT = RID[:8]
WF_PATH = ".archon/workflows/team/request-to-pr/request-to-pr.yaml"
WF_TEXT = (WS / WF_PATH).read_text(encoding="utf-8")
WFN = workflow_nodes(WF_TEXT)
KIND = {n["id"]: n["kind"] for n in WFN}
GIT = RUN / "git"
BRANCH_LOG = (GIT / "branch-log.txt").read_text(encoding="utf-8")
COMMITS = re.findall(r"^([0-9a-f]{7}) ", BRANCH_LOG, re.M)
PATCH = {p.stem.split("-")[1]: p.read_text(encoding="utf-8") for p in GIT.glob("commit-*.patch")}
assert len(COMMITS) == 2 and set(COMMITS) <= set(PATCH), (COMMITS, list(PATCH))
FEAT, FIX = COMMITS[1], COMMITS[0]  # git log lists newest first
BRANCH = re.search(r"Merge (request-age/[\w-]+)", S["merge"]["stdout"]).group(1)
STORAGE = (RUN / "storage.txt").read_text(encoding="utf-8")


def tests_in(text):
    return sum(int(m) for m in re.findall(r"Tests run: (\d+), Failures: 0", text))


# ---------- facts the page states, checked against the data ----------
assert len(WFN) == 15 and sum(1 for n in WFN if n["kind"] == "wait") == 4
assert "request-to-pr                            ok" in SETUP["validate"]["stdout"]
assert "verify: passed" in SETUP["verify-before"]["stdout"] and tests_in(SETUP["verify-before"]["stdout"]) == 3
assert '"ageBusinessDays"' not in SETUP["before"]["stdout"] and '"id":"PA-10231"' in SETUP["before"]["stdout"]
assert "!! priorauth-api/" in SETUP["identity"]["stdout"]
assert 'Registered folder project "java-workspace"' in S["run"]["stdout"] and "Started 'request-to-pr' in the background." in S["run"]["stdout"]
assert "_folder" in S["run"]["stdout"] and f"Run id: {RID}" in S["run"]["stdout"]
WAIT1 = json.loads(S["wait-1"]["stdout"])["attention"]
QUESTIONS = WAIT1["message"]
assert WAIT1["nodeId"] == "answer" and len(re.findall(r"^\d\. \*\*", QUESTIONS, re.M)) == 7
assert "Folder project — running in place (no worktree isolation)." in S["answer-1"]["stdout"]
W2, W3, W4, W5 = (json.loads(S[f"wait-{i}"]["stdout"])["attention"] for i in (2, 3, 4, 5))
assert "overFiveBusinessDays" in W2["message"] and "the age is 0, never negative" in W2["message"]
assert "`overLimit`" in W3["message"] and "`ageLabel`" in W3["message"] and "400 error instead of age 0" in W3["message"]
assert W4["nodeId"] == "approve-plan" and "request-age/pending-age" in W4["message"]
assert W5["nodeId"] == "approve-change" and W5["message"].startswith("Review verdict: READY")
assert "Loop node 'implement' completed after 1 iteration" in S["approve-plan"]["stdout"]
JAR1 = S["jar-check"]["stdout"]
assert '"ageBusinessDays":7,"overLimit":true,"ageLabel":"7 bd OVER 5"' in JAR1 and "HTTP/1.1 500" in JAR1
assert "Workflow cancelled" in S["reject-change"]["stdout"] and "Rejected but failed to resume" in S["reject-change"]["stderr"]
assert "folder projects run in place; adoption carries provenance and $ADOPTED_RUN_DIR access only." in S["fix-run"]["stdout"]
FIX_JSON = json.loads(re.search(r'(\{"done".*?\})\n', S["fix-run"]["stdout"]).group(1))
assert FIX_JSON["green"] is True and FIX in FIX_JSON["summary"]
tests = tests_in(S["verify-main"]["stdout"])
assert tests == 21 == tests_in(S["verify-fix"]["stdout"]), tests
JAR2 = S["jar-check-2"]["stdout"]
assert JAR2.count("HTTP/1.1 400") == 2 and "HTTP/1.1 500" not in JAR2 and '"ageLabel":"7 bd OVER 5"' in JAR2
assert f"[new branch]      {BRANCH} -> {BRANCH}" in S["push-by-hand"]["stdout"]
assert "Status: cancelled" in S["get"]["stdout"] and "(live)" in S["get"]["stdout"] and FIX_ID in S["get"]["stdout"]
assert "No codebases registered." in S["isolation-list"]["stdout"]
assert '"java-workspace" (runs in place) — 1 contained repo(s): priorauth-api' in S["doctor"]["stdout"]
assert "no active isolation environment" in S["complete"]["stdout"]
assert "verify on main: passed" in S["verify-main"]["stdout"] and "workspace clean" in S["verify-main"]["stdout"]
assert f"Deleted branch {BRANCH}" in S["cleanup"]["stdout"]
for d in ("_folder/java-workspace/artifacts/", "_folder/java-workspace/logs/"):
    assert d in STORAGE, d
assert "worktrees" not in STORAGE
ROWS = [n for n in NODES[RID]["nodes"] if n["event"] == "node_complete"]
COST_MAIN = sum(n["cost"] or 0 for n in ROWS)
COST_FIX = sum(n["cost"] or 0 for n in NODES[FIX_ID]["nodes"] if n["event"] == "node_complete")
GET_COST = float(re.search(r"Cost: \$([\d.]+)", S["get"]["stdout"]).group(1))
assert abs(COST_MAIN - GET_COST) < 0.01, (COST_MAIN, GET_COST)
ITER = {}
for n in ROWS:
    ITER[n["node"]] = ITER.get(n["node"], 0) + 1
assert ITER["write-requirements"] == 2 and ITER["review-requirements"] == 2
DIFFSTAT = (GIT / "diffstat.txt").read_text(encoding="utf-8").strip()
m = re.search(r"(\d+) files changed, (\d+) insertions\(\+\), (\d+) deletions", DIFFSTAT)
NFILES, PLUS, MINUS = map(int, m.groups())
CHANGED = re.findall(r"^diff --git a/(\S+) ", (GIT / "diff.patch").read_text(encoding="utf-8"), re.M)
assert len(CHANGED) == NFILES and all((API / f).exists() for f in CHANGED)


def x(s):
    return E(s)


def fold(t):
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


def pause(label):
    """The attention block a step ended on (from the pause marker to the end), Spring test logs folded."""
    o = S[label]["stdout"]
    i = o.rfind("⏸️")
    return fold(o[i:].strip()) if i >= 0 else ""


def progress(label, extra=()):
    lines = [ln for ln in (S[label]["stderr"]).splitlines() if re.match(r"^\[(?!workflow)[\w-]+\] ", ln)]
    return "\n".join(list(extra) + lines)


def nd(node, run=RID, i=-1):
    return [n for n in NODES[run]["nodes"] if n["node"] == node and n["event"] == "node_complete"][i]


def fmt_ms(ms):
    s = round((ms or 0) / 1000)
    return f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"


def nodechip(node, run=RID, i=-1):
    r = nd(node, run, i)
    return fmt_ms(r["ms"]) + (f" · ${r['cost']:.2f}" if r["cost"] else "")


def art(name, run=RID):
    return (RUN / "artifacts" / run / name).read_text(encoding="utf-8")


def wsf(rel):
    return (WS / rel).read_text(encoding="utf-8")


def cmdbox(win, mac=None, tag="PowerShell", mac_tag="Terminal"):
    return you(x(win), x(mac if mac is not None else win), tag, mac_tag if mac is not None else tag)


def group(labels, label="git returns"):
    c, o = shell_group(SETUP, labels)
    return io(cmdbox(c, None, "Git Bash"), see(x(fold(o)), "real", label))


def after(label, text):
    return S[label]["cmd"].split(text, 1)[1]


ANSWER_TEXT = after("answer-1", "--text ")
REJ_REQ = after("reject-requirements", RID + " ")
APP_REQ = after("approve-requirements", RID + " ")
APP_PLAN = after("approve-plan", RID + " ")
REJ_CHANGE = after("reject-change", RID + " ")
FIX_MSG = after("fix-run", RID + " ")
OCC = WAIT1["occurrence"]
TREE = """java-workspace/                      <b>the team's workspace</b>: a git repo of its own, an Archon folder project
├── <span class="n">.archon/config.yaml</span>              assistant: claude
├── <span class="n">.archon/workflows/team/request-to-pr/</span>
│   ├── <span class="n">request-to-pr.yaml</span>           <span class="m">15 nodes, 4 waits</span>
│   └── <span class="n">commands/scan.md, implement.md</span>
├── <span class="n">CLAUDE.md</span>                        the repo map and the team's rules
├── <span class="n">scripts/verify.sh</span>, verify.cmd    cd priorauth-api, then mvn -q test
├── <span class="n">docs-in/request.md</span>               Ravi's Slack message
├── <span class="n">.gitignore</span>                       /priorauth-api/ is not part of the workspace repo
├── <span class="n">.gitattributes</span>
└── priorauth-api/                   <b>the code repo</b>: its own git and remote, v1.0.2 (no age yet)
    ├── pom.xml
    └── src/main/java/com/acmehealth/priorauth/  api/ · model/ · store/"""

ST = []
# ================= Set up =================
ST.append(step(1, "Set up", "--setup", "ours", "The code repo's remote: the public starter",
               "A bare copy of the starter stands in for GitHub, so every push in the run is real. Main only: tag v1.1.0 is the AI-DLC answer key.", "Meena · 1 min",
               group(["remote-priorauth-api", "starter-log"])
               + note("<code>--no-tags</code> leaves the answer key behind (<code>git tag | wc -l</code> prints 0). On a real team this is the GitHub repo <code>priorauth-api</code>.")))

ST.append(step(2, "Set up", "--setup", "ours", "The team's workspace: a git repo of its own",
               "The workspace holds what people wrote for Archon: .archon/, CLAUDE.md, the check, the request. The code repo is cloned into it later, and its .gitignore leaves it out.", "Meena · 3 min",
               group(["workspace-repo"])
               + tabs("team", [("CLAUDE.md", "CLAUDE.md", "the repo map and the team's rules", "md", wsf("CLAUDE.md")),
                               (".gitignore", ".gitignore", "the code repo is not part of the workspace", "text", wsf(".gitignore")),
                               ("config.yaml", ".archon/config.yaml", "a folder project: no worktree settings", "yaml", wsf(".archon/config.yaml")),
                               ("verify.sh", "scripts/verify.sh", "the one check", "bash", wsf("scripts/verify.sh")),
                               ("verify.cmd", "scripts/verify.cmd", "the same, by hand on Windows", "text", wsf("scripts/verify.cmd")),
                               (".gitattributes", ".gitattributes", "keeps verify.sh LF", "text", wsf(".gitattributes"))])
               + note('The workflow and the request are step 5\'s tabs. Writing the files by hand, with a here-string per file: <a href="../archon-workspace-setup.html#s06">setup page, step 6</a>. <code>git update-index --chmod=+x</code> marks <code>verify.sh</code> executable for every clone; on Windows git does not see the file mode.')))

ST.append(step(3, "Set up", "--setup", "ours", "Its remote, then Kiran's clones: the workspace, and the repo inside it",
               "Clone the workspace first, then priorauth-api into it. Two repos, two remotes, one folder.", "Kiran · 2 min",
               group(["remote-java-workspace", "push-java-workspace", "clone-workspace", "clone-priorauth-api", "identity", "tree"])
               + disk(TREE, "On disk: Kiran's workspace")
               + note("The same shape as the AI-DLC course's <code>java-workspace/</code> and as this course's two-repo run: a folder around the code repo. <code>git status --ignored</code> in the workspace shows <code>!! priorauth-api/</code>: the workspace's git never sees the code. The workspace as it is after the run, with priorauth-api at its merged <code>main</code>, is in the course repo: <code>archon-hello-world-java/java-workspace/</code>.")))

ST.append(step(4, "Set up", "--setup", "before", "Before the run: valid, green, and no age yet",
               "The workflow validates, the check passes on v1.0.2, and the pending list has no age.", "Kiran · 2 min",
               io(cmdbox("archon validate workflows request-to-pr", None, "any shell"), see(x(SETUP["validate"]["stdout"].strip()), "real", "Archon returns"))
               + group(["verify-before", "before"], "verify and the API return")
               + note("Three tests at the start. The response has <code>receivedAt</code> and nothing else about age: that is what Ravi asked for.")))

ST.append(step(5, "Set up", "--setup", "the request", "Read the request and the workflow",
               "Ravi's Slack message is the input; the workflow is the process it will go through.", "Kiran · 2 min",
               tabs("req", [("request.md", "docs-in/request.md", "Ravi's Slack message · real input", "md", wsf("docs-in/request.md")),
                            ("request-to-pr.yaml", WF_PATH, "the team's workflow", "yaml", WF_TEXT),
                            ("scan.md", ".archon/workflows/team/request-to-pr/commands/scan.md", "the scan node's prompt", "md", wsf(".archon/workflows/team/request-to-pr/commands/scan.md")),
                            ("implement.md", ".archon/workflows/team/request-to-pr/commands/implement.md", "each implement pass's prompt", "md", wsf(".archon/workflows/team/request-to-pr/commands/implement.md"))])
               + workflow_dag(WFN, "request-to-pr: the 15 nodes this run goes through", {
                   "scan": "step 7", "questions": "step 7", "answer": "step 8", "plan": "step 10", "approve-plan": "step 11",
                   "checks": "step 12", "review": "step 12", "approve-change": "step 14", "push": "skipped: step 14"})
               + plain("The request is the order slip, the workflow is the recipe. Every arrow is a <code>depends_on</code>; every dashed box is a moment the kitchen stops until someone says go. "
                       "Because the workspace is a folder project, the git is in the YAML and the prompts: the implement prompt names the branch to make in priorauth-api, and the checks and push nodes run <code>git -C priorauth-api</code>.")))

ST.append(step(6, "Set up", "--setup", "free check", "Dry-run it first",
               "Walk the graph with stub outputs: no run, no model call, no cost. A dry run takes no --folder.", "Kiran · 1 min",
               io(cmdbox('archon workflow run request-to-pr --dry-run --default-stubs "Implement docs-in/request.md"', None, "any shell"),
                  see(x(S["dry-run"]["stdout"].split("STUBBED   questions")[0].strip()[:1500] + "\n…\nPAUSED    answer (wait) — durable wait\n…\nSimulation outcome: paused"), f"real · {S['dry-run']['seconds']}s", "Archon returns"))
               + note("The dry run shows each node's prompt with its variables filled in (<code>$USER_MESSAGE</code>, <code>$ARTIFACTS_DIR</code>) and stops at the first wait. With <code>--folder</code> it is refused (the two-repo run shows the message), and without it nothing is registered.")))

# ================= Plan =================
ST.append(step(7, "Plan", "--plan", "scan · questions", "Start the run from the workspace: Archon scans and asks",
               "One command from the workspace root. The first --folder run registers the folder project; Archon works in place, then pauses at the first wait.", f"Kiran · scan {nodechip('scan')} · questions {nodechip('questions')}", f"""
{io(cmdbox('cd C:\\work\\archon-java\\java-workspace\narchon workflow run request-to-pr --folder --detach "Implement the request in docs-in/request.md"\narchon workflow wait ' + SHORT + '… --json',
           'cd ~/work/archon-java/java-workspace\narchon workflow run request-to-pr --folder --detach "Implement the request in docs-in/request.md"\narchon workflow wait ' + SHORT + '… --json'),
     see(x(S["run"]["stdout"].strip()), "real", "Archon returns"))}
{see(x(json.dumps(dict(list(WAIT1.items())[:3] + [("message", "(below)"), ("occurrence", OCC), ("form", WAIT1["form"])]), indent=2)), f"real · abridged: the attention object of archon workflow wait --json, {S['wait-1']['seconds']:.0f}s later", "Archon returns")}
{tabs("q", [("the questions (the wait's message)", "attention: $questions.output.questions", "real · questions node", "md", QUESTIONS.split(chr(10) + chr(10), 1)[1]),
            ("scan.md", "$ARTIFACTS_DIR/scan.md", "real · written by the scan node", "md", art("scan.md"))])}
{disk('''C:\\Users\\you\\.archon\\workspaces\\_folder\\java-workspace\\
├── <span class="n">logs/''' + SHORT + '''….jsonl</span>
└── <span class="n">artifacts/runs/''' + SHORT + '''…/</span>
    ├── <span class="n">scan.md</span>
    └── <span class="n">questions.md</span>''', "On disk now (not in either repo)")}
{three([("The AI asked", "seven questions: holidays, how to count, weekends, what over 5 means, which day is today, field names, the version"),
        ("It suggested", "an answer for each, with the reason"), ("Nobody decided yet", "the run is paused; it holds no process")])}
{note("Each AI node here (<code>scan</code>, then <code>questions</code>, which continued <code>scan</code>'s session) is one Claude Code session in the workspace, reading its <code>CLAUDE.md</code>. Every session of the three runs, its prompt, model and tool calls: <a href='#claude'>What each AI node handed Claude Code</a>.")}
{note("<code>_folder/java-workspace</code>: the run's transcript and artifacts live under the folder project in <code>~/.archon/workspaces/</code>. No worktree, no branch: Kiran's clones are the checkouts the agent will work in. A one-repo project with <code>.archon/</code> inside the repo would get a worktree per run instead; the introduction's step 7 compares the two.")}
"""))

ST.append(step(8, "Plan", "--plan", "wait: answer", "Answer the seven questions",
               "A message-form wait: one free-text answer. Kiran writes what Ravi and Meena decided.", f"Kiran · write-requirements {nodechip('write-requirements', i=0)}",
               io(cmdbox(f'archon workflow answer {RID} --occurrence {OCC} --text "{ANSWER_TEXT.strip(chr(34))}"', None, "any shell"),
                  see(x(pause("answer-1")), f"real · the run continued in this terminal for {S['answer-1']['seconds']:.0f}s, then paused again", "Archon returns"), stack=True)
               + gate("Wait 1 answered: the questions", "Answered from the CLI with the occurrence id from step 7, so the answer can't land on a later pause by mistake.", "Kiran Rao, for Ravi Menon and Meena Iyer")
               + note("The first requirements already match the AI-DLC run's worked check: as of 2026-10-13, PA-10231 is 7 and over, PA-10244 is 4, PA-10263 is 1. But the field names are the AI's guess (<code>overFiveBusinessDays</code>), and an as-of date before the received date gives age 0.")))

ST.append(step(9, "Plan", "--plan", "wait: reject → revise", "Reject the requirements with the screen team's names",
               "Reject is an answer. Inside the requirements loop_group it means: write them again with this text, and ask again.", f"Meena · write-requirements {nodechip('write-requirements')}",
               io(cmdbox(f"archon workflow reject {RID} {REJ_REQ}", None, "any shell"),
                  see(x(pause("reject-requirements")), f"real · {S['reject-requirements']['seconds']:.0f}s", "Archon returns"), stack=True)
               + gate("Wait 2, first answer: reject", "The loop_group's <code>until_bash</code> saw decision <code>reject</code>, so it ran another pass: <code>write-requirements</code> read the text as <code>$LOOP_PREV.review-requirements.output.text</code> and revised.", "Meena Iyer")
               + three([("Changed", "fields <code>ageBusinessDays</code>, <code>overLimit</code>, <code>ageLabel</code>; key <code>priorauth.aging.threshold-days</code>; file <code>data/holidays-TX-01-2026.json</code>"),
                        ("New rule", "an as-of before a received date is a 400 (FR11)"), ("Still open", "the label when not over the limit (A-02), one bad row makes the call a 400 (A-03)")])))

ST.append(step(10, "Plan", "--plan", "wait: approve", "Approve the requirements; the plan is written",
               "Approve ends the loop. The plan node writes plan.md, branch included, and the run stops before any code.", f"Ravi + Meena · plan {nodechip('plan')}",
               io(cmdbox(f"archon workflow approve {RID} {APP_REQ}", None, "any shell"),
                  see(x(pause("approve-requirements")), f"real · {S['approve-requirements']['seconds']:.0f}s", "Archon returns"), stack=True)
               + tabs("req2", [("requirements.md", "$ARTIFACTS_DIR/requirements.md", "real · revision 2, approved", "md", art("requirements.md")),
                               ("plan.md", "$ARTIFACTS_DIR/plan.md", "real · plan node", "md", art("plan.md"))])
               + gate("Wait 2 answered: approve", "The answer's text records who approved and the assumptions they settled.", "Ravi Menon and Meena Iyer")
               + note(f"The plan names the branch, <code>{BRANCH}</code> in priorauth-api, following CLAUDE.md's pattern <code>request-age/&lt;slug&gt;</code>. In a folder project nobody else makes one.")))

# ================= Build =================
ST.append(step(11, "Build", "--build", "wait: approve-plan", "Approve the plan; the implement loop runs",
               "From here the agent writes code, in Kiran's priorauth-api clone, until ./scripts/verify.sh exits 0.", f"Meena · implement {nodechip('implement')}",
               io(cmdbox(f"archon workflow approve {RID} {APP_PLAN}", None, "any shell"),
                  see(x(progress("approve-plan")), f"real · node progress, {S['approve-plan']['seconds'] / 60:.0f} minutes in all", "Archon returns"))
               + gate("Wait 3 answered: the code plan", "<code>stop-plan</code> is skipped (<code>when</code> is false); <code>implement</code> runs.", "Meena Iyer")
               + see(x(art("implementation.md")), "real · $ARTIFACTS_DIR/implementation.md, written by the implement pass", "Claude wrote")
               + plain("The loop allowed three passes; one was enough. After the pass, Archon ran <code>./scripts/verify.sh</code> itself (<code>until_bash</code>), got exit 0, and moved on. The agent saying \"done\" counts for nothing; the script does. "
                       f"The agent made the branch <code>{BRANCH}</code> in priorauth-api and committed there (<code>{FEAT}</code>); the workspace repo stayed clean.")))

lang = {"java": "java", "yml": "yaml", "json": "json"}
ST.append(step(12, "Build", "--build", "checks · review", "The checks node, and a second agent reviews: READY",
               "A bash node re-runs the check and prints priorauth-api's branch, log and diffstat; a read-only review node judges the change against the requirements.", f"checks {nodechip('checks')} · review {nodechip('review')}",
               see(x(fold(W5["message"].split("Checks:", 1)[1].split("Approve to push")[0]).strip()), "real · the checks node's output", "Archon returns")
               + see(x(W5["message"].split("Checks:", 1)[0].strip()), "real · the review, in the last wait's message", "Archon returns")
               + tabs("rev", [("review.md", "$ARTIFACTS_DIR/review.md", "real · review node", "md", art("review.md")),
                              ("the commit", f"git show {FEAT}", "real · priorauth-api", "diff", PATCH[FEAT])])
               + note("READY, with notes. The review read the diff and the tests; it did not run the packaged jar or call the API over HTTP, and said so. <code>review</code> declares <code>mutates_checkout: false</code>, so Archon would have failed it had it changed a file.")))

# ================= Review =================
ST.append(step(13, "Review", "--review", "ours", "Check the packaged jar by hand: a 500",
               "Before approving, Kiran runs the jar and tries the inputs the review only read about.", "Kiran · 2 min",
               io(cmdbox("cd priorauth-api\nmvn -q -DskipTests package\njava -jar target/priorauth-api-1.0.2.jar --server.port=8093\ncurl -i \"http://localhost:8093/requests/pending?asOf=2026-10-13\"\ncurl -i \"http://localhost:8093/requests/pending?asOf=2026-10-05\"\ncurl -i \"http://localhost:8093/requests/pending?asOf=%2B999999999-12-31\"", None, "Git Bash"),
                  see(x(JAR1.strip()), "real", "the jar returns"), stack=True)
               + note('7 and over, 4, 1: the same numbers as the AI-DLC run\'s answer key (v1.1.0), with the 12 Oct holiday counted. An as-of before a received date is a 400, as FR11 says. But <code>asOf=+999999999-12-31</code> parses as a date and the count overflows: <b>500</b>. The old run\'s review caught exactly this; this run\'s review said READY. Compare: <a href="../../ai-dlc-execution/aidlc-hello-world-java/aidlc-hello-world-java-run.html">the AI-DLC run</a>.')))

ST.append(step(14, "Review", "--review", "wait: reject → cancel", "Reject the change; the run is cancelled",
               "Here reject goes to a cancel: node. The run ends; the branch and its commit stay in priorauth-api for the fix.", "Meena",
               io(cmdbox(f"archon workflow reject {RID} {REJ_CHANGE}", None, "any shell"),
                  see(x("\n".join(ln for ln in S["reject-change"]["stdout"].splitlines() if re.match(r"^(❌|⚠️|\s+(Usage|Cost|Input|Output))", ln)) + "\n\n" + progress("reject-change") + "\n" + "\n".join(ln for ln in S["reject-change"]["stderr"].splitlines() if ln.startswith(("Error:", "The rejection")))),
                      "real", "Archon returns"), stack=True)
               + gate("Wait 4 answered: reject", "<code>stop-change</code> ran (<code>cancel: The change was rejected at review.</code>); <code>push</code> was skipped.", "Meena Iyer")
               + note("<b>A misleading message.</b> The run was cancelled exactly as the YAML says, yet the CLI printed <code>Error: Rejected but failed to resume workflow …</code> and suggested <code>bun run cli workflow resume</code> (a source-install command). Nothing failed; <code>archon workflow get</code> shows status <code>cancelled</code>. Don't resume it.")))

ST.append(step(15, "Review", "--review", "bundled workflow", "Fix it with archon-implement, adopting the run",
               "A bundled workflow adopts the cancelled run: its artifacts and its history. In a folder project it works in place, on the branch already checked out.", f"Kiran · {nodechip('implement', FIX_ID)} on claude/opus",
               io(cmdbox(f"archon workflow run archon-implement --adopt {RID} {FIX_MSG}", None, "any shell"),
                  see(x(S["fix-run"]["stdout"].split("Dispatching workflow")[0].strip() + "\n…\n" + json.dumps(FIX_JSON, indent=1) + "\n\nWorkflow finished.\n  Status: completed\n  Authored outcome: succeeded"), f"real · {S['fix-run']['seconds']:.0f}s", "Archon returns"), stack=True)
               + tabs("fix", [("the fix commit", f"git show {FIX}", "real · priorauth-api", "diff", PATCH[FIX])])
               + note("Read the fourth line: <i>folder projects run in place; adoption carries provenance and $ADOPTED_RUN_DIR access only</i>. In a repo project <code>--adopt</code> also takes over the run's worktree and branch; here there is none, so the message tells the agent which branch to stay on. <code>archon-implement</code> asks for the <code>large</code> tier; with no tiers set, Archon used the built-in default, <code>claude/opus</code>.")))

# ================= Ship =================
ST.append(step(16, "Ship", "--ship", "ours", "Check again, push the branch, open the PR",
               "The workflow's push node never ran (the change was rejected there), so Kiran checks and pushes by hand.", "Kiran · 2 min",
               io(cmdbox("./scripts/verify.sh", None, "Git Bash"), see(x(S["verify-fix"]["stdout"].strip()), f"real · {tests} tests", "verify returns"))
               + see(x(JAR2.strip()), "real · the same three curls on the new jar", "the jar returns")
               + io(cmdbox(f"git -C priorauth-api push -u origin {BRANCH}", None, "any shell"),
                    see(x(S["push-by-hand"]["stdout"].strip()), "real · origin is a local bare repo standing in for GitHub", "git returns"))
               + see(x(BRANCH_LOG.strip()), f"real · git log main..{BRANCH}", "The branch")
               + note(f"Both bad dates are 400s now, and the numbers are unchanged. Opening the PR is documented, not run (no <code>gh</code> login): <code>gh pr create --base main --head {BRANCH}</code> in priorauth-api. The branch holds {NFILES} files changed, +{PLUS} −{MINUS}.")))

# ================= After =================
node_rows = []
for n in ROWS:
    node_rows.append([f"<code>{n['node']}</code>", KIND.get(n["node"], "loop pass" if "iteration" in n["node"] else ""), fmt_ms(n["ms"]),
                      f"{n['input']:,}" if n["input"] else "—", f"{n['output']:,}" if n["output"] else "—", f"${n['cost']:.2f}" if n["cost"] else "—"])
PROJECTS = S["project-list"]["stdout"].strip().splitlines()
ST.append(step(17, "After", "--setup", "the record", "What the run left behind",
               "No record in either repo, no worktree: a run row, transcripts and artifacts in ~/.archon. Here is where to find each.", "Kiran · reference",
               io(cmdbox(f"archon workflow runs\narchon workflow get {SHORT}…\narchon project list\narchon isolation list\narchon doctor", None, "any shell"),
                  see(x(S["runs"]["stdout"].strip() + "\n\n" + S["get"]["stdout"].strip() + "\n\n" + PROJECTS[0] + "\n" + next(ln for ln in PROJECTS if "\tjava-workspace\t" in ln)
                        + "\n\n" + S["isolation-list"]["stdout"].strip() + "\n\n" + "\n".join(ln for ln in S["doctor"]["stdout"].splitlines() if "Folder project" in ln or "All checks" in ln)), "real", "Archon returns"))
               + disk(x(STORAGE.strip()), "On disk: ~/.archon/workspaces/ for this project")
               + table(["Node", "Kind", "Time", "Input tokens", "Output tokens", "Cost"], node_rows)
               + note(f"<code>workflow get</code> calls the workspace itself the worktree, marked <i>(live)</i>, and records that the fix run adopted this one. <code>isolation list</code> has nothing to show. <code>project list</code> (one row shown) has this folder project as <code>_folder/java-workspace</code>. "
                      f"Costs are what the provider reported: <b>${COST_MAIN:.2f}</b> for request-to-pr and ${COST_FIX:.2f} for the fix, as API-price equivalents; the run used a claude.ai plan, so nothing was billed per token.")
               + see(x("\n".join(S["logs-text"]["stdout"].splitlines()[:30]) + "\n…"), "real · the transcript as text (first lines)", "Archon returns")))

ST.append(step(18, "After", "--setup", "merge", "Merge, then tidy up by hand",
               "Meena merges the PR. Archon has nothing to complete in a folder project: Kiran switches back to main and deletes his branch.", "Meena, Kiran · 2 min",
               see(x(S["merge"]["stdout"].strip()), "real · the PR merge, done by hand with git merge --no-ff", "git: Meena's merge")
               + io(cmdbox(f"archon complete {BRANCH}", None, "any shell"), see(x(S["complete"]["stdout"].strip()), "real", "Archon returns"))
               + io(cmdbox(f"git -C priorauth-api switch main; git -C priorauth-api pull\n./scripts/verify.sh\ngit -C priorauth-api branch -d {BRANCH}", None, "Git Bash"),
                    see(x(S["verify-main"]["stdout"].strip() + "\n" + S["cleanup"]["stdout"].strip()), f"real · {tests} tests on main", "git returns"))
               + note("In a repo project <code>archon complete &lt;branch&gt;</code> removes the run's worktree and local branch once the work is merged. Here there is no isolation environment, so it finds nothing: the branch was the agent's, made in Kiran's clone, and so is the tidy-up.")))

plan_art = art("plan.md", PLAN_ID)
AP = S["archon-plan"]["stdout"]
AP_DECISION = json.loads(re.search(r'(\{"decision".*?\})\n', AP).group(1))
assert AP_DECISION["decision"] == "done" and "4ca6b6a" in AP_DECISION["reason"] and "Workflow finished." in AP
ST.append(step(19, "After", "--setup", "bundled workflow", "The same request through archon-plan",
               "For comparison: the bundled planner, read-only, from the same workspace after the merge. It found the work already done.", f"Kiran · {S['archon-plan']['seconds']:.0f}s",
               io(cmdbox('archon workflow run archon-plan --folder "Plan the request in docs-in/request.md"', None, "any shell"),
                  see(x(progress("archon-plan") + "\n\n" + json.dumps(AP_DECISION, indent=1) + "\n\nWorkflow finished.\n" + AP.split("Workflow finished.", 1)[1].strip()), f"real · {S['archon-plan']['seconds']:.0f}s", "Archon returns"), stack=True)
               + tabs("aplan", [("plan.md", "$ARTIFACTS_DIR/plan.md", "real · archon-plan", "md", plan_art)])
               + three([("It found", "the request already met by Meena's merge on priorauth-api's main, and the check passing"), ("It asked", "nothing that stops a run: one open question, the version, marked non-blocking"),
                        ("It ran", "a planning cycle on <code>claude/opus</code> (the <code>large</code> tier) and a decision on <code>claude/sonnet</code> (<code>medium</code>)")])
               + note("The bundled pack is opinionated: questions only a person can answer would stop the run as one attention item (what, why, a recommendation, the choices); here there were none. The team's own workflow put that kind of question in its first wait. Run before the change, the planner would have planned it; run after, it checked the repo and said so.")))

ST.append(step(20, "After", "--setup", "compare", "Same request: AI-DLC and Archon",
               "One change, two tools, the same layout: a workspace around the repo. What each made you do, and what each left behind.", "read · 3 min",
               table(["", "AI-DLC 2.11 (express)", "Archon 0.13.2 (request-to-pr)"], [
                   ["Where you type", "<code>/aidlc …</code> inside Claude Code", "<code>archon workflow …</code> in a terminal (or the Web UI)"],
                   ["The workspace", "<code>java-workspace/</code>: CLAUDE.md, repos.json, <code>aidlc/</code>, the repo cloned inside", "<code>java-workspace/</code>: CLAUDE.md, <code>.archon/</code>, the repo cloned inside (a folder project)"],
                   ["The process", "the engine's 33 stages, 10 used by express", "the team's 15-node YAML, written for this"],
                   ["Stops for people", "4 gates + the plan stop", "4 waits (answers, requirements ×2, plan, change)"],
                   ["Request Changes", "option 2 at a gate", "reject inside a loop_group"],
                   ["The check", "<code>scripts/verify.sh</code>, recorded at Code Generation", "<code>until_bash: ./scripts/verify.sh</code> on the loop"],
                   ["A second reader", "the quality persona re-ran the tests", "the review node: READY; the 500 was found by Kiran's jar check"],
                   ["Git in the repo", "the agent, on a branch in the cloned repo", f"the agent, on <code>{BRANCH}</code> in the cloned repo; no worktree"],
                   ["The record", "<code>aidlc/</code>, committed with the workspace", "artifacts + transcript in <code>~/.archon</code>, not committed"],
                   ["Result", "12 files, 9 tests (answer key v1.1.0)", f"{NFILES} files, {tests} tests, the same three numbers"]])
               + plain("AI-DLC gives you a method with its stages and record already decided. Archon gives you an engine and asks you to write the method down. The same team rules (CLAUDE.md, one verify script, people approve) and the same workspace worked in both.")))

STEPS = [(1, "The code repo's remote"), (2, "The workspace repo"), (3, "Kiran's clones"), (4, "Before: valid, green"), (5, "Read request and workflow"),
         (6, "Dry-run it"), (7, "Start: scan and questions"), (8, "Answer the questions"), (9, "Reject the requirements"), (10, "Approve; the plan"),
         (11, "Approve the plan; implement"), (12, "Checks and review: READY"), (13, "The jar by hand: a 500"), (14, "Reject; cancelled"),
         (15, "Fix with archon-implement"), (16, "Check, push, open the PR"), (17, "What the run left"), (18, "Merge; tidy up"),
         (19, "archon-plan, for comparison"), (20, "AI-DLC vs Archon")]
PH = {n: ("Set up", "--setup") for n in range(1, 7)} | {n: ("Plan", "--plan") for n in range(7, 11)} | {n: ("Build", "--build") for n in (11, 12)} | \
     {n: ("Review", "--review") for n in (13, 14, 15)} | {n: ("Ship", "--ship") for n in (16,)} | {n: ("After", "--setup") for n in range(17, 21)}
assert len(ST) == len(STEPS)

hero = f'''<section class="hero" id="top">
  <div>
    <h1>One request through Archon, every step, for real.</h1>
    <p class="lead">Ravi asks for the request age on the API's pending list. Kiran sets up the team's workspace with priorauth-api cloned inside it, and runs the team's Archon workflow from there: Archon scans, asks, writes requirements that Meena sends back once, plans, implements until the tests pass, and has a second agent review. Kiran's own check of the jar finds a bug the review missed. Every command, every reply and every file below is from that run (Archon 0.13.2, Claude Code, 4 Nov 2026).</p>
    <div class="facts">
      <div><b>20</b>steps, setup included</div>
      <div><b>15</b>nodes, 4 of them waits</div>
      <div><b>5</b>answers by people</div>
      <div><b>3</b>runs: the workflow, a fix, a comparison</div>
      <div><b>{tests}</b>tests on main after the merge</div>
      <div><b>1</b>bug the review missed, found by hand</div>
    </div>
    <div class="legend">
      <div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--you)"><rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M8 14h8"/></svg><div><b>You type</b>In a terminal. Switch Windows/macOS at the top.</div></div>
      <div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--ink-2)"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg><div><b>Archon returns</b>Real output, paths mapped to <code>C:\\Users\\you</code> and <code>C:\\work</code>.</div></div>
      <div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--gate)"><path d="M12 3l9 9-9 9-9-9z"/></svg><div><b>Wait answered</b>Where a person decided, and who.</div></div>
      <div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--setup)"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg><div><b>On disk now</b>Where things landed. <span style="color:var(--new);font-weight:600">Green</span> is new.</div></div>
    </div>
  </div>
  <aside class="slack" aria-label="The request, as it arrived in Slack">
    <div class="slack__bar"><span># prior-auth-platform</span><span>Tue 13 Oct</span></div>
    <div class="slack__body">
      <div class="slack__who"><i>RM</i><div><b>Ravi Menon</b><span>Nurse Manager, Utilization Management · 09:10</span></div></div>
      <p>The nightly report shows the AGE column now, thank you. The reviewer screen still shows nothing, and it reads from priorauth-api. Can the pending list the API returns carry the same business-day age and the over-5 flag, so the screen can show it? Same rule as the report: weekends and our holidays do not count. Nothing else changes.</p>
    </div>
  </aside>
</section>
'''
# What each AI node handed Claude Code: the shared mapping (asserted against tools/data/docs/), and, from the three
# transcripts, every Claude Code session the course's runs started and the tools its agent called.
claude_facts()


def cc_sessions(rid):
    """[(node, prompt source, model asked for, session origin, {tool: count})] for each agent/loop node start of one run."""
    log = next((RUN / "logs").glob(f"{rid}*.jsonl")).read_text(encoding="utf-8")
    rows, subtasks = [], set()
    for ln in log.splitlines():
        d = json.loads(ln)
        if d.get("workflow_id") != rid:
            continue
        if d.get("type") == "node_start" and d["execution"]["node"]["kind"] in ("agent", "loop"):
            n, b = d["execution"]["node"], d["execution"]["binding"]
            assert b["provider"] == "claude" and not n.get("skills"), (rid, n, b)
            cmd = n.get("command") or (n.get("source") or {}).get("name")
            src = (f"<code>command: {cmd.rsplit('::', 1)[1]}</code> " + ("(the team's <code>commands/</code>)" if "__archon_pack__project:" in cmd else "(bundled sdlc pack)")) if cmd else "<code>prompt:</code> in the YAML"
            rows.append([d["step"], src, b["model"].get("requested") or "default", b["sessionOrigin"], {}])
        if d.get("type") == "provider_event":
            e = d["event"]
            if e.get("type") == "tool_call":
                rows[-1][4][e["name"]] = rows[-1][4].get(e["name"], 0) + 1
            if e.get("type") == "subtask":
                subtasks.add(e.get("taskType") or "")
    assert rows and not any({"Skill", "Task", "Agent"} & set(r[4]) for r in rows), rid
    assert subtasks <= {"local_bash", ""}, subtasks  # background shell commands of the session, not subagents
    return rows


CC = {rid: cc_sessions(rid) for rid in (RID, FIX_ID, PLAN_ID)}
assert [(r[0], r[3]) for r in CC[RID]] == [("scan", "fresh"), ("questions", "resumed"), ("write-requirements", "fresh"), ("write-requirements", "resumed"),
                                         ("plan", "fresh"), ("implement", "fresh"), ("review", "fresh")]
assert [(r[0], r[2]) for r in CC[PLAN_ID]] == [("stage__plan", "opus"), ("attend__decide", "sonnet")], CC[PLAN_ID]
assert [r[0] for r in CC[FIX_ID]] == ["implement"] and CC[FIX_ID][0][2] == "opus"
assert sum(r[4].get("StructuredOutput", 0) for r in CC[RID]) == 3
assert [r[0] for r in CC[RID] if "team's" in r[1]] == ["scan", "implement"] and "bundled" in CC[FIX_ID][0][1]
assert not re.search(r"^\s*(skills|agents|hooks|mcp|plugins):", WF_TEXT, re.M) and not (WS / ".claude").exists() and (WS / "CLAUDE.md").exists()
CC_STEP = {"scan": 7, "questions": 7, "write-requirements": 8, "plan": 10, "implement": 11, "review": 12}
cc_rows, _seen = [], set()
for rid, label in [(RID, "<code>request-to-pr</code>"), (FIX_ID, "<code>archon-implement</code>, step 15"), (PLAN_ID, "<code>archon-plan</code>, step 19")]:
    for node, src, model, origin, tools in CC[rid]:
        nm = node.split(".")[-1]
        if rid == RID:
            nm_txt = f"<code>{nm}</code>" + (" (revision 2)" if (rid, nm) in _seen else "") + f", step {CC_STEP[nm] + (1 if (rid, nm) in _seen else 0)}"
        else:
            nm_txt = f"<code>{nm}</code>"
        _seen.add((rid, nm))
        cc_rows.append([label, nm_txt, src, model, {"fresh": "new", "resumed": "continued the one before"}[origin],
                        ", ".join(f"{k} {v}" for k, v in sorted(tools.items(), key=lambda kv: -kv[1]))])
N_SESS = len(cc_rows)
ccard = card("claude", "What each AI node handed Claude Code",
             f"<p>Archon's Claude provider starts Claude Code through the Claude Agent SDK, with Kiran's claude.ai login: <b>each AI node, and each loop pass, is one Claude Code session</b> in the workspace. The course's three runs started {N_SESS} of them. From their transcripts (real):</p>"
             + table(["Run", "Node", "Its prompt", "Model asked for", "Session", "Tool calls"], cc_rows)
             + note("No session called <code>Skill</code> or <code>Task</code>: none of the workflows names <code>skills:</code> or <code>agents:</code>, and the workspace has no <code>.claude/</code> folder, so the one Claude Code file every session read was the workspace's <code>CLAUDE.md</code>. The transcripts' <i>subtasks</i> are the agent's background shell commands, not subagents. Both bundled workflows ask for a model per node (a tier: <code>opus</code> for planning and implementing, <code>sonnet</code> for <code>archon-plan</code>'s decision); <code>request-to-pr</code> names none, so Claude Code's default ran.")
             + "<p style=\"margin-top:14px\"><b>What each workflow field hands the session</b> (the third column is <code>request-to-pr</code>):</p>"
             + table(["In the workflow", "What Claude Code gets", "In the course's run"], [list(r_) for r_ in CLAUDE_MAP], "kv")
             + note("Checked against the Archon 0.13.2 docs (workflow language, skills, hooks, authoring commands, security). More: <a href=\"../archon-introduction.html#s11\">the introduction, step 11</a>, and where Claude Code's own files go in a workspace: <a href=\"../archon-workspace-setup.html#claude\">the setup page</a>."))
glossary = card("glossary", "Ten words", gloss([(w, ARCHON_WORDS[w]) for w in (
    "workflow", "node", "run", "wait", "form", "loop_group", "until_bash", "workspace", "folder project", "artifacts")]))
yourself = card("yourself", "Run it yourself", f"""<ol>
<li>Install Archon and the Claude provider, and check with <code>archon doctor</code> (<a href="../archon-workspace-setup.html">setup page</a>, steps 1–4).</li>
<li>Make the workspace as in steps 1–3, or start from the course repo's <code>archon-hello-world-java/java-workspace/</code>: the team's files with priorauth-api inside, as they are after this run. To start where the run started, put priorauth-api back to the starter (<code>git clone --no-tags https://github.com/varasrinivas/aidlc-priorauth-api priorauth-api</code> inside the workspace).</li>
<li>Start the run as in step 7, from the workspace root, and answer each wait. Your questions and wording will differ: the agent is not deterministic. Use the answers from steps 8–11 so the requirements land where the course's did.</li>
<li>Check the jar by hand as in step 13, then compare with <code>java-workspace/priorauth-api/</code>: the code, the tests ({tests}), and the curl numbers.</li></ol>
{note("Your run ids, times, costs and commit hashes will differ. The course's transcripts are in <code>java-run/logs/</code> and its artifacts in <code>java-run/artifacts/</code>.")}""")
real = card("real", "What is real here", """<p>Everything in the Archon and git boxes is real output from the course's run on Windows (4 Nov 2026, Archon 0.13.2, Claude Code on a claude.ai plan), setup included, captured by <code>tools/archon_step.py</code> and copied by <code>tools/capture_java_run.py</code>. Local paths are mapped to <code>C:\\Users\\you</code> and <code>C:\\work</code>; long Spring Boot test logs are folded. The macOS commands are the documented equivalents and were not run.</p>
<p>Not run: opening the PR (no <code>gh</code> login; the remotes are local bare repos standing in for GitHub), and the PR merge, which was a plain <code>git merge --no-ff</code>. The people are fictional; their answers were typed by the course author.</p>""")

main = (hero + phase("--setup", "Set up", "steps 1–6 · the remotes, the workspace, the clones, the request, a dry run") + "".join(ST[0:6])
        + phase("--plan", "Plan", "steps 7–10 · scan, questions, requirements, plan") + "".join(ST[6:10])
        + phase("--build", "Build", "steps 11–12 · implement until the check passes, then review") + "".join(ST[10:12])
        + phase("--review", "Review", "steps 13–15 · a 500 by hand, a cancel, a fix") + "".join(ST[12:15])
        + phase("--ship", "Ship", "step 16 · check again, push, PR") + "".join(ST[15:16])
        + phase("--setup", "After", "steps 17–20 · the record, the merge, a comparison") + "".join(ST[16:20])
        + yourself + ccard + glossary + real)
footer = ('<footer class="foot">Archon, Java edition · Archon 0.13.2 · <a href="archon-two-repos-run.html">the two-repo run</a> · <a href="../archon-introduction.html">introduction</a> · <a href="../archon-concepts-explained.html">concepts</a> · '
          '<a href="../archon-workspace-setup.html">setup</a> · <a href="../index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Archon, Java Edition: Every Step", "One small requirement taken through an Archon workflow from a team workspace with a Spring Boot repo inside it, step by step: the setup, what you type, what Archon and Claude return, every wait and who answered it, and what lands on disk. Real run, real code, real output.",
             "Archon, Java edition", "one request · every step · real run", len(STEPS),
             rail(STEPS, PH, [("yourself", "Run it yourself"), ("claude", "What Claude Code got"), ("glossary", "Ten words"), ("real", "What is real here")]), main, footer)
write(DEST / "archon-hello-world-java-run.html", html_)
