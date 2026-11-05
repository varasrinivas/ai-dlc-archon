"""Build archon-introduction.html: what Archon is, where you type, which workflow for which work, what you type at each
pause, every `workflow run` flag, every command, the workspace, its repo and ~/.archon.

Built from real output: tools/data/cli/cli.json (capture_cli.py), the team workflow in tools/data/java/files/, and the
course run's steps (archon-hello-world-java/java-run/steps.json). Asserts tie the page's counts to that data.

Usage: py -3.12 tools/build_intro_page.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli_parse import help_sections, workflow_nodes  # noqa: E402
from diagrams import node_cycle, workflow_dag  # noqa: E402
from pagekit import (ARCHON_WORDS, DOC, E, REAL, ROOT, card, disk, gloss, io, multirepo_facts, note, page, phase, plain, rail, see, step, table, tabs,  # noqa: E402
                     write, you)

DATA = ROOT / "tools" / "data"
CLI = json.loads((DATA / "cli" / "cli.json").read_text(encoding="utf-8"))
FILES = DATA / "java" / "files"
WF_PATH = ".archon/workflows/team/request-to-pr/request-to-pr.yaml"
WF = (FILES / WF_PATH).read_text(encoding="utf-8")
NODES = workflow_nodes(WF)
RUN = json.loads((ROOT / "archon-hello-world-java" / "java-run" / "steps.json").read_text(encoding="utf-8"))
STEP = {s["label"]: s for s in RUN}

VERSION = re.search(r"Archon CLI v([\d.]+)", CLI["version"]["out"]).group(1)
HELP = help_sections(CLI["help"]["out"])
COMMANDS, OPTIONS = HELP["commands"], HELP["options"]
WORKFLOWS = json.loads(CLI["workflow-list-json"]["out"])["workflows"]
BUNDLED = [w for w in WORKFLOWS if w["name"].startswith("archon-")]
assert VERSION == "0.13.2", VERSION
assert len(BUNDLED) == 25, len(BUNDLED)
assert len(COMMANDS) >= 60, len(COMMANDS)
RUN_HELP = help_sections(CLI["help-workflow-run"]["out"])
RUN_OPTS = RUN_HELP["options"]
assert any(o[0].startswith("--branch") for o in RUN_OPTS) and any(o[0] == "--detach" for o in OPTIONS)


def x(s):
    return E(s)


def full_desc(name):
    """The `Use when` / `NOT for` lines of a bundled workflow's full description (real `workflow list <name> --full`)."""
    txt = CLI["full"][name]
    body = txt.split(name, 2)[-1] if txt.count(name) >= 2 else txt
    body = re.sub(r"\s+", " ", body).strip()
    use = re.search(r"Use when:(.*?)(NOT for:|$)", body)
    nf = re.search(r"NOT for:(.*)$", body)
    return (use.group(1).strip() if use else ""), (nf.group(1).strip() if nf else "")


# ---------------- the course run, in numbers the "start here" steps state ----------------
NODES_JSON = json.loads((ROOT / "archon-hello-world-java" / "java-run" / "nodes.json").read_text(encoding="utf-8"))
RID = next(k for k, v in NODES_JSON.items() if v["workflow"] == "request-to-pr")
FIX_ID = next(k for k, v in NODES_JSON.items() if v["workflow"] == "archon-implement")
_DONE = [n for n in NODES_JSON[RID]["nodes"] if n["event"] == "node_complete"]
_FIXDONE = [n for n in NODES_JSON[FIX_ID]["nodes"] if n["event"] == "node_complete"]
COST_MAIN, COST_FIX = sum(n["cost"] or 0 for n in _DONE), sum(n["cost"] or 0 for n in _FIXDONE)
assert abs(COST_MAIN - float(re.search(r"Cost: \$([\d.]+)", STEP["get"]["stdout"]).group(1))) < 0.01
assert f"{COST_MAIN:.2f}" == "3.73" and f"{COST_FIX:.2f}" == "0.63", (COST_MAIN, COST_FIX)
AGENT_MIN = round((sum(n["ms"] or 0 for n in _DONE) + sum(n["ms"] or 0 for n in _FIXDONE)) / 60000)
_W = {i: json.loads(STEP[f"wait-{i}"]["stdout"])["attention"] for i in (1, 4, 5)}
N_QUESTIONS = len(re.findall(r"^\d\. \*\*", _W[1]["message"], re.M))
assert _W[1]["nodeId"] == "answer" and N_QUESTIONS == 7
assert sum(1 for n in _DONE if n["node"] == "write-requirements") == 2  # rejected once, approved the second
assert _W[4]["nodeId"] == "approve-plan" and _W[5]["message"].startswith("Review verdict: READY")
assert "Loop node 'implement' completed after 1 iteration" in STEP["approve-plan"]["stdout"]
assert "HTTP/1.1 500" in STEP["jar-check"]["stdout"] and "Workflow cancelled" in STEP["reject-change"]["stdout"]
assert sum(int(m) for m in re.findall(r"Tests run: (\d+), Failures: 0", STEP["verify-fix"]["stdout"])) == 21
_J2 = STEP["jar-check-2"]["stdout"]
assert _J2.count("HTTP/1.1 400") == 2 and "HTTP/1.1 500" not in _J2
assert "verify on main: passed" in STEP["verify-main"]["stdout"]
N_WAITS = sum(1 for n in NODES if n["kind"] == "wait")
RUNP = "archon-hello-world-java/archon-hello-world-java-run.html"

# ---------------- steps ----------------
S = []

