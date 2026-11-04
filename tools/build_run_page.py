"""Build archon-hello-world-java/archon-hello-world-java-run.html: Ravi's request taken through Archon, step by step.

Everything comes from the course's real run (3 Nov 2026, Archon 0.13.2, Claude Code on a claude.ai login), copied into
archon-hello-world-java/java-run/ by capture_java_run.py: steps.json (every command Kiran typed and what came back),
nodes.json (per node: time, tokens, cost, from the transcripts), artifacts/ (what each run wrote), git/ (commits and diffs),
and java-workspace/ (the repo at the end of the branch). The asserts tie the page's numbers to that data.

Usage: py -3.12 tools/build_run_page.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli_parse import workflow_nodes  # noqa: E402
from diagrams import workflow_dag  # noqa: E402
from pagekit import (DOC, E, REAL, ROOT, card, disk, gate, io, note, page, phase, plain, rail, see, step, table, tabs,  # noqa: E402
                     three, write, you)

DEST = ROOT / "archon-hello-world-java"
RUN = DEST / "java-run"
WS = DEST / "java-workspace"
S = {s["label"]: s for s in json.loads((RUN / "steps.json").read_text(encoding="utf-8"))}
SETUP = {s["label"]: s for s in json.loads((RUN / "setup-steps.json").read_text(encoding="utf-8"))}
NODES = json.loads((RUN / "nodes.json").read_text(encoding="utf-8"))
MAIN_ID = "cd54631b99f7e43dc9739bb63499690f"
FIX_ID = next(k for k, v in NODES.items() if v["workflow"] == "archon-implement")
PLAN_ID = next(k for k, v in NODES.items() if v["workflow"] == "archon-plan")
ART = RUN / "artifacts" / MAIN_ID
WF_TEXT = (WS / ".archon/workflows/team/request-to-pr/request-to-pr.yaml").read_text(encoding="utf-8")
WFN = workflow_nodes(WF_TEXT)
KIND = {n["id"]: n["kind"] for n in WFN}
GIT = RUN / "git"
BRANCH_LOG = (GIT / "branch-log.txt").read_text(encoding="utf-8")
COMMITS = re.findall(r"^([0-9a-f]{7}) ", BRANCH_LOG, re.M)
PATCH = {p.stem.split("-")[1]: p.read_text(encoding="utf-8") for p in GIT.glob("commit-*.patch")}
assert len(COMMITS) == 2 and set(COMMITS) <= set(PATCH), (COMMITS, list(PATCH))
FEAT, FIX = COMMITS[1], COMMITS[0]  # git log lists newest first

# ---------- facts the page states, checked against the data ----------
assert len(WFN) == 15 and sum(1 for n in WFN if n["kind"] == "wait") == 4
assert "Started 'request-to-pr' in the background." in S["run"]["stdout"]
assert '"nodeId": "answer"' in S["wait-1"]["stdout"]
assert "Workflow cancelled" in S["reject-change"]["stdout"] and "Rejected but failed to resume" in S["reject-change"]["stderr"]
assert '"verdict":"NOT-READY"' in S["approve-plan"]["stdout"]
assert "Loop node 'implement' completed after 1 iteration" in S["approve-plan"]["stdout"]
assert '"green":true' in S["fix-run"]["stdout"] and "24 tests pass" in S["fix-run"]["stdout"]
assert '"ageBusinessDays":7,"overLimit":true,"ageLabel":"7 bd OVER 5"' in S["curl"]["stdout"]
assert "HTTP/1.1 400" in S["curl"]["stdout"]
assert "Blocked: request-age/age-api" in S["complete"]["stderr"] and "2 commit(s) unique to this branch" in S["complete"]["stderr"]
assert "Completed: request-age/age-api" in S["complete-after-merge"]["stdout"]
tests = sum(int(m) for m in re.findall(r"Tests run: (\d+), Failures: 0", S["verify-main"]["stdout"]))
assert tests == 24, tests
assert S["checkout-untouched"]["stdout"].split()[0] == "main"
ROWS = [n for n in NODES[MAIN_ID]["nodes"] if n["event"] == "node_complete"]
COST_MAIN = sum(n["cost"] or 0 for n in ROWS)
COST_FIX = sum(n["cost"] or 0 for n in NODES[FIX_ID]["nodes"] if n["event"] == "node_complete" and n["node"] == "implement")
assert abs(COST_MAIN - 3.3116) < 0.01, COST_MAIN
ITER = {}
for n in ROWS:
    ITER[n["node"]] = ITER.get(n["node"], 0) + 1
assert ITER["write-requirements"] == 2 and ITER["review-requirements"] == 2
DIFFSTAT = (GIT / "diffstat.txt").read_text(encoding="utf-8").strip()
m = re.search(r"(\d+) files changed, (\d+) insertions\(\+\), (\d+) deletions", DIFFSTAT)
NFILES, PLUS, MINUS = map(int, m.groups())


def x(s):
    return E(s)


def pause(label):
    """The attention block a step ended on (from the pause marker to the end), Spring test logs folded."""
    o = S[label]["stdout"]
    i = o.rfind("⏸️")
    return fold(o[i:].strip()) if i >= 0 else ""


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
    return "\n".join(out)


def progress(label, extra=()):
    lines = [ln for ln in (S[label]["stderr"]).splitlines() if re.match(r"^\[(?!workflow)[\w-]+\] ", ln)]
    return "\n".join(list(extra) + lines)


def nd(node, run=MAIN_ID, i=-1):
    rows = [n for n in NODES[run]["nodes"] if n["node"] == node and n["event"] == "node_complete"]
    return rows[i]


def fmt_ms(ms):
    s = round((ms or 0) / 1000)
    return f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"


def nodechip(node, run=MAIN_ID, i=-1):
    r = nd(node, run, i)
    c = f" · ${r['cost']:.2f}" if r["cost"] else ""
    return f"{fmt_ms(r['ms'])}{c}"


def art(name, run=MAIN_ID):
    return (RUN / "artifacts" / run / name).read_text(encoding="utf-8")


def wsf(rel):
    return (WS / rel).read_text(encoding="utf-8")


def cmdbox(win, mac=None, tag="PowerShell", mac_tag="Terminal"):
    return you(x(win), x(mac if mac is not None else win), tag, mac_tag if mac is not None else tag)


RID = "cd54631b99f7e43dc9739bb63499690f"
SHORT = RID[:8]
ANSWER_TEXT = re.search(r'--text "(.*)"$', S["answer-1"]["cmd"], re.S)
ANSWER_TEXT = S["answer-1"]["cmd"].split("--text ", 1)[1]
REJ_REQ = S["reject-requirements"]["cmd"].split(RID + " ", 1)[1]
APP_REQ = S["approve-requirements"]["cmd"].split(RID + " ", 1)[1]
APP_PLAN = S["approve-plan"]["cmd"].split(RID + " ", 1)[1]
REJ_CHANGE = S["reject-change"]["cmd"].split(RID + " ", 1)[1]
FIX_MSG = S["fix-run"]["cmd"].split(RID + " ", 1)[1]
WAIT1 = json.loads(S["wait-1"]["stdout"])["attention"]
QUESTIONS = WAIT1["message"]
OCC = WAIT1["occurrence"]

ST = []
# ================= Set up =================
ST.append(step(1, "Set up", "--setup", "ours", "Clone the repo and add the team's files",
               "Everything Archon needs is in the repo. The setup page explains each file; here they are in one go.", "Kiran · 5 min", f"""
{io(cmdbox("git clone --single-branch --no-tags https://github.com/varasrinivas/aidlc-priorauth-api priorauth-api\ncd priorauth-api\n# write the nine team files: setup page, step 6\narchon validate workflows request-to-pr\ngit add -A\ngit commit -m \"Add the team's Archon files: CLAUDE.md, verify scripts, request-to-pr workflow\"",
           "git clone --single-branch --no-tags https://github.com/varasrinivas/aidlc-priorauth-api priorauth-api\ncd priorauth-api\n# write the nine team files: setup page, step 6\narchon validate workflows request-to-pr\ngit add -A\ngit commit -m \"Add the team's Archon files: CLAUDE.md, verify scripts, request-to-pr workflow\""),
     see(x(SETUP["validate"]["stdout"].strip()), "real", "Archon returns"))}
{disk('''priorauth-api/
├── <span class="n">.archon/config.yaml</span>
├── <span class="n">.archon/workflows/team/request-to-pr/</span>
│   ├── <span class="n">request-to-pr.yaml</span>          <span class="m">15 nodes, 4 waits</span>
│   └── <span class="n">commands/scan.md, implement.md</span>
├── <span class="n">CLAUDE.md</span>   <span class="n">.gitattributes</span>
├── <span class="n">scripts/verify.sh</span>, <span class="n">verify.cmd</span>
├── <span class="n">docs-in/request.md</span>
└── pom.xml, src/ …                 <span class="m">v1.0.2: GET /requests/pending, no age</span>''')}
{note('Full walk-through with every file: <a href="../archon-workspace-setup.html#s06">setup page, steps 5–8</a>. You need Archon with the Claude provider, Claude Code signed in, JDK 21 and Maven, and on Windows Git Bash where Archon finds it.')}
"""))

ST.append(step(2, "Set up", "--setup", "the request", "Read the request and the workflow",
               "Ravi's Slack message is the input; the workflow is the process it will go through.", "Kiran · 2 min",
               tabs("req", [("request.md", "docs-in/request.md", "Ravi's Slack message · real input", "md", wsf("docs-in/request.md")),
                            ("request-to-pr.yaml", ".archon/workflows/team/request-to-pr/request-to-pr.yaml", "the team's workflow", "yaml", WF_TEXT),
                            ("scan.md", ".archon/workflows/team/request-to-pr/commands/scan.md", "the scan node's prompt", "md", wsf(".archon/workflows/team/request-to-pr/commands/scan.md")),
                            ("implement.md", ".archon/workflows/team/request-to-pr/commands/implement.md", "each implement pass's prompt", "md", wsf(".archon/workflows/team/request-to-pr/commands/implement.md"))])
               + workflow_dag(WFN, "request-to-pr: the 15 nodes this run goes through", {
                   "scan": "step 4", "questions": "step 4", "answer": "step 5", "plan": "step 7", "approve-plan": "step 8",
                   "checks": "step 9", "review": "step 9", "approve-change": "step 11", "push": "skipped: step 11"})
               + plain("The request is the order slip, the workflow is the recipe. Every arrow in the drawing is a <code>depends_on</code>; every dashed box is a moment the kitchen stops until someone says go.")))

ST.append(step(3, "Set up", "--setup", "free check", "Dry-run it first",
               "Walk the graph with stub outputs: no run, no model call, no cost.", "Kiran · 1 min",
               io(cmdbox('archon workflow run request-to-pr --dry-run --default-stubs "Implement the request in docs-in/request.md"', None, "any shell"),
                  see(x(S["dry-run"]["stdout"].split("STUBBED   questions")[0].strip()[:1500] + "\n…\nPAUSED    answer (wait) — durable wait\n…\nSimulation outcome: paused"), f"real · {S['dry-run']['seconds']}s", "Archon returns"))
               + note("The dry run shows each node's prompt with its variables filled in (<code>$USER_MESSAGE</code>, <code>$ARTIFACTS_DIR</code>) and stops at the first wait. It caught nothing here; it is how you catch a misspelt <code>$node.output</code> before it costs a run.")))

# ================= Plan =================
ST.append(step(4, "Plan", "--plan", "scan · questions", "Start the run: Archon scans the repo and asks its questions",
               "One command. Archon cuts a branch and a worktree, then the scan and questions nodes run and the run pauses at the first wait.", f"Kiran · scan {nodechip('scan')} · questions {nodechip('questions')}", f"""
{io(cmdbox('archon workflow run request-to-pr --branch request-age/age-api --detach "Implement the request in docs-in/request.md"\narchon workflow wait ' + RID + ' --json', None, "any shell"),
     see(x(S["run"]["stdout"].strip()), "real", "Archon returns"))}
{see(x(json.dumps(dict(list(WAIT1.items())[:3] + [("message", "(below)"), ("occurrence", OCC), ("form", WAIT1["form"])]), indent=2)), f"real · abridged: the attention object of archon workflow wait --json, {S['wait-1']['seconds']}s later", "Archon returns")}
{tabs("q", [("the questions (the wait's message)", "attention: $questions.output.questions", "real · questions node", "md", QUESTIONS.split(chr(10) + chr(10), 1)[1]),
            ("scan.md", "$ARTIFACTS_DIR/scan.md", "real · written by the scan node", "md", art("scan.md"))])}
{disk('''C:\\Users\\you\\.archon\\workspaces\\_local\\priorauth-api\\
├── <span class="n">worktrees/request-age/age-api/</span>     <span class="m">a second checkout, on branch request-age/age-api</span>
├── <span class="n">logs/''' + RID + '''.jsonl</span>
└── <span class="n">artifacts/runs/''' + RID + '''/</span>
    ├── <span class="n">scan.md</span>
    └── <span class="n">questions.md</span>''', "On disk now (not in the repo)")}
{three([("The AI asked", "six questions: holidays, how to count, what over 5 means, field names, which day is today, one rule or per tenant"),
        ("It suggested", "an answer for each, with the reason"), ("Nobody decided yet", "the run is paused; it holds no process")])}
{note("<code>_local</code> in the path: the repo's remote is a folder, not GitHub, so Archon files the project under <code>_local/&lt;name&gt;</code>. With a GitHub remote it is <code>&lt;owner&gt;/&lt;repo&gt;</code>. Kiran's own checkout stayed on <code>main</code> the whole run.")}
"""))

ST.append(step(5, "Plan", "--plan", "wait: answer", "Answer the six questions",
               "A message-form wait: one free-text answer. Kiran writes what Ravi and Meena decided.", f"Kiran · write-requirements {nodechip('write-requirements', i=0)}",
               io(cmdbox(f'archon workflow answer {RID} --occurrence {OCC} --text "{ANSWER_TEXT.strip(chr(34))}"', None, "any shell"),
                  see(x(pause("answer-1")), f"real · the run continued in this terminal for {S['answer-1']['seconds']:.0f}s, then paused again", "Archon returns"), stack=True)
               + gate("Wait 1 answered: the questions", "Answered from the CLI with the occurrence id from step 4, so the answer can't land on a later pause by mistake.", "Kiran Rao, for Ravi Menon and Meena Iyer")
               + note("The first requirements already match the AI-DLC run's worked check: as of 2026-10-13, PA-10231 is 7 and over, PA-10244 is 4, PA-10263 is 1. But the field names are the AI's guess (<code>overFiveBusinessDays</code>), and the screen team has already named them.")))

ST.append(step(6, "Plan", "--plan", "wait: reject → revise", "Reject the requirements with the screen team's names",
               "Reject is an answer. Inside the requirements loop_group it means: write them again with this text, and ask again.", f"Meena · write-requirements {nodechip('write-requirements')}",
               io(cmdbox(f"archon workflow reject {RID} {REJ_REQ}", None, "any shell"),
                  see(x(pause("reject-requirements")), f"real · {S['reject-requirements']['seconds']:.0f}s", "Archon returns"), stack=True)
               + gate("Wait 2, first answer: reject", "The loop_group's <code>until_bash</code> saw decision <code>reject</code>, so it ran another pass: <code>write-requirements</code> read the text as <code>$LOOP_PREV.review-requirements.output.text</code> and revised.", "Meena Iyer")
               + three([("Changed", "fields <code>ageBusinessDays</code>, <code>overLimit</code>, <code>ageLabel</code>; key <code>priorauth.aging.threshold-days</code>; files <code>data/holidays-&lt;tenant&gt;-&lt;year&gt;.json</code>"),
                        ("New rule", "an as-of before the received date is a 400 (FR8)"), ("Still open", "the label when not over the limit, a request received after today")])))

ST.append(step(7, "Plan", "--plan", "wait: approve", "Approve the requirements; the plan is written",
               "Approve ends the loop. The plan node writes plan.md and the run stops before any code.", f"Ravi + Meena · plan {nodechip('plan')}",
               io(cmdbox(f"archon workflow approve {RID} {APP_REQ}", None, "any shell"),
                  see(x(pause("approve-requirements")), f"real · {S['approve-requirements']['seconds']:.0f}s", "Archon returns"), stack=True)
               + tabs("req2", [("requirements.md", "$ARTIFACTS_DIR/requirements.md", "real · revision 2, approved", "md", art("requirements.md")),
                               ("plan.md", "$ARTIFACTS_DIR/plan.md", "real · plan node", "md", art("plan.md"))])
               + gate("Wait 2 answered: approve", "The answer's text records who approved and the two open points they settled.", "Ravi Menon and Meena Iyer")))

# ================= Build =================
ST.append(step(8, "Build", "--build", "wait: approve-plan", "Approve the plan; the implement loop runs",
               "From here the agent writes code, in the worktree, until ./scripts/verify.sh exits 0.", f"Meena · implement {nodechip('implement')}",
               io(cmdbox(f"archon workflow approve {RID} {APP_PLAN}", None, "any shell"),
                  see(x(progress("approve-plan")), f"real · node progress, {S['approve-plan']['seconds'] / 60:.0f} minutes in all", "Archon returns"))
               + gate("Wait 3 answered: the code plan", "<code>stop-plan</code> is skipped (<code>when</code> is false); <code>implement</code> runs.", "Meena Iyer")
               + see(x(art("implementation.md")), "real · $ARTIFACTS_DIR/implementation.md, written by the implement pass", "Claude wrote")
               + plain("The loop allowed three passes; one was enough. After the pass, Archon ran <code>./scripts/verify.sh</code> itself (<code>until_bash</code>), got exit 0, and moved on. The agent saying \"done\" counts for nothing; the script does.")))

FEAT_FILES = ["src/main/java/com/acmehealth/priorauth/api/RequestAge.java", "src/main/java/com/acmehealth/priorauth/api/HolidayCalendar.java",
              "src/main/java/com/acmehealth/priorauth/api/PendingRequestsController.java", "src/main/java/com/acmehealth/priorauth/api/PendingRequestResponse.java",
              "src/main/resources/application.yml", "src/main/resources/data/holidays-TX-01-2026.json", "src/test/java/com/acmehealth/priorauth/api/RequestAgeTest.java"]
lang = {"java": "java", "yml": "yaml", "json": "json"}
ST.append(step(9, "Build", "--build", "checks · review", "The checks node, and a second agent reviews",
               "A bash node re-runs the check and prints the log and diffstat; then a read-only review node judges the change against the requirements.", f"checks {nodechip('checks')} · review {nodechip('review')}",
               see(x(fold(S["approve-plan"]["stdout"].split("Loop node 'implement' completed after 1 iteration")[1].split("{\"verdict\"")[0]).strip()[:2600]), "real · the checks node's output (abridged)", "Archon returns")
               + tabs("code", [(Path(p).name, p, f"commit {FEAT} · real", lang[p.rsplit('.', 1)[1]], wsf(p)) for p in FEAT_FILES]
                      + [("the commit", f"git show {FEAT}", "real", "diff", PATCH[FEAT])])
               + note(f"The commit is the implement pass's own (<code>{FEAT}</code>, as the team CLAUDE.md asks). <code>review</code> declares <code>mutates_checkout: false</code>, so Archon would have failed it had it changed a file.")))

# ================= Review =================
ST.append(step(10, "Review", "--review", "review: NOT-READY", "The review says NOT-READY",
               "Every check was green. The reviewer still found a hole the tests couldn't see.", "review node · real",
               see(x(pause("approve-plan")), "real · the last wait's message", "Archon returns")
               + tabs("rev", [("review.md", "$ARTIFACTS_DIR/review.md", "real · review node", "md", art("review.md"))])
               + plain("R-1 is the kind of thing a person skims past: <code>?asOf=+999999999-12-31</code> parses as a date, and the day-by-day count would then run for hours on one request. The review node was a second Claude session with one job and the requirements in hand, and it tried the input.")))

ST.append(step(11, "Review", "--review", "wait: reject → cancel", "Reject the change; the run is cancelled",
               "Here reject goes to a cancel: node. The run ends, and the branch and worktree stay for the fix.", "Meena",
               io(cmdbox(f"archon workflow reject {RID} {REJ_CHANGE}", None, "any shell"),
                  see(x("\n".join(l for l in S["reject-change"]["stdout"].splitlines() if re.match(r"^(❌|⚠️|\s+(Usage|Cost|Input|Output))", l)) + "\n\n" + progress("reject-change") + "\n" + "\n".join(l for l in S["reject-change"]["stderr"].splitlines() if l.startswith(("Error:", "The rejection")))),
                      "real", "Archon returns"), stack=True)
               + gate("Wait 4 answered: reject", "<code>stop-change</code> ran (<code>cancel: The change was rejected at review.</code>); <code>push</code> was skipped.", "Meena Iyer")
               + note("<b>A misleading message.</b> The run was cancelled exactly as the YAML says, yet the CLI printed <code>Error: Rejected but failed to resume workflow …</code> and suggested <code>bun run cli workflow resume</code> (a source-install command). Nothing failed; <code>archon workflow get</code> shows status <code>cancelled</code>. Don't resume it.")))

ST.append(step(12, "Review", "--review", "bundled workflow", "Fix it with archon-implement, on the same branch",
               "A bundled workflow adopts the cancelled run's worktree and branch, reads its artifacts, and applies the decision.", f"Kiran · {nodechip('implement', FIX_ID)} on claude/opus",
               io(cmdbox(f"archon workflow run archon-implement --adopt {RID} {FIX_MSG}", None, "any shell"),
                  see(x(S["fix-run"]["stdout"].split("Workflow finished.")[0].split("🚀 **Starting workflow**: `archon-implement`")[0].strip() + "\n…\n" + json.dumps(json.loads(re.search(r'(\{"done".*?\})\n', S["fix-run"]["stdout"]).group(1)), indent=1) + "\n\nWorkflow finished.\n  Status: completed\n  Authored outcome: succeeded"), f"real · {S['fix-run']['seconds']:.0f}s", "Archon returns"), stack=True)
               + tabs("fix", [("the fix commit", f"git show {FIX}", "real", "diff", PATCH[FIX])])
               + note("<code>archon-implement</code> asks for the <code>large</code> tier; with no tiers set, Archon used the built-in default, <code>claude/opus</code>, and said so once. Its loop ends on a structured field (<code>until_field: done</code>), and <code>green</code> reports whether the checks passed. One pass, 24 tests.")))

# ================= Ship =================
ST.append(step(13, "Ship", "--ship", "ours", "Check the packaged jar by hand",
               "The review's R-3: do the holiday files load from inside the jar? Two curls answer it.", "Kiran · 1 min",
               io(you(x("cd $HOME\\.archon\\workspaces\\_local\\priorauth-api\\worktrees\\request-age\\age-api\nmvn -q package -DskipTests\njava -jar target\\priorauth-api-1.0.2.jar\n# in a second terminal:\ncurl \"http://localhost:8080/requests/pending?asOf=2026-10-13\"\ncurl -i \"http://localhost:8080/requests/pending?asOf=%2B999999999-12-31\""),
                      x("cd ~/.archon/workspaces/_local/priorauth-api/worktrees/request-age/age-api\nmvn -q package -DskipTests\njava -jar target/priorauth-api-1.0.2.jar\n# in a second terminal:\ncurl \"http://localhost:8080/requests/pending?asOf=2026-10-13\"\ncurl -i \"http://localhost:8080/requests/pending?asOf=%2B999999999-12-31\""), "PowerShell", "Terminal"),
                  see(x(S["curl"]["stdout"].strip()), "real", "curl returns"), stack=True)
               + note('The numbers match the AI-DLC run\'s answer key (v1.1.0): 7 and over, 4, 1, with the 12 Oct holiday counted. The field names differ (<code>ageLabel</code> is Meena\'s, from step 6). Compare: <a href="../../ai-dlc-execution/aidlc-hello-world-java/aidlc-hello-world-java-run.html">the AI-DLC run</a>.')))

ST.append(step(14, "Ship", "--ship", "ours", "Push the branch and open the PR",
               "The workflow's push node never ran (the change was rejected there), so Kiran pushes; the PR is opened in GitHub.", "Kiran",
               io(cmdbox("git -C $HOME\\.archon\\workspaces\\_local\\priorauth-api\\worktrees\\request-age\\age-api push -u origin request-age/age-api",
                         "git -C ~/.archon/workspaces/_local/priorauth-api/worktrees/request-age/age-api push -u origin request-age/age-api"),
                  see(x((S["push-by-hand"]["stdout"] + S["push-by-hand"]["stderr"]).strip()), "real · origin was a local copy of the repo", "git returns"))
               + see(x(BRANCH_LOG.strip()), "real · git log main..request-age/age-api", "The branch")
               + note(f"Opening the PR is documented, not run (no <code>gh</code> login): <code>gh pr create --base main --head request-age/age-api</code>. The branch holds {NFILES} files changed, +{PLUS} −{MINUS}. To let Archon open it, use the bundled <code>archon-pr</code> with <code>gh</code> signed in.")))

# ================= After =================
ST.append(step(15, "After", "--setup", "tidy up", "After the merge: archon complete",
               "Removes the worktree and the local branch, but only once the work is safe.", "Meena merges · Kiran tidies",
               io(cmdbox("archon complete request-age/age-api", None, "any shell"),
                  see(x(S["complete"]["stdout"].strip() + "\n" + "\n".join(l for l in S["complete"]["stderr"].splitlines() if l.strip().startswith(("Blocked", "✗", "Use --force", "Error")))), "real · before the merge", "Archon returns"))
               + io(see(x(S["merge"]["stdout"].strip()), "real · the PR merge, done by hand with git merge --no-ff", "git returns"),
                    see(x(S["complete-after-merge"]["stdout"].strip() + "\n" + "\n".join(l for l in S["complete-after-merge"]["stderr"].splitlines() if "Remote branch retained" in l) + "\n\n$ archon isolation list\n" + S["isolation-final"]["stdout"].strip()), "real · after the merge", "Archon returns"))
               + see(x("\n".join(S["verify-main"]["stdout"].strip().splitlines()[-4:])), f"real · ./scripts/verify.sh on main: {tests} tests", "Surefire reports")
               + note("Before the merge, <code>archon complete</code> refused: 2 commits not on <code>main</code>. It also tried <code>gh pr list</code> to look for an open PR and, with no <code>gh</code> login, skipped that check and said so. After the merge it removed the worktree and the local branch, and kept the remote branch on purpose.")))

node_rows = []
for n in ROWS:
    node_rows.append([f"<code>{n['node']}</code>", KIND.get(n["node"], "loop pass" if "iteration" in n["node"] else ""), fmt_ms(n["ms"]),
                      f"{n['input']:,}" if n["input"] else "—", f"{n['output']:,}" if n["output"] else "—", f"${n['cost']:.2f}" if n["cost"] else "—"])
ST.append(step(16, "After", "--setup", "the record", "What the run left behind",
               "No record in the repo: the run's files, transcript and costs are in ~/.archon. Here is where to find each.", "Kiran · reference",
               io(cmdbox(f"archon workflow runs\narchon workflow get {RID}\narchon workflow artifacts {RID}\narchon workflow logs {RID} --format text", None, "any shell"),
                  see(x(S["runs"]["stdout"].strip() + "\n\n" + S["get"]["stdout"].strip()), "real · during step 13", "Archon returns"))
               + table(["Node", "Kind", "Time", "Input tokens", "Output tokens", "Cost"], node_rows)
               + note(f"From the run's transcript (<code>logs/{SHORT}….jsonl</code>, {NODES[MAIN_ID]['events']} events). Waits count the time a person took. Costs are what the provider reported: <b>${COST_MAIN:.2f}</b> for request-to-pr and ${COST_FIX:.2f} for the fix, as API-price equivalents; the run used a claude.ai plan, so nothing was billed per token. Archon labels them \"may be partial\".")
               + see(x("\n".join(S["logs-text"]["stdout"].splitlines()[:30]) + "\n…"), "real · the transcript as text (first lines)", "Archon returns")))

plan_art = art("plan.md", PLAN_ID)
ST.append(step(17, "After", "--setup", "bundled workflow", "The same request through archon-plan",
               "For comparison: the bundled planner, read-only, on the repo after the run. It stopped and asked, as one attention item.", f"Kiran · {S['archon-plan']['seconds']:.0f}s",
               io(cmdbox('archon workflow run archon-plan --no-worktree "Plan the request in docs-in/request.md"', None, "any shell"),
                  see(x(pause("archon-plan")), "real", "Archon returns"), stack=True)
               + io(cmdbox(f"archon workflow respond {PLAN_ID} finish {S['plan-finish']['cmd'].split(' finish ', 1)[1]}", None, "any shell"),
                    see(x(progress("plan-finish")), "real", "Archon returns"))
               + tabs("aplan", [("plan.md", "$ARTIFACTS_DIR/plan.md", "real · archon-plan", "md", plan_art)])
               + three([("It found", "the request depends on a rule and a holiday list that are not in the repo"), ("It noticed", "the existing <code>request-age/age-api</code> branch, and that it ships things nobody asked for"),
                        ("It asked", "one select-form wait: <code>rerun</code> with answers, or <code>finish</code>")])
               + note("The bundled pack is opinionated: questions only a person can answer stop the run as one attention item (what, why, a recommendation, the choices, what happens if nobody answers). The team's own workflow put the same kind of questions in its first wait.")))

ST.append(step(18, "After", "--setup", "compare", "Same request: AI-DLC and Archon",
               "One change, two tools. What each made you do, and what each left behind.", "read · 3 min",
               table(["", "AI-DLC 2.11 (express)", "Archon 0.13.2 (request-to-pr)"], [
                   ["Where you type", "<code>/aidlc …</code> inside Claude Code", "<code>archon workflow …</code> in a terminal (or the Web UI)"],
                   ["The process", "the engine's 33 stages, 10 used by express", "the team's 15-node YAML, written for this"],
                   ["Stops for people", "4 gates + the plan stop", "4 waits (answers, requirements ×2, plan, change)"],
                   ["Request Changes", "option 2 at a gate", "reject inside a loop_group"],
                   ["The check", "<code>scripts/verify.sh</code>, recorded at Code Generation", "<code>until_bash: ./scripts/verify.sh</code> on the loop"],
                   ["A second reader", "the quality persona re-ran the tests", "the review node: NOT-READY, a real bug (R-1)"],
                   ["Where the work happens", "on a branch in the repo you cloned", "a separate worktree; your checkout untouched"],
                   ["The record", "<code>aidlc/</code>, committed with the workspace", "artifacts + transcript in <code>~/.archon</code>, not committed"],
                   ["Result", "12 files, 9 tests (answer key v1.1.0)", f"{NFILES} files, {tests} tests, the same three numbers"]])
               + plain("AI-DLC gives you a method with its stages and record already decided. Archon gives you an engine and asks you to write the method down. The same team rules (CLAUDE.md, one verify script, people approve) worked in both.")))

STEPS = [(1, "Clone and add team files"), (2, "Read request and workflow"), (3, "Dry-run it"), (4, "Start: scan and questions"), (5, "Answer the questions"),
         (6, "Reject the requirements"), (7, "Approve; the plan"), (8, "Approve the plan; implement"), (9, "Checks and review"), (10, "NOT-READY"),
         (11, "Reject; cancelled"), (12, "Fix with archon-implement"), (13, "Check the jar by hand"), (14, "Push, open the PR"),
         (15, "archon complete"), (16, "What the run left"), (17, "archon-plan, for comparison"), (18, "AI-DLC vs Archon")]
PH = {n: ("Set up", "--setup") for n in (1, 2, 3)} | {n: ("Plan", "--plan") for n in (4, 5, 6, 7)} | {n: ("Build", "--build") for n in (8, 9)} | \
     {n: ("Review", "--review") for n in (10, 11, 12)} | {n: ("Ship", "--ship") for n in (13, 14)} | {n: ("After", "--setup") for n in (15, 16, 17, 18)}
assert len(ST) == len(STEPS)

wall = (NODES[MAIN_ID]["end"], NODES[MAIN_ID]["start"])
hero = f'''<section class="hero" id="top">
  <div>
    <h1>One request through Archon, every step, for real.</h1>
    <p class="lead">Ravi asks for the request age on the API's pending list. Kiran runs the team's Archon workflow on the Spring Boot repo: Archon scans, asks, writes requirements that Meena sends back once, plans, implements until the tests pass, and has a second agent review, which finds a real bug. Every command, every reply and every file below is from that run (Archon 0.13.2, Claude Code, 3 Nov 2026).</p>
    <div class="facts">
      <div><b>18</b>steps, Windows and macOS</div>
      <div><b>15</b>nodes, 4 of them waits</div>
      <div><b>5</b>answers by people</div>
      <div><b>3</b>runs: the workflow, a fix, a comparison</div>
      <div><b>{tests}</b>tests on main after the merge</div>
      <div><b>1</b>bug the tests didn't catch, found by review</div>
    </div>
    <div class="legend">
      <div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--you)"><rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M8 14h8"/></svg><div><b>You type</b>In a terminal. Switch Windows/macOS at the top.</div></div>
      <div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:var(--ink-2)"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg><div><b>Archon returns</b>Real output, paths mapped to <code>C:\\Users\\you</code>.</div></div>
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
glossary = card("glossary", "Ten words", '<dl class="gloss">' + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in [
    ("workflow", "the YAML file with the team's process (<code>request-to-pr</code>)"), ("node", "one step of it: an agent prompt, a bash command, a loop or a wait"),
    ("run", "one execution, with a run id"), ("wait", "a node that pauses the run until someone answers"), ("form", "what a wait accepts: message, approval, select"),
    ("attention queue", "every run that is waiting for someone"), ("loop_group", "a few nodes repeated until a check passes; here, until the requirements are approved"),
    ("until_bash", "the shell check that ends a loop on exit 0"), ("worktree", "the run's own checkout, on its own branch, under ~/.archon"),
    ("artifacts", "the files a run writes for people and later nodes: scan.md, requirements.md, plan.md…")]) + "</dl>")
yourself = card("yourself", "Run it yourself", f"""<ol>
<li>Install Archon and the Claude provider, and check with <code>archon doctor</code> (<a href="../archon-workspace-setup.html">setup page</a>, steps 1–4).</li>
<li>Clone the starter with <code>--no-tags</code> and write the team's files (setup page, steps 5–8), or copy them from <code>archon-hello-world-java/java-workspace/</code> in the course files, which is the repo at the end of this run.</li>
<li>Start the run as in step 4 and answer each wait. Your questions and wording will differ: the agent is not deterministic. Use the answers from steps 5–8 so the requirements land where the course's did.</li>
<li>Compare with <code>java-workspace/</code>: the code, the tests ({tests}), and the curl numbers in step 13.</li></ol>
{note("Your run ids, times, costs and commit hashes will differ. The course's transcripts are in <code>java-run/logs/</code> and its artifacts in <code>java-run/artifacts/</code>.")}""")
real = card("real", "What is real here", f"""<p>Everything in the Archon and git boxes is real output from the course's run on Windows (3 Nov 2026, Archon 0.13.2, Claude Code on a claude.ai plan), captured by <code>tools/archon_step.py</code> and copied by <code>tools/capture_java_run.py</code>. Local paths are mapped to <code>C:\\Users\\you</code> and <code>C:\\work</code>; long Spring Boot test logs are folded. The macOS commands are the documented equivalents and were not run.</p>
<p>Not run: opening the PR (no <code>gh</code> login; the run pushed to a local copy of the repo standing in for GitHub), and the merge, which was a plain <code>git merge --no-ff</code> standing in for the PR merge. The people are fictional; their answers were typed by the course author.</p>""")

main = (hero + phase("--setup", "Set up", "steps 1–3 · the repo, the request, a free dry run") + "".join(ST[0:3])
        + phase("--plan", "Plan", "steps 4–7 · scan, questions, requirements, plan") + "".join(ST[3:7])
        + phase("--build", "Build", "steps 8–9 · implement until the check passes, then review") + "".join(ST[7:9])
        + phase("--review", "Review", "steps 10–12 · a NOT-READY, a cancel, a fix") + "".join(ST[9:12])
        + phase("--ship", "Ship", "steps 13–14 · check by hand, push, PR") + "".join(ST[12:14])
        + phase("--setup", "After", "steps 15–18 · tidy up, the record, a comparison") + "".join(ST[14:18])
        + yourself + glossary + real)
footer = ('<footer class="foot">Archon, Java edition · Archon 0.13.2 · <a href="../archon-introduction.html">introduction</a> · <a href="../archon-concepts-explained.html">concepts</a> · '
          '<a href="../archon-workspace-setup.html">setup</a> · <a href="../index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Archon, Java Edition: Every Step", "One small requirement taken through an Archon workflow on a Spring Boot repo, step by step: what you type, what Archon and Claude return, every wait and who answered it, and what lands on disk. Real run, real code, real output.",
             "Archon, Java edition", "one request · every step · real run", len(STEPS),
             rail(STEPS, PH, [("yourself", "Run it yourself"), ("glossary", "Ten words"), ("real", "What is real here")]), main, footer)
write(DEST / "archon-hello-world-java-run.html", html_)
