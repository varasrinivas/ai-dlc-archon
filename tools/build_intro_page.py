"""Build archon-introduction.html: what Archon is, where you type, which workflow for which work, what you type at each
pause, every `workflow run` flag, every command, the files in a repo and in ~/.archon.

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
from pagekit import (DOC, E, REAL, ROOT, card, disk, io, note, page, phase, plain, rail, see, step, table, tabs,  # noqa: E402
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


# ---------------- steps ----------------
S = []

S.append(step(1, "Meet Archon", "--setup", "the idea", "What Archon is, in four sentences",
              "Before any command: what kind of tool this is, so the rest of the page has somewhere to land.", "read · 2 min", f"""
<p>Archon is an open-source <b>workflow engine for AI coding</b>: you write how a kind of work gets done as a <b>YAML workflow</b>, and Archon runs it the same way every time. A workflow is a graph of <b>nodes</b>; an AI node hands a prompt to the agent you already use (Claude Code, Codex or Pi), a code node runs a command, and a <b>wait</b> node stops until a person answers. Each run works in its own <b>git worktree and branch</b>, and keeps a transcript, the files each node wrote and what it cost. Archon {VERSION} (29 Oct 2026) ships {len(BUNDLED)} workflows of its own, the <code>sdlc</code> pack, and you add yours in the repo's <code>.archon/</code> folder.</p>
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

S.append(step(2, "Meet Archon", "--setup", "the idea", "How one node runs",
              "Every workflow is built from this one move: a node gets inputs, does one job, and hands its output on.", "read · 2 min",
              node_cycle() + note("The agent in an AI node is a full Claude Code session in the run's worktree: it reads files, runs commands and edits code, and it reads the repo's <code>CLAUDE.md</code>. What it may do is set by the node (<code>allowed_tools</code>, <code>denied_tools</code>, <code>mutates_checkout: false</code>), not by Archon guessing.")))

NOTE = {"scan": "reads the repo, writes scan.md", "questions": "asks what only people can decide", "answer": "Kiran answers for Ravi and Meena",
        "plan": "files, tests, order → plan.md", "approve-plan": "Meena approves the plan", "checks": "verify + git log + diffstat",
        "review": "a second agent, read-only: READY / NOT-READY", "approve-change": "approve to push", "push": "git push -u origin HEAD"}
S.append(step(3, "Meet Archon", "--setup", "the idea", "A workflow is a graph you can read",
              "The course's workflow, drawn from its YAML file. Read it once now; the hands-on run walks through every box.", "read · 3 min",
              f"<p>This is <code>request-to-pr</code>, the team's workflow the course runs on priorauth-api: {len(NODES)} nodes, {sum(1 for n in NODES if n['kind'] == 'wait')} of them are waits for a person. Arrows are <code>depends_on</code>; the labels on them are <code>when:</code> conditions; the dashed loop is the requirements being revised until approved.</p>"
              + workflow_dag(NODES, "request-to-pr: the team's workflow, drawn from its YAML", NOTE)
              + tabs("wf", [("request-to-pr.yaml", WF_PATH, "the team's workflow · real file", "yaml", WF)])))

S.append(step(4, "Meet Archon", "--setup", "the people", "The people in this course",
              "The same fictional team as the AI-DLC course, so the two runs compare one to one.", "read · 1 min", table(
                  ["Person", "Role", "In the run"], [
                      ["Ravi Menon", "Nurse manager (the business)", "Sent the request in Slack; his answers are in the first wait"],
                      ["Kiran Rao", "Developer", "Runs Archon in a terminal; answers the waits; opens the PR"],
                      ["Meena Iyer", "Tech lead", "Rejects the first requirements with the screen team's names; approves the plan and the change"]])
              + note("Archon doesn't know who anyone is on a CLI-only install: an answer records the surface and the time, and the text says who decided. The course writes the names into the answer text, as the team's CLAUDE.md asks.")))