S.append(step(1, "Start here", "--setup", "why", "The problem Archon solves",
              "If you have never used an AI coding agent with a process around it: what goes wrong without one.", "read · 2 min", f"""
<p>An <b>AI coding agent</b> (Claude Code, Codex and the like) is a program you give a task in plain English; it reads your code, edits files and runs commands until it thinks the task is done. It is fast and often right. Left alone, though, it decides for itself what to do first, what to ask, and when it's finished. On a team, that's the part that goes wrong:</p>
{table(["", "An agent on its own", "The same agent, run by Archon"], [
    ["Order of work", "whatever the agent picks this time", "the order the team wrote down: read the code, ask, write requirements, plan, build, review"],
    ["Questions", "it guesses an answer and carries on", "a step that writes the questions down and <b>stops</b> until a person answers"],
    ["Sign-off", "nobody, unless someone happens to look", "named people approve the requirements, the plan and the change before it is pushed"],
    ["“Done”", "the agent says so", "a check you chose passes (here: the project's tests, through <code>scripts/verify.sh</code>)"],
    ["Afterwards", "a chat history, if you kept it", "a transcript, every file each step wrote, and the cost, per run"],
    ["Next time", "a different path again", "the same steps, because they are in a file in the team's repo"]], "kv")}
{plain("Archon doesn't write code. It's the checklist and the traffic lights around the agent that does: it tells the agent which step is next, and turns red where a person has to look.")}
{note("When it isn't worth it: a one-off, two-line edit you'd review in ten seconds anyway, or if you don't use a coding agent yet. Archon pays off when the same kind of work comes round again and more than one person has a say in it.")}
"""))

BASICS = [("repo (repository)", "a project's folder of code, tracked by <b>git</b>, which remembers every saved change"),
          ("commit", "one saved change in a repo, with a message saying what and why"),
          ("branch", "a separate line of commits, so work in progress doesn't touch the main version (<code>main</code>) until it's ready"),
          ("pull request (PR)", "a request to merge a branch into <code>main</code>, where teammates review it first"),
          ("merge", "folding a branch's commits into <code>main</code>: the change is now part of the product"),
          ("coding agent", "an AI program that works on code by itself: reads, edits, runs commands"),
          ("Claude Code", "Anthropic's coding agent, the one this course uses; Archon starts it for you"),
          ("terminal", "the window where you type commands (PowerShell on Windows, Terminal on macOS)"),
          ("YAML", "a plain-text file format of <code>name: value</code> lines and indented lists; easy to read and to diff"),
          ("test", "a small program that checks the code does what it should; <i>the tests pass</i> means all of them did")]
S.append(step(2, "Start here", "--setup", "words", "Ten everyday words this page uses",
              "Not Archon's words (those are at the end of the page): the developer basics the rest assumes.", "read · 2 min",
              gloss(BASICS) + note('Archon\'s own words (workflow, node, wait, worktree, folder project …) are in <a href="#words">Archon words</a> at the end of the page.')))

STORY = [
    ("The request", "Ravi, a nurse manager, asks in Slack for the list of pending requests to show how many business days each has been waiting, and flag those over 5. Kiran, a developer, saves it as <code>docs-in/request.md</code> and starts the team's workflow with one command."),
    ("Read, then ask", f"The agent reads the code and writes down <b>{N_QUESTIONS} questions</b> only people can answer (where do the holidays come from? which date is 201ctoday201d? what are the field names?). The run stops. Kiran types the team's answers."),
    ("Requirements, rejected once", "The agent writes the requirements. Meena, the tech lead, <b>rejects</b> the first draft: the screen team already chose other field names. The agent revises; she approves the second."),
    ("Plan", "The agent writes a plan: which files, which tests, which branch. Meena approves it."),
    ("Build until the tests pass", "The agent writes the code and runs the tests; it would loop until they pass. They passed on the <b>first</b> try."),
    ("Review", "A second agent, which can read but not change anything, reviews the change: <b>READY</b>."),
    ("A person catches what the agents missed", "Before approving, Kiran tries the built program by hand. One silly date (the year 999,999,999) makes it <b>crash with a 500 error</b>. Meena rejects the change, which ends the run."),
    ("Fix", f"Kiran starts a small follow-up workflow on the same branch. The agent makes the bad date a clean error (400) instead, and all <b>21 tests</b> pass. Kiran re-checks by hand and pushes."),
    ("Merge", "Meena merges the branch; the tests pass on <code>main</code>. Ravi's screen can show the age."),
]
S.append(step(3, "Start here", "--setup", "the story", "One request, start to finish",
              "What the course actually did with Archon, in plain words. Every line is from the real run.", "read · 3 min",
              '<ol style="margin:0 0 14px;padding-left:22px;line-height:1.6">' + "".join(f"<li><b>{h}.</b> {b}</li>" for h, b in STORY) + "</ol>"
              + table(["", "In the course's run"], [
                  ["People's decisions", f"{N_WAITS} pauses in the workflow; 5 answers typed, two of them rejections"],
                  ["Agent time", f"about {AGENT_MIN} minutes across both runs"],
                  ["Reported cost", f"${COST_MAIN:.2f} for the workflow + ${COST_FIX:.2f} for the fix (what the API would have charged; the course used a claude.ai plan, so nothing was billed per use)"],
                  ["What the person added", "the one bug the tests and the review didn't catch"]], "kv")
              + plain("The workflow didn't make the agent smarter. It made sure people looked at the right moments, and one of those looks found a crash before it was shipped.")
              + note(f'Every command, answer and output of this run, step by step: <a href="{RUNP}">the hands-on run</a>.')))

