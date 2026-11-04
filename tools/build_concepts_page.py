"""Build archon-concepts-explained.html: Archon's concepts, one card each (what, why, how, example, analogy, test).

Design: the AI-DLC course's concepts page (tools/frame/concepts.css/.js, copied by make_frame.py).
Facts come from the Archon v0.13.2 docs (packages/docs-web in the release tag) and the course's own run; examples
name the run's real nodes, which this script reads from the team workflow file so they can't drift from it.

Usage: py -3.12 tools/build_concepts_page.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pagekit import E, ROOT, multirepo_facts, write  # noqa: E402

FRAME = ROOT / "tools" / "frame"
WF = (ROOT / "tools/data/java/files/.archon/workflows/team/request-to-pr/request-to-pr.yaml").read_text(encoding="utf-8")
NODES = re.findall(r"^\s*- id: ([\w-]+)", WF, re.M)
for n in ["scan", "questions", "answer", "requirements", "write-requirements", "review-requirements", "plan", "approve-plan",
          "stop-plan", "implement", "checks", "review", "approve-change", "stop-change", "push"]:
    assert n in NODES, n
CLI = json.loads((ROOT / "tools/data/cli/cli.json").read_text(encoding="utf-8"))
VERSION = re.search(r"Archon CLI v([\d.]+)", CLI["version"]["out"]).group(1)
BUNDLED = sum(1 for w in json.loads(CLI["workflow-list-json"]["out"])["workflows"] if w["name"].startswith("archon-"))
assert BUNDLED == 25, BUNDLED
multirepo_facts(CLI)  # the folder-project lines below are documented, not run: tie them to the docs and the help

BULB = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2a7 7 0 0 0-4 12.7V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.3A7 7 0 0 0 12 2z"/><path d="M9 21h6"/></svg>'


def concept(cid, title, what, why, how, ex, ana, got, confuse):
    return (f'<section class="card concept" id="{cid}"><h2>{title}</h2>'
            f'<span class="lab">What it is</span><p>{what}</p>'
            f'<span class="lab">Why Archon has it</span><p>{why}</p>'
            f'<span class="lab">How it works in the tool</span>{how}'
            f'<span class="lab">Example from the course run</span><p class="ex">{ex}</p>'
            f'<div class="ana">{BULB}<div><b>In everyday terms</b>{ana}</div></div>'
            f'<div class="got"><b>You\'ve got it when</b> {got}</div>'
            f'<p class="confuse"><b>Don\'t confuse with:</b> {confuse}</p></section>\n')


def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


# ---------- the concept map (theme tokens, so it follows light and dark mode) ----------
def tx(x, y, s, size=13, w=400, fill="var(--ink)", anchor="middle", mono=False):
    fam = "font-family:var(--mono);" if mono else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" style="{fam}fill:{fill};font-size:{size}px;font-weight:{w}">{E(s)}</text>'


def rect(x, y, w, h, col, op=.12, dash=False, rx=12):
    d = "stroke-dasharray:6 4;" if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" style="fill:{col};fill-opacity:{op};stroke:{col};stroke-width:1.6;{d}"/>'


def ln(x1, y1, x2, y2, dash=False):
    d = "stroke-dasharray:5 4;" if dash else ""
    return f'<path d="M{x1} {y1} L{x2} {y2}" style="stroke:var(--ink-3);stroke-width:1.6;fill:none;{d}" marker-end="url(#ah)"/>'


def concept_map():
    A, G, O, K, I3 = "var(--accent)", "var(--gold)", "var(--ours)", "var(--ok)", "var(--ink-3)"
    p = ['<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill:var(--ink-3)"/></marker></defs>']
    p.append(tx(20, 30, "A workflow file runs as a graph, in its own worktree, and stops where a person decides", 17, 700, anchor="start"))
    p.append(tx(20, 52, "Left: where you start and answer. Middle: what one run is. Right: what it leaves behind. Dashed = a pause for a person.", 12, 400, I3, "start"))
    # you
    p.append(rect(20, 80, 190, 300, O, .06))
    p.append(tx(115, 104, "You", 15, 700, O))
    for i, (a, b) in enumerate([("CLI", "archon workflow run"), ("Web UI", "archon serve · :3090"), ("Chat", "Slack, Telegram, Discord"), ("Triggers", "schedules, webhooks")]):
        y = 124 + i * 62
        p.append(rect(36, y, 158, 48, O, .1, rx=9))
        p.append(tx(115, y + 20, a, 13, 700))
        p.append(tx(115, y + 37, b, 10.5, 400, I3, mono=True))
    # the run
    p.append(rect(240, 80, 470, 300, A, .05))
    p.append(tx(475, 104, "One run of a workflow", 15, 700, A))
    p.append(tx(475, 122, ".archon/workflows/<pack>/<workflow>/<name>.yaml", 10.5, 400, I3, mono=True))
    nodes = [("scan", 262, 150, "command", A), ("questions", 262, 210, "prompt", A), ("answer", 262, 270, "wait", G),
             ("plan", 402, 150, "prompt", A), ("approve-plan", 402, 210, "wait", G), ("implement", 402, 270, "loop", A),
             ("checks", 552, 150, "bash", K), ("review", 552, 210, "prompt", A), ("push", 552, 270, "bash", K)]
    for name, x, y, kind, col in nodes:
        p.append(rect(x, y, 132, 42, col, .14, dash=(kind == "wait"), rx=8))
        p.append(tx(x + 66, y + 18, name, 12, 700, mono=True))
        p.append(tx(x + 66, y + 33, kind, 10.5, 400, I3))
    for (x1, y1, x2, y2) in [(328, 192, 328, 208), (328, 252, 328, 268), (394, 291, 400, 171), (468, 192, 468, 208), (468, 252, 468, 268),
                             (534, 291, 550, 171), (618, 192, 618, 208), (618, 252, 618, 268)]:
        p.append(ln(x1, y1, x2, y2))
    p.append(tx(475, 340, "AI nodes run Claude Code (or Codex, Pi) · bash and script nodes run code, no model", 11, 400, I3))
    p.append(tx(475, 360, "in a git worktree on its own branch: request-age/age-api", 11, 600, A))
    # what stays
    p.append(rect(740, 80, 220, 300, K, .06))
    p.append(tx(850, 104, "What the run leaves", 15, 700, K))
    for i, (a, b) in enumerate([("Artifacts", "$ARTIFACTS_DIR/*.md"), ("Transcript", "logs/<run-id>.jsonl"), ("Run record", "archon.db: status, cost"), ("The branch", "commits, pushed")]):
        y = 124 + i * 62
        p.append(rect(756, y, 188, 48, K, .1, rx=9))
        p.append(tx(850, y + 20, a, 13, 700))
        p.append(tx(850, y + 37, b, 10.5, 400, I3, mono=True))
    # arrows between columns
    p.append(ln(210, 150, 238, 150))
    p.append(tx(224, 140, "start", 10, 600, I3))
    p.append(ln(712, 230, 738, 230))
    # attention loop
    p.append(f'<path d="M328 312 C328 420, 115 430, 115 384" style="stroke:var(--gold);stroke-width:1.8;fill:none;stroke-dasharray:6 4" marker-end="url(#ah)"/>')
    p.append(tx(250, 420, "a wait pauses the run: it joins the attention queue until you answer (approve, reject, text)", 11.5, 600, G))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 440" role="img" aria-labelledby="ct"><title id="ct">Archon in one picture</title>'
            + "".join(p) + "</svg>")


C = []
C.append(concept(
    "workflow", "Workflow",
    "A YAML file that writes down how one kind of work gets done: its steps (nodes), the order between them, the checks that decide when a step is finished and the places where a person must decide. It needs a <code>name</code>, a <code>description</code> and <code>nodes</code>.",
    "A coding agent asked to \"fix this\" does what it likes on that run: it may skip the plan or the tests. Archon moves the process out of the model's head into a file the team owns and reviews, so every run follows the same steps.",
    ul(["Lives in the repo at <code>.archon/workflows/&lt;pack&gt;/&lt;workflow&gt;/&lt;name&gt;.yaml</code> (flat <code>.archon/workflows/foo.yaml</code> still works), or in <code>~/.archon/workflows/</code> for every repo on your machine.",
        f"{BUNDLED} workflows ship inside Archon {VERSION} (the <code>sdlc</code> pack). A repo workflow with the same name overrides a home one, and a home one overrides a bundled one.",
        "<code>archon workflow list</code> shows what it finds; <code>archon validate workflows</code> checks the file; <code>archon workflow run &lt;name&gt; \"message\"</code> starts it. Since 0.13.1 the name must match exactly."]),
    "The team's <code>request-to-pr</code> workflow: scan, ask, write requirements until approved, plan, approve, implement until <code>./scripts/verify.sh</code> passes, review, approve, push. Kiran ran it with the message <code>Implement the request in docs-in/request.md</code>.",
    "A recipe card pinned in a restaurant kitchen. Every cook follows the same card; the cook's skill goes into each step, but nobody skips the step where the chef tastes the sauce.",
    "you can say which file holds your team's process, and that changing the process is a pull request on that file.",
    "a <b>run</b> (one execution of a workflow) or a <b>command</b> (one prompt file a node uses).",
))
C.append(concept(
    "nodes", "Nodes: one job each",
    "A node is one step of a workflow. Each node has an <code>id</code> and exactly one body: <code>prompt</code> or <code>command</code> (an AI agent), <code>bash</code> or <code>script</code> (code, no AI), <code>loop</code> or <code>loop_group</code> (repeat until a check passes), <code>wait</code> (pause), <code>cancel</code> (end the run), <code>include</code> or <code>workflow</code> (reuse another workflow).",
    "The docs' rule of thumb is <i>YAML coordinates, code computes, agents judge</i>. Splitting the work into nodes lets the cheap, certain steps (run the tests, push) be code, and keeps the agent for the steps that need judgment.",
    ul(["An AI node's output is its final reply, readable later as <code>$id.output</code>. With <code>output_format</code> (a JSON Schema) the reply must be JSON, and later nodes read fields such as <code>$plan.output.summary</code>. A reply that doesn't fit the schema fails the node.",
        "A <code>bash</code> node's stdout is its output. It runs under bash on every OS (Git Bash on Windows).",
        "<code>mutates_checkout: false</code> asserts a node changes no file in the checkout; the engine compares git status before and after and fails the node if it did.",
        "<code>approval:</code> is deprecated; use <code>wait:</code> with <code>form: approval</code>."]),
    "In <code>request-to-pr</code>: <code>scan</code> is a command node, <code>questions</code>, <code>plan</code> and <code>review</code> are prompt nodes with <code>output_format</code>, <code>checks</code> and <code>push</code> are bash nodes, <code>implement</code> is a loop and <code>answer</code>, <code>approve-plan</code> and <code>approve-change</code> are waits.",
    "A production line: some stations are people with skill (the agent), some are machines that always do the same thing (bash), some are an inspector's desk where the line stops until someone signs (wait).",
    "you can look at a step and say whether it should be an agent, a script or a pause, and why.",
    "a Claude Code subagent. A node starts its own agent session (or none, for bash); what that agent does inside is up to it.",
))
C.append(concept(
    "graph", "The graph: depends_on, when, trigger_rule",
    "Nodes form a directed graph. <code>depends_on</code> lists the nodes that must finish first; nodes with no dependency between them run in parallel. <code>when:</code> skips a node unless a condition on earlier output holds. <code>trigger_rule</code> says how a node with several parents joins (default <code>all_success</code>).",
    "A graph says exactly what may happen in parallel and what must wait, and conditions let one file hold several paths (approved, rejected) without a script deciding at run time.",
    ul(["A node starts when every parent has settled and its <code>when:</code> and <code>trigger_rule</code> allow it. A skipped node passes \"skipped\" to its children.",
        "Conditions read outputs: <code>when: \"$approve-plan.output.decision == 'approve'\"</code>.",
        "<code>archon workflow run &lt;name&gt; --dry-run</code> walks the graph with stub outputs, without a run or a model call, and stops at the first wait."]),
    "<code>approve-plan</code> has two children: <code>stop-plan</code> (<code>when</code> the decision is <code>reject</code>, a <code>cancel</code> node) and <code>implement</code> (<code>when</code> it is <code>approve</code>). Exactly one runs.",
    "A wiring diagram: current flows only along the wires you drew, and a switch (when) decides which branch lights up.",
    "you can read a workflow and say which nodes could run at the same moment.",
    "a sequence of steps. Order comes only from <code>depends_on</code>; the order of nodes in the file means nothing.",
))
C.append(concept(
    "commands", "Commands and packs",
    "A command is a Markdown file of instructions that a <code>command:</code> node (or a loop's <code>command:</code>) sends to the agent. A pack is a folder of related workflows, each with its own <code>commands/</code> and <code>scripts/</code>, shared through git or as a plugin.",
    "Long prompts don't belong in YAML. A command file can be reviewed, diffed and reused like code, and the package boundary stops two workflows' <code>review.md</code> from colliding.",
    ul(["In a packaged workflow, <code>command: scan</code> resolves only from <code>&lt;pack&gt;/&lt;workflow&gt;/commands/scan.md</code>, with no fallback.",
        "Commands see the same variables as prompts: <code>$USER_MESSAGE</code>, <code>$ARTIFACTS_DIR</code>, <code>$BASE_BRANCH</code>, <code>$&lt;node&gt;.output</code>, <code>$LOOP_PREV_OUTPUT</code> in loops.",
        "<code>archon validate commands</code> checks them; <code>archon plugin copy &lt;id&gt;</code> copies an installed pack into the repo to edit."]),
    "The team's pack is <code>team</code>, with one workflow, <code>request-to-pr</code>, and two commands: <code>scan.md</code> (read only, write <code>scan.md</code> into the artifacts) and <code>implement.md</code> (the loop's prompt: implement the approved plan, run the verify script, commit).",
    "A recipe card (workflow) that says \"make the sauce, see card 12\" (command). Card 12 sits in the same folder as the recipe, so another recipe's card 12 never gets mixed in.",
    "you can say where the text a node sends to the agent comes from, and change it without touching the YAML.",
    "Claude Code's own slash commands in <code>.claude/commands/</code>. Archon's commands are read by Archon and passed to the agent as its prompt.",
))
C.append(concept(
    "loops", "Loops and their completion checks",
    "A <code>loop</code> node repeats one agent step; a <code>loop_group</code> repeats a small graph of nodes. Each needs <code>max_iterations</code> and at least one way to finish: <code>until_bash</code> (a shell check exits 0), <code>until_field</code> (a boolean in the step's structured output) or <code>until</code> (a word the agent prints; the weakest).",
    "\"Keep going until the tests pass\" is the most useful thing an agent loop does, and the most dangerous if the agent decides for itself when it is done. A shell check makes the code, not the model, decide.",
    ul(["<code>until_bash</code> runs after each pass; exit 0 ends the loop. Reaching <code>max_iterations</code> fails the node.",
        "<code>fresh_context: true</code> starts each pass in a new agent session; <code>$LOOP_PREV_OUTPUT</code> carries the previous pass's report.",
        "A <code>loop_group</code> whose body ends in a <code>wait</code> is the way to say \"revise until a person approves\": the next pass reads the answer as <code>$LOOP_PREV.&lt;wait-id&gt;.output.text</code>."]),
    "<code>implement</code> is a loop with <code>until_bash: ./scripts/verify.sh</code> and <code>max_iterations: 3</code>. <code>requirements</code> is a loop_group: <code>write-requirements</code> then <code>review-requirements</code> (a wait), until the decision is <code>approve</code>. Meena's rejection with the screen team's field names sent it round once more.",
    "A driving test: you can retake it up to three times, and the examiner (the check), not you, decides when you've passed.",
    "you can say what ends a loop, and why <code>until_bash</code> beats asking the agent to print DONE.",
    "a retry. A retry repeats a failed node the same way; a loop repeats a working step until its result is good enough.",
))
C.append(concept(
    "waits", "Waits and the attention queue",
    "A <code>wait:</code> node pauses the run durably: for a time, for an event, or (with <code>attention:</code>) until someone answers a question. The question's <code>form</code> fixes the answer: <code>message</code> (free text), <code>approval</code> (approve or reject, plus text), <code>select</code> or <code>multi_select</code> (declared options). Paused runs make up the attention queue.",
    "People decide; the run shouldn't hang a terminal while they think. A paused run holds no process, survives restarts, and can be answered from the CLI, the Web UI or chat. The docs call this \"human on the loop, not in it\".",
    ul(["<code>archon workflow attention</code> lists what is waiting; <code>archon workflow wait &lt;run-id&gt;</code> blocks until a run ends or needs you.",
        "<code>archon workflow approve &lt;run-id&gt; \"text\"</code>, <code>reject</code>, <code>respond &lt;option&gt;</code> and <code>answer --occurrence &lt;id&gt; --text</code> answer it. Answered from the CLI, the run continues in that terminal.",
        "<b>Reject does not cancel.</b> It is an answer like any other; the workflow must route it, for example to a <code>cancel:</code> node with <code>when: \"$approve.output.decision == 'reject'\"</code>."]),
    "The run stopped at all four waits: <code>answer</code> (six questions, answered by Kiran for Ravi and Meena), <code>review-requirements</code> (rejected once with the screen team's names, then approved), <code>approve-plan</code> (Meena) and <code>approve-change</code>.",
    "A form in a manager's in-tray. The work stops at the desk, nobody has to stand there waiting, and the clerk carries on the moment it is signed.",
    "you can add a gate to a workflow and say what happens on reject.",
    "an AI-DLC gate, which the tool's own engine opens at fixed stages. In Archon you place every pause yourself, and there are none unless you write them.",
))
C.append(concept(
    "runs", "Runs: id, status, transcript, cost",
    "One execution of a workflow. It has a 32-character run id, a status (running, paused, completed, failed, cancelled), a JSONL transcript of every event, and recorded token usage and cost, all in Archon's database.",
    "Governance: you can always say what ran, what the agent was told, what it said back, who answered each pause and what it cost. A failed run can be resumed from the nodes that already completed instead of starting over.",
    ul(["<code>archon workflow runs</code> lists recent runs; <code>archon workflow get &lt;run-id&gt;</code> shows one (path, branch, cost, artifacts); <code>archon workflow logs &lt;run-id&gt; --format text</code> reads the transcript.",
        "<code>--detach</code> starts a run in the background; <code>archon workflow resume &lt;run-id&gt;</code> continues a failed or paused one, replaying completed nodes (<code>Skipped (prior_success)</code>).",
        "<code>cancel</code> stops a run; <code>abandon</code> marks it cancelled and removes its worktree but keeps the branch."]),
    "Kiran's run <code>cd54631b…</code>: started with <code>--detach</code>, paused five times at its four waits (the requirements wait twice), and each answer continued it in Kiran's terminal, replaying the finished nodes first.",
    "A parcel's tracking number: one id that tells you where it is, every stop it made and what it cost to send.",
    "you can find, from a run id alone, what the agent wrote at any node.",
    "a conversation. A chat conversation can start runs; the run is the workflow execution with its own record.",
))
C.append(concept(
    "worktrees", "Isolation: a worktree per run",
    "A run against a git repo works in its own git worktree, a second checkout of the same repo on its own branch, under <code>~/.archon/workspaces/&lt;owner&gt;/&lt;repo&gt;/worktrees/</code>. <code>--branch</code> names the branch; <code>--no-worktree</code> runs in your own checkout.",
    "Several runs can change the same files at once without seeing each other, and your own checkout stays as you left it. If you don't like a result, you drop the branch.",
    ul(["The worktree is cut from the base branch (<code>worktree.baseBranch</code> in <code>.archon/config.yaml</code>, else detected). Only tracked files are in it, so commit what the run needs (or list ignored files in <code>worktree.copyFiles</code>).",
        "<code>archon isolation list</code> shows them; <code>archon complete &lt;branch&gt;</code> removes a worktree and its local branch (the remote branch stays); <code>archon isolation cleanup --merged</code> removes the merged ones.",
        "<b>Not a sandbox.</b> A worktree separates checkouts; commands a run executes can still touch files elsewhere.",
        "A <b>folder project</b> (a root holding several repos, see <a href=\"#places\">Where things live</a>) gets no worktree: it runs in place, and <code>--branch</code> is rejected."]),
    "The run's branch <code>request-age/age-api</code> lived in <code>~/.archon/workspaces/_local/priorauth-api/worktrees/request-age/age-api</code> (<code>_local</code> because the repo's remote is a folder, not GitHub). Kiran's own checkout stayed on <code>main</code> throughout.",
    "A builder gets a copy of the plans to draw on, not the originals in the office. Several builders can draw at once; the office keeps the clean set.",
    "you can say where a run's edits are, and how to get rid of them.",
    "a container. Container isolation exists for folder projects and is a separate option.",
))
C.append(concept(
    "artifacts", "Artifacts and variables",
    "Artifacts are files a run writes to <code>$ARTIFACTS_DIR</code>, a folder per run outside the repo. Variables are the placeholders Archon fills in prompts, commands and bash: <code>$USER_MESSAGE</code> (the run message), <code>$ARTIFACTS_DIR</code>, <code>$BASE_BRANCH</code>, <code>$WORKFLOW_ID</code>, <code>$&lt;node&gt;.output</code> and its fields.",
    "Nodes hand work to each other through files, not through one long chat. A fresh agent session can read just <code>plan.md</code> and stay focused, and the artifacts stay for people to read after the run, without cluttering the repo.",
    ul(["Artifacts live in <code>~/.archon/workspaces/&lt;owner&gt;/&lt;repo&gt;/artifacts/runs/&lt;run-id&gt;/</code>, never in git.",
        "<code>archon workflow artifacts &lt;run-id&gt;</code> lists them; add a file name to print one.",
        "Node outputs used in <code>bash:</code> are shell-quoted; a reply over 32,768 characters is spilled to a file and substituted as <code>$(cat …)</code>."]),
    "The run left <code>scan.md</code>, <code>questions.md</code>, <code>requirements.md</code>, <code>plan.md</code>, <code>implementation.md</code> and <code>review.md</code>. The repo got only the code and tests.",
    "The folder of working papers a surveyor leaves with the client: the house only gets the finished work, the folder explains how it was decided.",
    "you can say where to look for a run's requirements a month later, and why they are not in the repo.",
    "AI-DLC's record in <code>aidlc/</code>, which is committed with the workspace. Archon's artifacts are per run and stay on the machine that ran it unless you copy them.",
))
C.append(concept(
    "providers", "Providers, models and tiers",
    "A provider connects Archon to an agent: Claude Code, Codex or Pi (OpenCode and Copilot are deprecated). Archon brings no model of its own; it runs the agent with your login or key. A tier (<code>small</code>, <code>medium</code>, <code>large</code>) names a provider and model, so a workflow can say <code>model: large</code>.",
    "Teams already pay for an agent and have its project guidance (<code>CLAUDE.md</code>). Archon uses that agent as it is, and lets a workflow pick a cheaper model for easy steps.",
    ul(["<code>archon provider add claude</code> installs the provider plugin (it does not install Claude Code itself). Re-run it after each Archon upgrade.",
        "The repo's <code>.archon/config.yaml</code> <code>assistant:</code> sets the default; a workflow or node can override <code>provider</code> and <code>model</code>.",
        "<code>archon ai tier list</code> shows the tiers; on this install: small = claude/haiku, medium = claude/sonnet, large = claude/opus.",
        "Claude Code reads the repo's <code>CLAUDE.md</code> in every AI node, so the team's rules reach each step."]),
    "<code>assistant: claude</code> in <code>.archon/config.yaml</code>; no node sets a model, so every AI node used the provider's default. The run used the machine's claude.ai login: <code>archon doctor</code> reported <code>Assistant login: claude: usable</code>.",
    "A staffing agency: Archon books the work and keeps the timesheets; the people come from the agencies you already use.",
    "you can say which agent runs a node and where that is set.",
    "the workflow. Swapping the provider changes who does each step, not the steps.",
))
C.append(concept(
    "places", "Where things live: the repo, a folder project, and ~/.archon",
    "Two places. The project's <code>.archon/</code> holds what the team shares and commits: <code>workflows/</code>, <code>config.yaml</code>, optionally <code>commands/</code> and <code>scripts/</code>. Your home's <code>~/.archon/</code> holds the install: the binary, plugins, global config, <code>archon.db</code>, and <code>workspaces/</code> with every run's worktrees, logs and artifacts. The project is usually one repo; when a feature spans several repos, it is a <b>folder project</b>: a root that holds them, with the <code>.archon/</code> at the root.",
    "The process is the team's and travels with the code; the runs are yours and stay on your machine.",
    ul(["<code>~/.archon/config.yaml</code> holds your defaults (assistant, tiers, concurrency); the repo's <code>.archon/config.yaml</code> holds the repo's (assistant, worktree settings) and wins.",
        "Credentials go in <code>~/.archon/.env</code> (or the repo's <code>.archon/.env</code>, never committed); <code>archon setup</code> writes them.",
        "The first run in a repo registers it as a project (<code>archon project list</code>).",
        "<b>Several repos, one feature:</b> put them under one root, with <code>.archon/</code> and <code>CLAUDE.md</code> at the root, and run from there once with <code>--folder</code>. The agent works at the root, in place, and sees every repo. Archon makes no worktree, branch or PR for a folder project: the agent branches, commits and pushes in each repo, so the workflow's prompts must say so. <code>--container</code> adds a Docker overlay with an approval before writes reach the folders. Runs are stored in <code>~/.archon/workspaces/_folder/&lt;slug&gt;/</code>.",
        "Archon does not give one run a worktree in each of two repos. The docs' advice: the root as a folder project for cross-repo work, and each repo also its own project for changes that touch only it.",
        "Workflows can also live outside every repo: <code>~/.archon/workflows/</code> (in all your projects, not shared), or <code>--workflow-source &lt;dir&gt;</code> (read the workflow from one folder, run it against <code>--cwd</code>)."]),
    "Committed in <code>priorauth-api</code>: <code>.archon/config.yaml</code>, the <code>team/request-to-pr</code> workflow and its two commands, next to <code>CLAUDE.md</code> and <code>scripts/verify.sh</code>. Not committed: everything under <code>~/.archon/workspaces/_local/priorauth-api/</code>.",
    "The cookbook lives in the restaurant (repo); each cook's notebook and apron live in their locker (home).",
    "you can say which of the two folders a new teammate gets with <code>git clone</code>, and where the <code>.archon/</code> goes when a feature spans two repos.",
    "AI-DLC's workspace, a folder around the repos. For one repo Archon needs none: the repo is the project. For several, a folder project is that workspace, without per-run worktrees.",
))
C.append(concept(
    "surfaces", "Where you work: CLI, Web UI, chat, triggers",
    "The same runs can be started and answered from four places: the CLI (<code>archon …</code>), the Web UI (<code>archon serve</code>, port 3090: runs, chat, settings, an experimental workflow builder), chat platforms through plugins, and triggers (schedules, GitHub events, signed webhooks).",
    "A decision should reach whoever can make it, wherever they are, without them opening a terminal.",
    ul(["The Web UI shows each run's events, artifacts and graph, and approve/reject/resume/cancel buttons; alerts can notify the browser when a run pauses.",
        "<code>archon chat \"…\"</code> talks to the orchestrator, which can pick and start a workflow from your words (it reads each workflow's <code>description</code>).",
        "Triggers are deployment configuration, not workflow YAML."]),
    "The course run used the CLI only: <code>workflow run --detach</code>, <code>workflow wait</code>, <code>answer</code>, <code>reject</code>, <code>approve</code>. The same pauses would have shown in the Web UI's \"Needs your input\" banner.",
    "A shop with a counter, a website and a phone line: one stock room behind all three.",
    "you can answer a paused run from somewhere other than where it started.",
    "Claude Code's interactive session. You don't type into the agent; you type into Archon, which runs the agent.",
))
C.append(concept(
    "factory", "The sdlc pack: a factory of queues",
    f"The {BUNDLED} bundled workflows are one pack, <code>sdlc</code>. <code>archon-ship</code> takes one issue or request to a reviewed PR: triage, then investigate or plan if needed, then delivery rounds (implement, draft PR, review, CI). Around it, queues run on their own: <code>archon-intake</code> triages new issues, <code>archon-build-queue</code> works them, <code>archon-merge-queue</code> merges green, reviewed PRs.",
    "It is Archon's answer to \"what does a complete process look like\": every stage a separate, reusable workflow, people asked only for decisions that are theirs.",
    ul(["The pack talks to GitHub through <code>gh</code> (or a forge plugin): <code>archon workflow run archon-forge-check</code> proves it can.",
        "Read-only building blocks are useful alone: <code>archon-investigate</code> (root cause, changes nothing), <code>archon-plan</code>, <code>archon-review</code>, <code>archon-validate</code>.",
        "0.12.0 removed the older <code>archon-fix-github-issue</code>, <code>archon-idea-to-pr</code>, <code>archon-smart-pr-review</code> and <code>archon-assist</code>; tutorials that name them are out of date."]),
    "The course writes its own small workflow to learn the parts, then shows <code>archon-plan</code> on the same request for comparison. The full factory needs a GitHub repo, <code>gh</code> and CI, which the run doesn't have.",
    "A car plant next to your home garage: the same tools, but the plant has a line that runs while you sleep.",
    "you can say when you'd write your own workflow and when you'd run <code>archon-ship</code>.",
    "a template you must use. The pack is an example and a product; your repo's workflows sit beside it.",
))

MAPPING = [("Intent (one request, one record)", "One run of a workflow, with its run id", "AI-DLC keeps one intent across sessions and days; an Archon run is one execution, resumable while it's not finished."),
           ("Scope (express, feature, bugfix…)", "Which workflow you run", "AI-DLC ships 11 scopes over one fixed stage list; Archon has no fixed stages, you write or pick the workflow."),
           ("Stage (2.3 Requirements Analysis)", "Node (<code>write-requirements</code>)", "A stage has a lead persona and a fixed artifact; a node is whatever you wrote."),
           ("Gate (Approve / Request Changes)", "<code>wait</code> with <code>form: approval</code>", "Request Changes = reject inside a <code>loop_group</code> that revises and asks again."),
           ("Plan approval switch", "A <code>wait</code> node before the implement node", "In Archon it exists only if the workflow has it."),
           ("Verification command, checkpoint", "<code>until_bash</code> on the implement loop, a <code>bash</code> checks node", "The check is in the YAML, not recorded at a stage."),
           ("The record in <code>aidlc/</code>, committed", "Artifacts + transcript + run row, under <code>~/.archon</code>", "Not committed by default; copy artifacts into the repo (or a PR) if the team must keep them."),
           ("Workspace around the repos", "One repo: the repo itself, with <code>.archon/</code>. Several: a folder project around them", "A folder project (<code>--folder</code>) runs in place: no worktree, and the agent does the git in each repo. AI-DLC had no per-run worktree either."),
           ("AI personas (developer, quality…)", "Each AI node's prompt; optional inline <code>agents</code>", "No built-in cast: the prompt says who the agent is."),
           ("<code>/aidlc</code> inside Claude Code", "<code>archon workflow run</code> in a terminal (or Web UI, chat)", "Archon starts the agent; you don't sit in the agent's session.")]

MIS = [("\"Reject stops the run.\"", "Only if the workflow says so. Reject is an answer; route it to a <code>cancel:</code> node, or to a revision loop."),
       ("\"The worktree keeps the agent safe.\"", "It keeps your checkout clean. It is not a sandbox: commands can still reach other files."),
       ("\"Archon is an AI model / agent.\"", "It is an engine that runs your agent (Claude Code, Codex, Pi) inside steps you define."),
       ("\"Old tutorials' workflow names still work.\"", "0.12.0 removed <code>archon-fix-github-issue</code>, <code>archon-idea-to-pr</code> and others, and 0.13.1 made names exact."),
       ("\"The run's requirements end up in the repo.\"", "Artifacts live under <code>~/.archon</code>, per run. Commit them only if your workflow does."),
       ("\"Archon is the knowledge-base MCP server.\"", "That was Archon v1, kept on the <code>archive/v1-task-management-rag</code> branch. Today's Archon is the workflow engine."),
       ("\"bash: nodes need WSL on Windows.\"", "They need Git Bash. Archon looks in the usual Git locations; set <code>ARCHON_BASH_PATH</code> if Git is elsewhere."),
       ("\"Archon's files must go into each repo.\"", "Only in a one-repo project. For a feature across repos, a folder project keeps <code>.archon/</code> at the root that holds them; <code>~/.archon/workflows/</code> and <code>--workflow-source</code> keep workflows out of any repo."),
       ("\"Telemetry is off by default.\"", "It is on. Set <code>ARCHON_TELEMETRY_DISABLED=1</code> (or <code>DO_NOT_TRACK=1</code>); <code>archon telemetry status</code> checks.")]

QUIZ = [("Ravi sends a second request tomorrow. New workflow or new run?", "A new run of the same workflow, with the new request as its message. The workflow only changes if the team changes the process."),
        ("Where does Meena read the requirements the run wrote?", "In the run's artifacts: <code>archon workflow artifacts &lt;run-id&gt; requirements.md</code>, or the Web UI's run page. Not in the repo."),
        ("Meena rejects the code plan. What happens?", "<code>approve-plan</code> completes with decision <code>reject</code>; <code>stop-plan</code>'s <code>when</code> is true, so the run is cancelled. <code>implement</code> is skipped."),
        ("Who decides the implement loop is finished?", "<code>./scripts/verify.sh</code>: exit 0 after a pass ends the loop. Three failing passes fail the node."),
        ("Kiran's terminal crashed while the run was paused. Is the run lost?", "No. A paused run holds no process; answer it from any terminal or the Web UI with its run id."),
        ("Which nodes cost model tokens in <code>request-to-pr</code>?", "The prompt, command and loop nodes. <code>checks</code> and <code>push</code> (bash) and the waits cost none."),
        ("Why did the course add a <code>.gitattributes</code> before the run?", "The machine converts line endings (<code>core.autocrlf</code>), so a fresh worktree would get <code>verify.sh</code> with CRLF and bash would fail on it. <code>*.sh text eol=lf</code> keeps it runnable."),
        ("Ravi's next request needs priorauth-api and the reviewer screen's UI repo. Where does the team's <code>.archon/</code> go?", "At a root folder that holds both repos, registered as a folder project (<code>--folder</code>). The agent works there in place and does the git in each repo; Archon makes no worktree or PR for it.")]

SOURCES = [("https://github.com/coleam00/Archon", f"coleam00/Archon on GitHub (v{VERSION}, 29 Oct 2026): README"),
           ("https://archon.diy/getting-started/why-archon/", "Why Archon (core concepts, YAML coordinates / code computes / agents judge)"),
           ("https://archon.diy/reference/workflow-language/", "Workflow language reference (fields, node types, waits, loops, variables)"),
           ("https://archon.diy/guides/approval-nodes/", "Asking for an answer (wait forms, reject, rework until approved)"),
           ("https://archon.diy/guides/loop-nodes/", "Loop nodes (completion channels, fresh context, loop_group)"),
           ("https://archon.diy/guides/worktrees/", "Run work in parallel with worktrees (isolation, cleanup, not a sandbox)"),
           ("https://archon.diy/reference/archon-directories/", "Archon directories (~/.archon layout)"),
           ("https://archon.diy/guides/multi-repo-projects/", "Multi-repo projects (folder projects, in place, git per service)"),
           ("https://archon.diy/guides/global-workflows/", "Global workflows (~/.archon/workflows in every project)"),
           ("https://archon.diy/reference/sdlc-workflows/", "SDLC pack workflows (the bundled catalog, removed workflows)"),
           ("https://archon.diy/getting-started/sdlc-factory/", "Set up the SDLC factory (queues, gh, maintainers)"),
           ("https://archon.diy/reference/configuration/", "Configuration (repo config, ARCHON_BASH_PATH, telemetry)")]

head = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Archon Concepts, Explained</title>
<meta name="description" content="Archon {VERSION}'s concepts: workflows, nodes, the graph, commands and packs, loops, waits and the attention queue, runs, worktree isolation, artifacts, providers, where things live, the surfaces, and the sdlc pack. What each is, why Archon has it, how the tool does it, with examples from a real run and everyday analogies.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Source+Code+Pro:wght@400;600&display=swap" rel="stylesheet">
<style>
{(FRAME / "concepts.css").read_text(encoding="utf-8")}</style></head><body>
"""
ids = [("workflow", "Workflow"), ("nodes", "Nodes: one job each"), ("graph", "The graph: depends_on, when"), ("commands", "Commands and packs"),
       ("loops", "Loops and completion checks"), ("waits", "Waits and the attention queue"), ("runs", "Runs: id, status, transcript, cost"),
       ("worktrees", "Isolation: a worktree per run"), ("artifacts", "Artifacts and variables"), ("providers", "Providers, models and tiers"),
       ("places", "Where things live"), ("surfaces", "CLI, Web UI, chat, triggers"), ("factory", "The sdlc pack")]