S.append(step(5, "Set up", "--plan", "where you type", "Three places you type, and one you don't",
              "Archon runs the agent for you. You type into Archon, not into Claude Code.", "read · 2 min",
              table(["Where", "What you do there", "In this course"], [
                  ["Terminal: <code>archon …</code>", "Start runs, see the attention queue, answer waits, read artifacts and logs", f"every step {REAL}"],
                  ["Web UI: <code>archon serve</code> → <code>http://localhost:3090</code>", "The same runs, with the graph, the events, and approve/reject buttons", f"setup page step 7 {DOC}"],
                  ["Chat: Slack, Telegram, Discord (plugins); <code>archon chat</code>", "Ask the orchestrator to pick and start a workflow; answer waits in the thread", DOC],
                  ["Claude Code itself", "Nothing during a run. Archon starts its own Claude Code sessions with your login", "—"]])
              + plain("Archon is the dispatcher with the job sheets; Claude Code is the technician it sends out. You talk to the dispatcher.")))

S.append(step(6, "Set up", "--plan", "once per machine", "Set up once",
              "Install the binary, connect the agent, check. The setup page shows each command's real output.", "about 5 minutes",
              io(you("irm https://archon.diy/install.ps1 | iex\narchon provider add claude\narchon doctor",
                     "curl -fsSL https://archon.diy/install | bash\narchon provider add claude\narchon doctor", "PowerShell", "Terminal"),
                 see(x(CLI["doctor"]["out"].strip()), f"archon doctor · {VERSION} · real", "Archon returns"))
              + note('The installer verifies the binary\'s checksum, puts it in <code>~/.archon/bin</code> and adds that folder to your user PATH (open a new terminal). It asks which providers to add; <code>archon provider add claude</code> does the same later. Claude Code must already be installed and signed in. Full walk-through: <a href="archon-workspace-setup.html">set up Archon for a repo</a>.')))

REPO_TREE = """priorauth-api/                       <b>the repo is the project: no workspace folder around it</b>
├── <span class="n">.archon/</span>                         committed: the team's Archon files
│   ├── <span class="n">config.yaml</span>                  assistant: claude · worktree.baseBranch: main
│   └── workflows/
│       └── team/                    <span class="m">a pack (any name)</span>
│           └── request-to-pr/       <span class="m">one workflow per folder</span>
│               ├── <span class="n">request-to-pr.yaml</span>
│               └── commands/
│                   ├── <span class="n">scan.md</span>          <span class="m">the prompt of the scan node</span>
│                   └── <span class="n">implement.md</span>     <span class="m">the prompt of each implement pass</span>
├── <span class="n">CLAUDE.md</span>                        the team's rules; Claude Code reads it in every AI node
├── <span class="n">.gitattributes</span>                   keeps verify.sh LF in every worktree
├── <span class="n">scripts/verify.sh</span>, verify.cmd     the one check (until_bash and the checks node)
├── <span class="n">docs-in/request.md</span>               Ravi's request, named in the run message
└── pom.xml, src/ …                  the code"""
HOME_TREE = """~/.archon/                           <b>yours, never committed</b> (C:\\Users\\you\\.archon on Windows)
├── bin/archon.exe                   the CLI
├── plugins/                         provider plugins (archon-provider-claude.exe)
├── config.yaml                      your defaults: assistant, tiers, concurrency
├── install.json                     which binary and version
├── archon.db                        SQLite: projects, runs, events, costs
└── workspaces/_local/priorauth-api/ one folder per project
    ├── worktrees/request-age/age-api/   the run's checkout, on branch request-age/age-api
    ├── logs/&lt;run-id&gt;.jsonl            the transcript
    └── artifacts/runs/&lt;run-id&gt;/        scan.md, questions.md, requirements.md, plan.md …"""