S.append(step(4, "Meet Archon", "--setup", "the idea", "What Archon is, in four sentences",
              "Now the same thing in Archon's terms, so the rest of the page has somewhere to land.", "read · 2 min", f"""
<p><b>In one sentence:</b> you describe, in a file, how your team does a kind of job; Archon makes the AI agent do it in that order and stops wherever a person has to decide.</p>
<p>Archon is an open-source <b>workflow engine for AI coding</b>. The file is a <b>YAML workflow</b>, and Archon runs it the same way every time. A workflow is a graph of <b>nodes</b> (steps): an AI node hands a prompt to the agent you already use (Claude Code, Codex or Pi), a code node runs a command, and a <b>wait</b> node stops until a person answers.</p>
<p>A run works either in place in a <b>workspace</b> that holds your repos (a <i>folder project</i>, what this course uses) or in its own <b>git worktree and branch</b> (a <i>repo project</i>), and keeps a transcript, the files each node wrote and what it cost. Archon {VERSION} (29 Oct 2026) ships {len(BUNDLED)} workflows of its own, the <code>sdlc</code> pack, and you add yours in a <code>.archon/</code> folder.</p>
<p>The kinds of node, and which of them cost money (an AI model bills by the <b>token</b>, roughly ¾ of a word read or written; a command or a pause costs nothing):</p>
{table(["Node body", "What it does", "Costs model tokens?"], [
    ["<code>prompt:</code> / <code>command:</code>", "Sends an inline prompt, or a Markdown command file, to the agent", "yes"],
    ["<code>loop:</code> / <code>loop_group:</code>", "Repeats an agent step (or a small graph) until a check passes", "yes"],
    ["<code>bash:</code> / <code>script:</code>", "Runs a shell script, or TypeScript (bun) / Python (uv)", "no"],
    ["<code>wait:</code>", "Pauses for a time, an event, or a person's answer", "no"],
    ["<code>cancel:</code>", "Ends the run with a reason", "no"],
    ["<code>include:</code> / <code>workflow:</code>", "Reuses another workflow, inlined or as a child run", "depends"]])}
{plain("A coding agent on its own is a talented cook who improvises. Archon is the recipe card on the wall: the cook still cooks, but in the order the card says, and the chef tastes before anything leaves the kitchen.")}
<p style="font-size:.92rem;color:var(--ink-3)">Not the old Archon: until 2025 the name meant a knowledge-base and task MCP server (kept on the repo's <code>archive/v1-task-management-rag</code> branch). Everything here is the workflow engine.</p>
"""))

S.append(step(5, "Meet Archon", "--setup", "the idea", "How one node runs",
              "Every workflow is built from this one move: a node gets inputs, does one job, and hands its output on.", "read · 2 min",
              node_cycle() + note("The agent in an AI node is a full Claude Code session in the run's folder (the workspace in this course, or a run's worktree): it reads files, runs commands and edits code, and it reads the <code>CLAUDE.md</code> there. What it may do is set by the node (<code>allowed_tools</code>, <code>denied_tools</code>, <code>mutates_checkout: false</code>), not by Archon guessing.")))

NOTE = {"scan": "reads the repo, writes scan.md", "questions": "asks what only people can decide", "answer": "Kiran answers for Ravi and Meena",
        "plan": "files, tests, order → plan.md", "approve-plan": "Meena approves the plan", "checks": "verify + git log + diffstat",
        "review": "a second agent, read-only: READY / NOT-READY", "approve-change": "approve to push", "push": "git -C priorauth-api push"}
BOX = {"scan": "The agent reads the code and the request, changes nothing, and writes what it found to <code>scan.md</code>.",
       "questions": "The agent lists only what a person must decide, each with options and its own pick.",
       "answer": "<b>Pause.</b> A person answers the questions.",
       "requirements": "A small loop around the next two boxes: repeat until the requirements are approved.",
       "write-requirements": "The agent writes the requirements from the request and the answers (or revises them after a rejection).",
       "review-requirements": "<b>Pause.</b> The tech lead approves the requirements, or rejects them with what to change.",
       "plan": "The agent writes the plan: which files, which tests, which branch.",
       "approve-plan": "<b>Pause.</b> The tech lead approves the plan.",
       "stop-plan": "Only if the plan is rejected: the run ends here.",
       "implement": "The agent writes the code and runs the tests; it repeats until they pass (or a limit is hit).",
       "checks": "A script, not the AI: runs the tests once more and lists what changed.",
       "review": "A second agent, allowed to read but not to edit, says READY or NOT-READY.",
       "approve-change": "<b>Pause.</b> A person approves the finished change (Kiran tries it by hand first).",
       "stop-change": "Only if the change is rejected: the run ends here.",
       "push": "A script pushes the branch to the shared remote, ready for a pull request."}
WHO = {"command": "agent", "prompt": "agent", "loop": "agent, repeated", "loop_group": "Archon (repeats)", "bash": "script", "wait": "person", "cancel": "Archon"}
assert set(BOX) == {n["id"] for n in NODES} and all(n["kind"] in WHO for n in NODES)
S.append(step(6, "Meet Archon", "--setup", "the idea", "A workflow is a graph you can read",
              "The course's workflow, drawn from its YAML file. Read it once now; the hands-on run walks through every box.", "read · 3 min",
              f"<p>This is <code>request-to-pr</code>, the team's workflow the course runs from its workspace on priorauth-api: {len(NODES)} nodes, {sum(1 for n in NODES if n['kind'] == 'wait')} of them are waits for a person. Arrows are <code>depends_on</code>; the labels on them are <code>when:</code> conditions; the dashed loop is the requirements being revised until approved.</p>"
              + workflow_dag(NODES, "request-to-pr: the team's workflow, drawn from its YAML", NOTE)
              + '<h3 style="margin:22px 0 8px">Box by box, in plain words</h3>'
              + table(["Box", "What happens", "Who"], [[f"<code>{n['id']}</code>", BOX[n["id"]], WHO[n["kind"]]] for n in NODES])
              + tabs("wf", [("request-to-pr.yaml", WF_PATH, "the team's workflow · real file", "yaml", WF)])))