assert len(ids) == len(C)
rail = ('<nav class="rail" aria-label="Contents"><h4>Start</h4><a href="#thesis" data-k="thesis">The big idea</a><a href="#map" data-k="map">One picture</a><h4>Concepts</h4>'
        + "".join(f'<a href="#{i}" data-k="{i}">{E(l)}</a>' for i, l in ids)
        + '<h4>Then</h4><a href="#mapping" data-k="mapping">AI-DLC → Archon</a><a href="#mistakes" data-k="mistakes">Misunderstandings</a><a href="#quiz" data-k="quiz">Check yourself</a><a href="#sources" data-k="sources">Sources</a></nav>')
thesis = (f'<section class="card thesis" id="thesis"><h1>The big idea, in one paragraph</h1><p class="big">Archon turns how your team works into a file. '
          "A workflow is a YAML graph of steps: some are an AI agent with a prompt, some are plain code, some are a pause where a person decides. "
          "Archon runs that graph the same way every time, each run in its own git branch and worktree, checks the agent's work with commands instead of taking its word, "
          "and keeps a transcript, the files each step wrote and the cost of every run. "
          "It brings no model: it drives the agent you already use (Claude Code, Codex or Pi). "
          "The docs put the split in six words: <i>YAML coordinates, code computes, agents judge.</i></p>"
          f'<div class="ana">{BULB}<div><b>In everyday terms</b>A restaurant kitchen with a recipe card for every dish. The cooks (agents) bring the skill; the card fixes the order, the timer (a check) says when the bread is done, and the chef (you) tastes before anything leaves the pass.</div></div>'
          f'<p class="lead" style="font-size:.95rem;margin:0">Thirteen concepts follow. Each: what it is, why Archon has it, how it shows up in the tool, an example from the course\'s real run (Kiran\'s <code>request-to-pr</code> run on priorauth-api), an analogy, a one-line test that you have understood it, and what not to confuse it with. Facts are from Archon {VERSION} and its docs.</p></section>\n')