S.append(step(7, "The repo", "--build", "the files", "Files in a repo, and in ~/.archon",
              "Two places: what the team commits, and what stays on your machine.", "read · 3 min",
              io(disk(REPO_TREE, "In the repo (committed)"), disk(HOME_TREE, "In your home folder (not committed)"), stack=True)
              + table(["File", "Needed?", "Why"], [
                  ["<code>.archon/workflows/…/*.yaml</code>", "only for your own workflows", "The bundled 25 need nothing in the repo"],
                  ["<code>.archon/config.yaml</code>", "optional", "Repo defaults; wins over <code>~/.archon/config.yaml</code>. Worktree settings (<code>copyFiles</code>, <code>postCreate</code>) are read only from here"],
                  ["<code>CLAUDE.md</code>", "optional, recommended", "The agent's standing rules for this repo, in every AI node"],
                  ["<code>.archon/.env</code>", "optional, never commit", "Credentials for this repo (<code>archon setup --scope project</code>)"],
                  ["<code>.gitattributes</code>", "on Windows with autocrlf", "A worktree is a fresh checkout: without <code>*.sh text eol=lf</code> bash gets CRLF scripts"]], "kv")
              + note("Workflow commands need a git repository: outside one, <code>archon workflow list</code> says <code>" + x(CLI["outside-repo"]["out"].strip().splitlines()[0]) + "</code> (or register a plain folder with <code>--folder</code>).")))

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
S.append(step(8, "The repo", "--build", "authoring", "The fields you will use",
              "A short list from the workflow-language reference: enough to read any workflow and write a first one.", "reference",
              table(["Field", "What it does"], FIELDS, "kv")
              + io(you("archon validate workflows request-to-pr\narchon workflow run request-to-pr --dry-run --default-stubs \"Implement the request in docs-in/request.md\"", None, "any shell"),
                   see(x(STEP["dry-run"]["stdout"].split("STUBBED   questions")[0].strip()[:900] + "\n…\nPAUSED    answer (wait) — durable wait\n…\nSimulation outcome: paused"), "real · dry run, no model call", "Archon returns"))
              + note("<code>--dry-run</code> walks the graph with stub outputs: it starts no run and calls no model, and stops at the first wait (add <code>--pause-at-gates</code> to stop at approval gates too). Check every new workflow this way before it costs anything.")))

cat_rows = []
for w in BUNDLED:
    use, nf = full_desc(w["name"])
    cat_rows.append([f"<code>{w['name']}</code>", x(w["description"]), x(use) or "—"])