S.append(step(7, "Meet Archon", "--setup", "the people", "The people in this course",
              "The same fictional team as the AI-DLC course, so the two runs compare one to one.", "read · 1 min", table(
                  ["Person", "Role", "In the run"], [
                      ["Ravi Menon", "Nurse manager (the business)", "Sent the request in Slack; his answers are in the first wait"],
                      ["Kiran Rao", "Developer", "Runs Archon in a terminal; answers the waits; opens the PR"],
                      ["Meena Iyer", "Tech lead", "Rejects the first requirements with the screen team's names; approves the plan and the change"]])
              + note("Archon doesn't know who anyone is on a CLI-only install: an answer records the surface and the time, and the text says who decided. The course writes the names into the answer text, as the team's CLAUDE.md asks.")))

S.append(step(8, "Set up", "--plan", "where you type", "Three places you type, and one you don't",
              "Archon runs the agent for you. You type into Archon, not into Claude Code.", "read · 2 min",
              table(["Where", "What you do there", "In this course"], [
                  ["Terminal: <code>archon …</code>", "Start runs, see the attention queue, answer waits, read artifacts and logs", f"every step {REAL}"],
                  ["Web UI: <code>archon serve</code> → <code>http://localhost:3090</code>", "The same runs, with the graph, the events, and approve/reject buttons", f"setup page step 7 {DOC}"],
                  ["Chat: Slack, Telegram, Discord (plugins); <code>archon chat</code>", "Ask the orchestrator to pick and start a workflow; answer waits in the thread", DOC],
                  ["Claude Code itself", "Nothing during a run. Archon starts its own Claude Code sessions with your login", "—"]])
              + plain("Archon is the dispatcher with the job sheets; Claude Code is the technician it sends out. You talk to the dispatcher.")))

S.append(step(9, "Set up", "--plan", "once per machine", "Set up once",
              "Install the binary, connect the agent, check. The setup page shows each command's real output.", "about 5 minutes",
              io(you("irm https://archon.diy/install.ps1 | iex\narchon provider add claude\narchon doctor",
                     "curl -fsSL https://archon.diy/install | bash\narchon provider add claude\narchon doctor", "PowerShell", "Terminal"),
                 see(x(CLI["doctor"]["out"].strip()), f"archon doctor · {VERSION} · real", "Archon returns"))
              + note('The installer verifies the binary\'s checksum, puts it in <code>~/.archon/bin</code> and adds that folder to your user PATH (open a new terminal). It asks which providers to add; <code>archon provider add claude</code> does the same later. Claude Code must already be installed and signed in. Full walk-through: <a href="archon-workspace-setup.html">set up Archon for a repo</a>.')
              + plain('<b>New to this? Read on through step 10 (the workspace), then go to <a href="archon-workspace-setup.html">the setup page</a>.</b> Steps 11–16 are reference: come back to them when you write your own workflow or meet a command you do not know.')))

WS_TREE = """java-workspace/                      <b>the team's workspace</b>: a git repo of its own, wherever you keep it
                                     the course's: C:\\work\\archon-java\\java-workspace
                                     an Archon <b>folder project</b>: runs start here, with --folder the first time
├── <span class="n">.archon/</span>                         committed: the team's Archon files
│   ├── <span class="n">config.yaml</span>                  assistant: claude (no worktree settings: none apply)
│   └── workflows/
│       └── team/                    <span class="m">a pack (any name)</span>
│           └── request-to-pr/       <span class="m">one workflow per folder</span>
│               ├── <span class="n">request-to-pr.yaml</span>
│               └── commands/
│                   ├── <span class="n">scan.md</span>          <span class="m">the prompt of the scan node</span>
│                   └── <span class="n">implement.md</span>     <span class="m">the prompt of each implement pass</span>
├── <span class="n">CLAUDE.md</span>                        the repo map and the team's rules; read in every AI node
├── <span class="n">scripts/verify.sh</span>, verify.cmd    the one check: cd priorauth-api, mvn -q test
├── <span class="n">docs-in/request.md</span>               Ravi's request, named in the run message
├── <span class="n">.gitignore</span>                       /priorauth-api/: the code repo is not part of this one
├── <span class="n">.gitattributes</span>                   keeps verify.sh LF
└── priorauth-api/                   <b>the code repo</b>: cloned inside, its own git and remote
    ├── <span class="n">pom.xml</span>                      Spring Boot 4.1, Java 21, Maven
    └── <span class="n">src/</span>                         <b>the API code</b>, as on main before the run
        ├── main/java/com/acmehealth/priorauth/
        │   ├── PriorAuthApiApplication.java
        │   ├── api/                 <span class="m">the endpoint the reviewer screen reads</span>
        │   │   ├── PendingRequestsController.java   GET /requests/pending
        │   │   └── PendingRequestResponse.java      one row of the list
        │   ├── model/PriorAuthRequest.java
        │   └── store/RequestStore.java  <span class="m">the nightly export, packed into the jar</span>
        ├── main/resources/          application.yml, data/requests.sample.json
        └── test/java/com/acmehealth/priorauth/
            ├── api/PendingRequestsControllerTest.java
            └── store/RequestStoreTest.java"""
RUN_TREE = """java-workspace/priorauth-api/         <b>where the run writes the API code</b>: Kiran's own clone,
                                      on the branch the agent made, request-age/pending-age
├── src/main/java/com/acmehealth/priorauth/
│   ├── aging/RequestAging.java       <span class="m">new</span>
│   ├── api/PendingRequestsController.java   <span class="m">changed</span>
│   ├── api/PendingRequestResponse.java      <span class="m">changed</span>
│   └── PriorAuthApiApplication.java  <span class="m">changed</span>
├── src/main/resources/application.yml       <span class="m">changed</span>
├── src/main/resources/data/holidays-TX-01-2026.json   <span class="m">new</span>
└── src/test/java/…                   <span class="m">new and changed tests</span>"""
HOME_TREE = """~/.archon/                           <b>yours, never committed</b> (C:\\Users\\you\\.archon on Windows)
├── bin/archon.exe                   the CLI
├── plugins/                         provider plugins (archon-provider-claude.exe)
├── config.yaml                      your defaults: assistant, tiers, concurrency
├── install.json                     which binary and version
├── archon.db                        SQLite: projects, runs, events, costs
└── workspaces/_folder/java-workspace/   one folder per project (no worktrees/ for a folder project)
    ├── logs/&lt;run-id&gt;.jsonl            the transcript
    ├── artifacts/runs/&lt;run-id&gt;/        scan.md, questions.md, requirements.md, plan.md …
    ├── state/
    └── workflow-source/runs/&lt;run-id&gt;/  the workflow as it was when the run started"""