mapc = f'<section class="card" id="map"><h2>Archon in one picture</h2><div class="chart">{concept_map()}</div></section>\n'
mapping = ('<section class="card" id="mapping"><h2>AI-DLC → Archon</h2><p>If you have done the AI-DLC course, this is where each idea went. Same request, same people; the hello-world run on this site lets you compare both on one change.</p>'
           "<table><thead><tr><th>AI-DLC</th><th>Archon</th><th>The difference</th></tr></thead><tbody>"
           + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in MAPPING) + "</tbody></table></section>\n")
mist = ('<section class="card" id="mistakes"><h2>Common misunderstandings</h2><div class="mis">'
        + "".join(f"<div><b>{a}</b>{b}</div>" for a, b in MIS) + "</div></section>\n")
quiz = ('<section class="card" id="quiz"><h2>Check yourself</h2><p class="lead" style="font-size:.95rem">Answer, then open.</p>'
        + "".join(f"<details><summary>{i + 1}. {q}</summary><p>{a}</p></details>" for i, (q, a) in enumerate(QUIZ)) + "</section>\n")
src = ('<section class="card" id="sources"><h2>Sources</h2><ul style="margin:0;padding-left:20px;font-size:.92rem">'
       + "".join(f'<li><a href="{u}">{E(t)}</a></li>' for u, t in SOURCES)
       + f'</ul><p style="margin:10px 0 0;font-size:.9rem;color:var(--ink-3)">Read at the v{VERSION} tag of the repository (the docs site is built from <code>packages/docs-web</code>). Examples are from the course\'s run on 3 Nov 2026; the analogies are ours.</p></section>\n')
page = (head + '<header class="top"><div class="top__in"><div class="brand">Archon concepts, explained<small>what · why · how · example · in everyday terms</small></div>'
        '<button class="btn" id="themeToggle" type="button" aria-pressed="false">Dark mode</button><button class="btn" type="button" onclick="window.print()">Print</button></div></header>\n'
        '<div class="shell">' + rail + "<main>\n" + thesis + mapc + "".join(C) + mapping + mist + quiz + src
        + '</main></div><footer class="foot">Archon concepts, explained · part of <a href="index.html">the Archon course</a> · <a href="#thesis">Back to top</a></footer>\n'
        + "<script>\n" + (FRAME / "concepts.js").read_text(encoding="utf-8") + "</script></body></html>\n")
write(ROOT / "archon-concepts-explained.html", page)