S.append(step(9, "Doing the work", "--review", "which workflow", "Which workflow for which work",
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
S.append(step(10, "Doing the work", "--review", "at a pause", "What you type at each pause",
              "A wait node stops the run and puts it in the attention queue. The form it declares says what it accepts.", "reference",
              table(["Form", "You answer with", "The next node reads"], [
                  ["<code>message</code> (default)", "<code>archon workflow answer &lt;run&gt; --occurrence &lt;id&gt; --text \"…\"</code> (or <code>approve &lt;run&gt; \"…\"</code>)", "<code>$id.output.text</code>"],
                  ["<code>approval</code>", "<code>archon workflow approve &lt;run&gt; \"…\"</code> · <code>archon workflow reject &lt;run&gt; \"…\"</code>", "<code>$id.output.decision</code>, <code>.text</code>"],
                  ["<code>select</code>", "<code>archon workflow respond &lt;run&gt; &lt;option-id&gt; \"…\"</code>", "<code>$id.output.decision</code>, <code>.text</code>"],
                  ["<code>multi_select</code>", "<code>archon workflow answer &lt;run&gt; --occurrence &lt;id&gt; --choose a --choose b</code>", "<code>$id.output.decisions</code>, <code>.text</code>"]])
              + io(you("archon workflow attention\narchon workflow wait &lt;run-id&gt; --json", None, "find what is waiting"),
                   see(x(tail), "real · printed under every pause in the course run", "Archon returns"))
              + plain("<b>Reject is an answer, not a stop.</b> The run carries on with decision <code>reject</code>; the workflow decides what that means. In <code>request-to-pr</code>, a rejected requirements draft is revised (the loop_group), a rejected plan or change goes to a <code>cancel:</code> node.")
              + note("Answering from the CLI continues the run in that terminal until the next pause or the end. Add <code>--json</code> to record the answer and return at once; <code>archon serve</code> or <code>archon workflow wake</code> then continues it.")))

S.append(step(11, "Doing the work", "--review", "starting a run", "Every <code>workflow run</code> flag",
              "From the real <code>archon workflow run --help</code>. The ones the course uses are first.", "reference",
              table(["Flag", "What it does"], [[f"<code>{x(f)}</code>", x(d)] for f, d in RUN_OPTS], "kv")
              + note("The course starts its run with <code>archon workflow run request-to-pr --branch request-age/age-api --detach \"Implement the request in docs-in/request.md\"</code>: a named branch (so the worktree and the PR are easy to find), in the background (so the terminal is free while it works).")))

S.append(step(12, "Doing the work", "--review", "after a run", "After a run, and between runs",
              "Where to look, and how to tidy up.", "reference", table(["Command", "What it shows or does"], [
                  ["<code>archon workflow runs</code> · <code>status</code>", "recent runs of this project; running and paused ones"],
                  ["<code>archon workflow get &lt;run-id&gt;</code>", "one run: status, worktree path, branch, cost, artifacts"],
                  ["<code>archon workflow logs &lt;run-id&gt; --format text</code>", "the transcript as progress lines (<code>--follow</code> to stream)"],
                  ["<code>archon workflow artifacts &lt;run-id&gt; [file]</code>", "the files the run wrote; print one"],
                  ["<code>archon workflow resume &lt;run-id&gt;</code>", "continue a failed or paused run; finished nodes are replayed, not re-run"],
                  ["<code>archon workflow cancel</code> · <code>abandon &lt;run-id&gt;</code>", "stop a run · mark it cancelled and remove its worktree (keeps the branch)"],
                  ["<code>archon isolation list</code>", "every worktree Archon made"],
                  ["<code>archon complete &lt;branch&gt;</code>", "remove a branch's worktree and local branch (the remote branch stays)"],
                  ["<code>archon isolation cleanup [days]</code> · <code>--merged</code>", "remove old (default 7 days) or merged worktrees; keeps anything unpushed or uncommitted"]], "kv")))

S.append(step(13, "Reference", "--ship", "every command", "Every command",
              f"All {len(COMMANDS)} entries of the real <code>archon help</code> in {VERSION}, and its global options.", "reference",
              '<div class="flist">' + table(["Command", "What it does"], [[f"<code>{x(c)}</code>", x(d)] for c, d in COMMANDS], "kv") + "</div>"
              + '<p style="margin-top:14px"><b>Options</b> (they apply to the commands named in each line):</p><div class="flist">'
              + table(["Option", "What it does"], [[f"<code>{x(f)}</code>", x(d)] for f, d in OPTIONS], "kv") + "</div>"))

STEPS = [(1, "What Archon is"), (2, "How one node runs"), (3, "A workflow is a graph"), (4, "The people"),
         (5, "Where you type"), (6, "Set up once"), (7, "Files in a repo"), (8, "The fields you will use"),
         (9, "Which workflow"), (10, "At each pause"), (11, "workflow run flags"), (12, "After a run"), (13, "Every command")]
PH = {n: ("Meet Archon", "--setup") for n in (1, 2, 3, 4)} | {n: ("Set up", "--plan") for n in (5, 6)} | \
     {n: ("The repo", "--build") for n in (7, 8)} | {n: ("Doing the work", "--review") for n in (9, 10, 11, 12)} | {13: ("Reference", "--ship")}
assert len(S) == len(STEPS)

hero = f'''<section class="hero" id="top">
  <div>
    <h1>Archon in one page: what it is, where you type, which workflow, what you answer.</h1>
    <p class="lead">Archon {VERSION} turns how your team works into a YAML file and runs it with the agent you already use. This page is the map: the idea, the files, the commands and the pauses, each from Archon's own output. Then <a href="archon-workspace-setup.html">set it up</a> and <a href="archon-hello-world-java/archon-hello-world-java-run.html">run one real request</a>.</p>
    <div class="facts">
      <div><b>1</b>workflow file = the team's process</div>
      <div><b>{len(BUNDLED)}</b>workflows bundled (the sdlc pack)</div>
      <div><b>10</b>node kinds: agent, code, wait …</div>
      <div><b>4</b>answer forms at a wait</div>
      <div><b>1</b>worktree and branch per run</div>
      <div><b>0</b>files the repo must have to start</div>
    </div>
  </div>
  <aside class="slack" aria-label="The short version">
    <div class="slack__bar"><span>The short version</span><span>Archon {VERSION}</span></div>
    <div class="slack__body">
      <p style="margin:0 0 8px"><b>Write</b> <code>.archon/workflows/…/x.yaml</code><br><span style="color:var(--ink-3)">nodes, depends_on, waits, checks</span></p>
      <p style="margin:0 0 8px"><b>Run</b> <code>archon workflow run x "…"</code><br><span style="color:var(--ink-3)">in its own worktree and branch</span></p>
      <p style="margin:0 0 8px"><b>Answer</b> <code>archon workflow approve &lt;run&gt; "…"</code><br><span style="color:var(--ink-3)">reject is an answer too</span></p>
      <p style="margin:0"><b>Read</b> <code>archon workflow artifacts &lt;run&gt;</code><br><span style="color:var(--ink-3)">the files each node wrote</span></p>
    </div>
  </aside>
</section>
'''
real = card("real", "Where this comes from", f"""<p>Every Archon output on this page is real, from Archon {VERSION} on Windows (3 Nov 2026), captured by <code>tools/capture_cli.py</code>: <code>archon help</code>, <code>workflow run --help</code>, <code>doctor</code>, <code>workflow list --json</code> and each bundled workflow's <code>--full</code> description, and a dry run. The pause commands are from the course's real run. Items marked {DOC} are from the Archon docs at the v{VERSION} tag and were not run here. The cast is fictional.</p>
<p style="margin:0;font-size:.9rem;color:var(--ink-3)">Docs: <a href="https://archon.diy/reference/workflow-language/">workflow language</a> · <a href="https://archon.diy/reference/cli/">CLI</a> · <a href="https://archon.diy/guides/approval-nodes/">waits</a> · <a href="https://archon.diy/reference/sdlc-workflows/">sdlc workflows</a> · <a href="https://github.com/coleam00/Archon">github.com/coleam00/Archon</a>.</p>""")
main = (hero + phase("--setup", "Meet Archon", "steps 1–4 · the idea, one node, one workflow, the people")
        + "".join(S[0:4]) + phase("--plan", "Set up", "steps 5–6 · where you type, once per machine") + "".join(S[4:6])
        + phase("--build", "The repo", "steps 7–8 · the files and the fields") + "".join(S[6:8])
        + phase("--review", "Doing the work", "steps 9–12 · which workflow, each pause, run flags, after a run") + "".join(S[8:12])
        + phase("--ship", "Reference", "every command and option") + S[12] + real)
footer = ('<footer class="foot">Archon introduction · Archon ' + VERSION + ' · next: <a href="archon-workspace-setup.html">set up Archon for a repo</a> · '
          '<a href="archon-concepts-explained.html">concepts</a> · <a href="index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Archon Introduction", f"Start here for Archon {VERSION}: what it is, where you type, the files in a repo and in ~/.archon, which bundled workflow fits which work, what you type at each pause, and every command, from real output.",
             "Archon introduction", "workflows · pauses · commands · files", len(STEPS), rail(STEPS, PH, [("real", "Where this comes from")]), main, footer)
write(ROOT / "archon-introduction.html", html_)