# Every file the trees name is a real file of priorauth-api, and new/changed matches the run's diff.
_GIT = ROOT / "archon-hello-world-java" / "java-run" / "git"
_FILES = set((_GIT / "files.txt").read_text(encoding="utf-8").split())
_DIFF = (_GIT / "diff.patch").read_text(encoding="utf-8")
_NEW = set(re.findall(r"diff --git a/(\S+) b/\S+\nnew file mode", _DIFF))
_CHANGED = set(re.findall(r"diff --git a/(\S+) b/", _DIFF)) - _NEW
_J, _T = "src/main/java/com/acmehealth/priorauth/", "src/test/java/com/acmehealth/priorauth/"
for _f in ["pom.xml", _J + "PriorAuthApiApplication.java", _J + "api/PendingRequestsController.java", _J + "api/PendingRequestResponse.java",
           _J + "model/PriorAuthRequest.java", _J + "store/RequestStore.java", "src/main/resources/application.yml",
           "src/main/resources/data/requests.sample.json", _T + "api/PendingRequestsControllerTest.java", _T + "store/RequestStoreTest.java"]:
    assert _f in _FILES and _f not in _NEW, f"repo tree: {_f} is not a starter file"
assert {_J + "aging/RequestAging.java", "src/main/resources/data/holidays-TX-01-2026.json"} <= _NEW
assert {_J + "api/PendingRequestsController.java", _J + "api/PendingRequestResponse.java", _J + "PriorAuthApiApplication.java", "src/main/resources/application.yml"} <= _CHANGED
assert any(f.startswith(_T) for f in _NEW) and any(f.startswith(_T) for f in _CHANGED)
_WSDIR = ROOT / "archon-hello-world-java" / "java-workspace"
for _f in (".archon/config.yaml", WF_PATH, ".archon/workflows/team/request-to-pr/commands/scan.md", "CLAUDE.md", "scripts/verify.sh", "docs-in/request.md", ".gitignore", ".gitattributes", "priorauth-api/pom.xml"):
    assert (_WSDIR / _f).exists(), f"workspace tree: {_f}"
assert "/priorauth-api/" in (_WSDIR / ".gitignore").read_text(encoding="utf-8")
FOLDER_TREE = """priorauth-workspace/                 <b>the same shape, two repos</b>
├── <span class="n">.archon/workflows/…</span>              the team's workflows, read from the root
├── <span class="n">CLAUDE.md</span>                        the rules for work across both repos
├── <span class="n">docs-in/bug-report.md</span>            the bug, named in the run message
├── priorauth-aging/                 repo 1: the aging library, a git repo of its own
└── priorauth-api/                   repo 2: the API, depends on the library
                                     <span class="m">the agent branches and commits in each</span>"""
multirepo_facts(CLI)
_RUNSTEPS = {s["label"]: s for s in RUN}
assert 'Registered folder project "java-workspace"' in _RUNSTEPS["run"]["stdout"]
assert "No codebases registered." in _RUNSTEPS["isolation-list"]["stdout"]
assert "request-age/pending-age" in _RUNSTEPS["push-by-hand"]["stdout"]
S.append(step(10, "The workspace", "--build", "the files", "The workspace, its repo, and ~/.archon",
              "Like the AI-DLC course: a team workspace with the code repo cloned inside it. Two places: what the team commits (the workspace, and the code in its own repo), and what stays on your machine.", "read · 3 min",
              plain("Two folders matter. The team's <b>workspace</b> is shared through git: the process (<code>.archon/</code>), the rules for the agent (<code>CLAUDE.md</code>), the check (<code>scripts/verify.sh</code>), the requests, and the code repo cloned inside it. Your <b>~/.archon</b> folder is private to your machine: the Archon program, its database of runs, and each run's transcript and files.")
              + io(disk(WS_TREE, "The workspace, with the code repo inside (both committed, each in its own repo)"), disk(HOME_TREE, "In your home folder (not committed)"), stack=True)
              + disk(RUN_TREE, "During the run: the agent's branch in priorauth-api")
              + plain("Archon runs from the workspace root, in place. The agent reads <code>CLAUDE.md</code> there, makes the branch in <code>priorauth-api/</code> and commits the code there. The workspace repo only changes when the team's process does.")
              + table(["File", "Needed?", "Why"], [
                  ["<code>.archon/workflows/…/*.yaml</code>", "only for your own workflows", "The bundled 25 need nothing in the workspace"],
                  ["<code>.archon/config.yaml</code>", "optional", "Project defaults; wins over <code>~/.archon/config.yaml</code>. Worktree settings (<code>copyFiles</code>, <code>postCreate</code>) only matter in a repo project"],
                  ["<code>CLAUDE.md</code>", "optional, recommended", "Which repos are here, how to check them, the git rules: the agent's standing rules, in every AI node"],
                  ["<code>.gitignore</code>", "yes, in a workspace repo", "Leaves the cloned code repos out: each keeps its own history, branches and PRs"],
                  ["<code>.archon/.env</code>", "optional, never commit", "Credentials for this project (<code>archon setup --scope project</code>)"],
                  ["<code>.gitattributes</code>", "on Windows with autocrlf", "Without <code>*.sh text eol=lf</code> bash gets CRLF scripts"]], "kv")
              + f'<h3 style="margin:22px 0 8px">Two repos? The same workspace {REAL}</h3>'
              + plain("When one change spans two repos, clone both into the workspace. Nothing else changes: the same <code>.archon/</code> at the root, the same <code>--folder</code> run. The course's two-repo run has exactly this layout.")
              + disk(FOLDER_TREE, "The course's two-repo run: priorauth-workspace")
              + f'<h3 style="margin:22px 0 8px">Or: the repo is the project {DOC}</h3>'
              + table(["", "A workspace, a folder project (this course)", "The repo is the project"], [
                  ["Where <code>.archon/</code> lives", "the workspace root, next to the cloned repos", "inside the repo, committed with the code"],
                  ["Register", "the first run with <code>--folder</code> from the root; later runs need no flag", "the first run in the repo"],
                  ["The agent works in", "the root, in place: Kiran's own clones", "the run's own worktree under <code>~/.archon</code>, on a branch Archon makes"],
                  ["Branches and the PR", "the agent's job, in each repo (<code>--branch</code> is rejected)", "Archon makes the branch (<code>--branch</code>); the workflow pushes it"],
                  ["Isolation", "none, or <code>--container</code>: a Docker overlay, with an approval before writes reach the folders", "a worktree per run; <code>archon complete</code> removes it after the merge"],
                  ["Runs are stored in", "<code>~/.archon/workspaces/_folder/&lt;slug&gt;/</code>", "<code>~/.archon/workspaces/&lt;owner&gt;/&lt;repo&gt;/</code>, worktrees included"],
                  ["Fits", "a team that keeps its process outside the code, or a change across repos", "one repo, when you want each run in its own checkout"]], "kv")
              + note("Archon does not give one run a worktree in each of two repos. Workflows can also live outside every repo and workspace: <code>~/.archon/workflows/</code> appear in all your projects (yours, not the team's), and <code>--workflow-source &lt;dir&gt;</code> reads the workflow from one folder and runs it against <code>--cwd</code>. From the Archon " + VERSION + " docs and <code>workflow run --help</code>. Workflow commands need a git repository or a registered folder: outside one, <code>archon workflow list</code> says <code>" + x(CLI["outside-repo"]["out"].strip().splitlines()[0]) + "</code>.")))

FIELDS = [["<code>name</code>, <code>description</code>, <code>nodes</code>", "required. The description is what <code>workflow list</code> shows and what chat reads to pick a workflow: say when to use it and when not"],
          ["<code>provider</code>, <code>model</code>, <code>effort</code>", "defaults for every AI node (a node can override)"],
          ["<code>worktree.enabled</code>", "<code>false</code> = always in the live checkout; <code>true</code> = always a worktree; omit to let the caller choose"],
          ["<code>inputs</code>", "named inputs, passed with <code>--input name=value</code>, read as <code>$INPUTS.name</code>"],
          ["<code>budget</code>", "a ceiling on the run's total spend"],
          ["node: <code>id</code>, <code>depends_on</code>, <code>when</code>, <code>trigger_rule</code>", "the graph"],
          ["node: <code>output_format</code>", "JSON Schema the AI reply must match; fields readable as <code>$id.output.field</code>"],
          ["node: <code>mutates_checkout: false</code>", "the engine fails the node if it changed the checkout"],
          ["node: <code>allowed_tools</code>, <code>denied_tools</code>, <code>context: fresh</code>, <code>retry</code>, <code>idle_timeout</code>", "how the agent runs"],
          ["loop: <code>max_iterations</code> + <code>until_bash</code> / <code>until_field</code> / <code>until</code>", "when a loop is done (at least one; <code>until_bash</code> is the strongest)"],
          ["wait: <code>attention</code>, <code>form</code>, <code>options</code>", "the question and the answer it accepts"]]
S.append(step(11, "The workspace", "--build", "authoring", "The fields you will use",
              "A short list from the workflow-language reference: enough to read any workflow and write a first one.", "reference",
              table(["Field", "What it does"], FIELDS, "kv")
              + io(you("archon validate workflows request-to-pr\narchon workflow run request-to-pr --dry-run --default-stubs \"Implement the request in docs-in/request.md\"", None, "any shell"),
                   see(x(STEP["dry-run"]["stdout"].split("STUBBED   questions")[0].strip()[:900] + "\n…\nPAUSED    answer (wait) — durable wait\n…\nSimulation outcome: paused"), "real · dry run, no model call", "Archon returns"))
              + note("<code>--dry-run</code> walks the graph with stub outputs: it starts no run and calls no model, and stops at the first wait (add <code>--pause-at-gates</code> to stop at approval gates too). Check every new workflow this way before it costs anything.")))

cat_rows = []
for w in BUNDLED:
    use, nf = full_desc(w["name"])
    cat_rows.append([f"<code>{w['name']}</code>", x(w["description"]), x(use) or "—"])
S.append(step(12, "Doing the work", "--review", "which workflow", "Which workflow for which work",
              f"Archon {VERSION} ships {len(BUNDLED)} workflows. Most are building blocks of the sdlc factory; a handful are useful on their own.", "reference", f"""
{table(["If you want to…", "Run", "Changes the repo?"], [
    ["find the cause of a bug, or answer a question about the code", "<code>archon-investigate</code>", "no"],
    ["turn a decided request into a plan", "<code>archon-plan</code>", "no (pauses if it has questions)"],
    ["build decided work until checks pass", "<code>archon-implement</code>", "commits; opens no PR"],
    ["take an issue or request all the way to a reviewed PR", "<code>archon-ship</code>", "branch, PR (needs <code>gh</code>)"],
    ["review a PR or a diff", "<code>archon-review</code>", "no (one PR comment)"],
    ["run the project's own checks and get a verdict", "<code>archon-validate</code>", "no"],
    ["your team's own steps, gates and checks", "your workflow in <code>.archon/workflows/</code>", "as you wrote it"]])}
<p>The full catalog, with each workflow's own words (from <code>archon workflow list --json</code> and <code>workflow list &lt;name&gt; --full</code>, real):</p>
<div class="flist">{table(["Workflow", "Description", "Use when"], cat_rows)}</div>
{note("0.12.0 removed the older <code>archon-fix-github-issue</code>, <code>archon-idea-to-pr</code>, <code>archon-smart-pr-review</code> and <code>archon-assist</code>, and 0.13.1 made names exact (<code>review</code> no longer finds <code>archon-review</code>). Tutorials that use them are out of date.")}
"""))

approve_txt = STEP["approve-requirements"]["stdout"]
tail = "\n".join(l for l in approve_txt.splitlines() if l.startswith(("Approve:", "Reject:", "Abandon:", "Workflow paused")))
assert "archon workflow approve" in tail
S.append(step(13, "Doing the work", "--review", "at a pause", "What you type at each pause",
              "A wait node stops the run and puts it in the attention queue. The form it declares says what it accepts.", "reference",
              table(["Form", "You answer with", "The next node reads"], [
                  ["<code>message</code> (default)", "<code>archon workflow answer &lt;run&gt; --occurrence &lt;id&gt; --text \"…\"</code> (or <code>approve &lt;run&gt; \"…\"</code>)", "<code>$id.output.text</code>"],
                  ["<code>approval</code>", "<code>archon workflow approve &lt;run&gt; \"…\"</code> · <code>archon workflow reject &lt;run&gt; \"…\"</code>", "<code>$id.output.decision</code>, <code>.text</code>"],
                  ["<code>select</code>", "<code>archon workflow respond &lt;run&gt; &lt;option-id&gt; \"…\"</code>", "<code>$id.output.decision</code>, <code>.text</code>"],
                  ["<code>multi_select</code>", "<code>archon workflow answer &lt;run&gt; --occurrence &lt;id&gt; --choose a --choose b</code>", "<code>$id.output.decisions</code>, <code>.text</code>"]])
              + io(you("archon workflow attention\narchon workflow wait &lt;run-id&gt; --json", None, "find what is waiting"),
                   see(x(tail), "real · printed under every pause in the course run", "Archon returns"))
              + plain("A pause is the workflow asking a person a question. You see it in <code>archon workflow attention</code>, and you reply with one command: <code>approve</code>, <code>reject</code> or <code>answer</code>, followed by your text. The agent reads your text in the next step.")
              + plain("<b>Reject is an answer, not a stop.</b> The run carries on with decision <code>reject</code>; the workflow decides what that means. In <code>request-to-pr</code>, a rejected requirements draft is revised (the loop_group), a rejected plan or change goes to a <code>cancel:</code> node.")
              + note("Answering from the CLI continues the run in that terminal until the next pause or the end. Add <code>--json</code> to record the answer and return at once; <code>archon serve</code> or <code>archon workflow wake</code> then continues it.")))

S.append(step(14, "Doing the work", "--review", "starting a run", "Every <code>workflow run</code> flag",
              "From the real <code>archon workflow run --help</code>. The ones the course uses are first.", "reference",
              table(["Flag", "What it does"], [[f"<code>{x(f)}</code>", x(d)] for f, d in RUN_OPTS], "kv")
              + plain("You only need two flags at first: <code>--folder</code> on your first run in a workspace, and <code>--detach</code> to get your terminal back while it works. The rest is here for when you need it.")
              + note("The course starts its run from the workspace root with <code>archon workflow run request-to-pr --folder --detach \"Implement the request in docs-in/request.md\"</code>: <code>--folder</code> registers the workspace as a folder project the first time, and <code>--detach</code> runs it in the background (so the terminal is free while it works). In a repo project you would name the branch with <code>--branch</code> instead; a folder project rejects it.")))

S.append(step(15, "Doing the work", "--review", "after a run", "After a run, and between runs",
              "Where to look, and how to tidy up.", "reference", table(["Command", "What it shows or does"], [
                  ["<code>archon workflow runs</code> · <code>status</code>", "recent runs of this project; running and paused ones"],
                  ["<code>archon workflow get &lt;run-id&gt;</code>", "one run: status, worktree path, branch, cost, artifacts"],
                  ["<code>archon workflow logs &lt;run-id&gt; --format text</code>", "the transcript as progress lines (<code>--follow</code> to stream)"],
                  ["<code>archon workflow artifacts &lt;run-id&gt; [file]</code>", "the files the run wrote; print one"],
                  ["<code>archon workflow resume &lt;run-id&gt;</code>", "continue a failed or paused run; finished nodes are replayed, not re-run"],
                  ["<code>archon workflow cancel</code> · <code>abandon &lt;run-id&gt;</code>", "stop a run · mark it cancelled and remove its worktree (keeps the branch)"],
                  ["<code>archon isolation list</code>", "every worktree Archon made (a folder project has none: it says <i>No codebases registered.</i>)"],
                  ["<code>archon complete &lt;branch&gt;</code>", "remove a branch's worktree and local branch (the remote branch stays). In a folder project it finds nothing: delete your branch with git"],
                  ["<code>archon isolation cleanup [days]</code> · <code>--merged</code>", "remove old (default 7 days) or merged worktrees; keeps anything unpushed or uncommitted"]], "kv")))

S.append(step(16, "Reference", "--ship", "every command", "Every command",
              f"All {len(COMMANDS)} entries of the real <code>archon help</code> in {VERSION}, and its global options.", "reference",
              '<div class="flist">' + table(["Command", "What it does"], [[f"<code>{x(c)}</code>", x(d)] for c, d in COMMANDS], "kv") + "</div>"
              + '<p style="margin-top:14px"><b>Options</b> (they apply to the commands named in each line):</p><div class="flist">'
              + table(["Option", "What it does"], [[f"<code>{x(f)}</code>", x(d)] for f, d in OPTIONS], "kv") + "</div>"))

STEPS = [(1, "The problem it solves"), (2, "Ten everyday words"), (3, "One request, start to finish"),
         (4, "What Archon is"), (5, "How one node runs"), (6, "A workflow is a graph"), (7, "The people"),
         (8, "Where you type"), (9, "Set up once"), (10, "The workspace and ~/.archon"), (11, "The fields you will use"),
         (12, "Which workflow"), (13, "At each pause"), (14, "workflow run flags"), (15, "After a run"), (16, "Every command")]
PH = {n: ("Start here", "--setup") for n in (1, 2, 3)} | {n: ("Meet Archon", "--setup") for n in (4, 5, 6, 7)} |      {n: ("Set up", "--plan") for n in (8, 9)} | {n: ("The workspace", "--build") for n in (10, 11)} |      {n: ("Doing the work", "--review") for n in (12, 13, 14, 15)} | {16: ("Reference", "--ship")}
assert len(S) == len(STEPS)

hero = f'''<section class="hero" id="top">
  <div>
    <h1>Archon in one page: what it is, where you type, which workflow, what you answer.</h1>
    <p class="lead">An AI coding agent will write code for you, but it decides its own steps. Archon {VERSION} lets your team write those steps down once (read, ask, plan, build, review, with people signing off in between) and makes the agent follow them every time. New here? Start with steps 1–3: the problem, ten basic words, and one real request told start to finish. Then <a href="archon-workspace-setup.html">set it up</a> and <a href="{RUNP}">run that request yourself</a>.</p>
    <div class="facts">
      <div><b>1</b>file describes the team's process</div>
      <div><b>{N_WAITS}</b>places the course's workflow stops for a person</div>
      <div><b>{N_QUESTIONS}</b>questions the agent asked before writing anything</div>
      <div><b>1</b>crash a person caught that the tests and the review missed</div>
      <div><b>${COST_MAIN + COST_FIX:.2f}</b>reported for the whole request, fix included</div>
      <div><b>{len(BUNDLED)}</b>ready-made workflows ship with Archon</div>
    </div>
  </div>
  <aside class="slack" aria-label="The short version">
    <div class="slack__bar"><span>The short version</span><span>Archon {VERSION}</span></div>
    <div class="slack__body">
      <p style="margin:0 0 8px"><b>Write</b> <code>.archon/workflows/…/x.yaml</code><br><span style="color:var(--ink-3)">nodes, depends_on, waits, checks</span></p>
      <p style="margin:0 0 8px"><b>Run</b> <code>archon workflow run x "…"</code><br><span style="color:var(--ink-3)">from the workspace, in place</span></p>
      <p style="margin:0 0 8px"><b>Answer</b> <code>archon workflow approve &lt;run&gt; "…"</code><br><span style="color:var(--ink-3)">reject is an answer too</span></p>
      <p style="margin:0"><b>Read</b> <code>archon workflow artifacts &lt;run&gt;</code><br><span style="color:var(--ink-3)">the files each node wrote</span></p>
    </div>
  </aside>
</section>
'''
real = card("real", "Where this comes from", f"""<p>Every Archon output on this page is real, from Archon {VERSION} on Windows (3 Nov 2026), captured by <code>tools/capture_cli.py</code>: <code>archon help</code>, <code>workflow run --help</code>, <code>doctor</code>, <code>workflow list --json</code> and each bundled workflow's <code>--full</code> description, and a dry run. The pause commands are from the course's real run. Items marked {DOC} are from the Archon docs at the v{VERSION} tag and were not run here. The cast is fictional.</p>
<p style="margin:0;font-size:.9rem;color:var(--ink-3)">Docs: <a href="https://archon.diy/reference/workflow-language/">workflow language</a> · <a href="https://archon.diy/reference/cli/">CLI</a> · <a href="https://archon.diy/guides/approval-nodes/">waits</a> · <a href="https://archon.diy/reference/sdlc-workflows/">sdlc workflows</a> · <a href="https://github.com/coleam00/Archon">github.com/coleam00/Archon</a>.</p>""")
words = card("words", "Archon words", gloss(list(ARCHON_WORDS.items())))
main = (hero + phase("--setup", "Start here", "steps 1–3 · why, ten everyday words, the course's run in plain words") + "".join(S[0:3])
        + phase("--setup", "Meet Archon", "steps 4–7 · the idea, one node, one workflow, the people") + "".join(S[3:7])
        + phase("--plan", "Set up", "steps 8–9 · where you type, once per machine") + "".join(S[7:9])
        + phase("--build", "The workspace", "steps 10–11 · the files and the fields") + "".join(S[9:11])
        + phase("--review", "Doing the work", "steps 12–15 · reference: which workflow, each pause, run flags, after a run") + "".join(S[11:15])
        + phase("--ship", "Reference", "step 16 · every command and option") + S[15] + words + real)
footer = ('<footer class="foot">Archon introduction · Archon ' + VERSION + ' · next: <a href="archon-workspace-setup.html">set up Archon for a repo</a> · '
          '<a href="archon-concepts-explained.html">concepts</a> · <a href="index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Archon Introduction", f"Start here for Archon {VERSION}: what it is, where you type, the workspace, its repo and ~/.archon, which bundled workflow fits which work, what you type at each pause, and every command, from real output.",
             "Archon introduction", "workflows · pauses · commands · files", len(STEPS), rail(STEPS, PH, [("words", "Archon words"), ("real", "Where this comes from")]), main, footer)
write(ROOT / "archon-introduction.html", html_)
