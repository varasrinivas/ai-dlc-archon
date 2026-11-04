"""Build archon-concepts-onepage.html: Archon's concepts on one A4-landscape sheet (the AI-DLC course's aidlc-concepts-onepage.html).

Same design and print rules as the AI-DLC sheet: a header with the idea, a strip of the run's five phases,
twelve concept tiles (what, why, analogy, in the tool), and a bottom row of mappings, mix-ups, myths and
what you type. Facts are the concepts page's, condensed; node ids, counts and tiers are asserted against
the team workflow and the captured CLI output.

Usage: py -3.12 tools/build_onepage.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli_parse import workflow_nodes  # noqa: E402
from pagekit import ROOT, write  # noqa: E402

WF_TEXT = (ROOT / "tools/data/java/files/.archon/workflows/team/request-to-pr/request-to-pr.yaml").read_text(encoding="utf-8")
NODES = {n["id"]: n["kind"] for n in workflow_nodes(WF_TEXT)}
assert len(NODES) == 15 and list(NODES.values()).count("wait") == 4
for n, k in {"scan": "command", "questions": "prompt", "answer": "wait", "requirements": "loop_group", "plan": "prompt",
             "approve-plan": "wait", "stop-plan": "cancel", "implement": "loop", "checks": "bash", "review": "prompt",
             "approve-change": "wait", "stop-change": "cancel", "push": "bash"}.items():
    assert NODES[n] == k, (n, NODES[n])
assert "until_bash: ./scripts/verify.sh" in WF_TEXT and "fresh_context: true" in WF_TEXT
CLI = json.loads((ROOT / "tools/data/cli/cli.json").read_text(encoding="utf-8"))
VERSION = re.search(r"Archon CLI v([\d.]+)", CLI["version"]["out"]).group(1)
BUNDLED = sum(1 for w in json.loads(CLI["workflow-list-json"]["out"])["workflows"] if w["name"].startswith("archon-"))
assert (VERSION, BUNDLED) == ("0.13.2", 25)
for tier, model in [("small", "claude/haiku"), ("medium", "claude/sonnet"), ("large", "claude/opus")]:
    assert re.search(rf"{tier}\s+\(default: {model}\)", CLI["tier-list"]["out"]), tier
STEPS = {s["label"]: s for s in json.loads((ROOT / "archon-hello-world-java/java-run/steps.json").read_text(encoding="utf-8"))}
for lab, start in [("answer-1", "archon workflow answer "), ("reject-requirements", "archon workflow reject "),
                   ("approve-plan", "archon workflow approve "), ("plan-finish", "archon workflow respond "),
                   ("fix-run", "archon workflow run archon-implement --adopt "), ("complete", "archon complete ")]:
    assert STEPS[lab]["cmd"].startswith(start), lab

CSS = """@page{size:A4 landscape;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff;color:#1C1917;font:7.6pt/1.3 "Source Sans 3","Segoe UI",system-ui,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
code{font-family:"Source Code Pro",ui-monospace,Consolas,Menlo,monospace;font-size:.92em;background:#F0EEE9;padding:0 .2em;border-radius:2px}
.sheet{width:297mm;height:210mm;padding:5mm 7mm 4mm;display:grid;grid-template-rows:auto auto 1fr auto;gap:1.8mm;overflow:hidden}
.head{display:grid;grid-template-columns:auto 1fr auto;gap:5mm;align-items:start;border-bottom:1.2pt solid #1C1917;padding-bottom:1.6mm}
.head h1{margin:0;font-size:15pt;line-height:1;letter-spacing:-.01em;max-width:80mm;white-space:nowrap}
.head h1 small{display:block;font-size:7pt;font-weight:400;color:#6B6560;margin-top:1mm;letter-spacing:0;white-space:normal;max-width:80mm}
.head .idea{font-size:7.1pt;color:#1C1917;max-width:150mm;line-height:1.3}
.head .idea b{color:#6D28D9}
.legend{font-size:6.3pt;color:#6B6560;text-align:right;line-height:1.45;max-width:58mm}
.legend i{display:inline-block;width:6px;height:6px;border:1px dashed #D97706;background:#FFFBEB;margin:0 2px -1px 0}
.phases{display:grid;grid-template-columns:repeat(5,1fr);gap:2mm}
.ph{border:1pt solid var(--c);border-radius:2.2mm;padding:1.1mm 2mm 1mm;background:#fff;position:relative}
.ph b{display:block;color:var(--c);font-size:8.2pt}
.ph b span{float:right;font-family:"Source Code Pro",monospace;font-weight:600;font-size:6.8pt;color:#6B6560}
.ph .q{font-weight:700;font-size:7.4pt;margin:.6mm 0 .4mm}
.ph .o{color:#4B4742;font-size:6.8pt}
.ph .pp{color:var(--c);font-size:6.2pt;margin-top:.5mm;line-height:1.25}.ph .pp i{font-style:normal;font-weight:700}
.ph:not(:last-child)::after{content:"";position:absolute;right:-1.7mm;top:40%;width:1.2mm;height:1.2mm;background:#9CA3AF;border-radius:50%}
.body{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;grid-template-rows:repeat(3,1fr);gap:1.6mm;min-height:0}
.tile{border:0.8pt solid #DDD8D0;border-top:2.2pt solid var(--c);border-radius:2mm;padding:1.1mm 1.7mm 1mm;background:#FBFAF8;overflow:hidden;display:flex;flex-direction:column;gap:.35mm}
.tile h2{margin:0 0 .3mm;font-size:8.3pt;color:var(--c);line-height:1.1}
.tile p{margin:0;font-size:6.65pt;line-height:1.22}
.tile p b{color:#6B6560;font-weight:700;font-size:6.1pt;letter-spacing:.04em;text-transform:uppercase;margin-right:.5mm}
.tile .ana{background:#F3F1EC;border-radius:1.4mm;padding:.7mm 1.3mm;color:#4B4742;margin-top:auto}
.tile .ana b{color:#D97706}
.tile .tool{font-size:6.2pt;color:#6B6560;border-top:0.5pt dashed #DDD8D0;padding-top:.5mm}
.side{display:grid;grid-template-columns:1fr 1.35fr 1.1fr 1fr;gap:2.4mm;border-top:0.8pt solid #DDD8D0;padding-top:1.1mm}
.side h3{margin:0 0 .4mm;font-size:7.2pt;color:#1C1917}
.side table{border-collapse:collapse;width:100%;font-size:6.3pt}
.side td{padding:.15mm 1mm .15mm 0;vertical-align:top;border-bottom:0.5pt solid #ECE9E3}
.side td:first-child{font-weight:600;white-space:nowrap;padding-right:2mm}
.side td.arrow{color:#9CA3AF;padding:0 1mm}
.side .mix b{display:block;font-size:6.5pt}
.side .mix p{margin:0 0 .3mm;font-size:6.2pt;color:#4B4742}
.side .myth p{margin:0 0 .3mm;font-size:6.3pt}
.side .myth b{color:#9F1239;font-weight:600}
.side .gates{font-size:6.3pt;color:#4B4742;line-height:1.35}
.side .gates code{font-size:6.6pt}
.foot{display:flex;justify-content:space-between;gap:4mm;font-size:5.8pt;color:#6B6560;border-top:0.5pt solid #DDD8D0;padding-top:.7mm}
.foot a{color:inherit}
@media screen{body{background:#E9E6E0;padding:6mm}.sheet{margin:0 auto;box-shadow:0 10px 40px -20px rgba(0,0,0,.5)}}
@media screen and (max-width:1180px){body{overflow-x:auto}}
"""

SETUP, PLAN, BUILD, REVIEW, SHIP = "#5B6B7F", "#0E7490", "#C2410C", "#6D28D9", "#15803D"
GOLD = "#D97706"

PHASES = [
    (SETUP, "Set up", "once per repo", "Can Archon run here?",
     "install · <code>provider add claude</code> · <code>doctor</code> · telemetry off · Git Bash found",
     "the team's files in <code>.archon/</code>, validated and dry-run"),
    (PLAN, "Plan", "scan → requirements", "What exactly?",
     "<code>scan</code>, <code>questions</code>, wait <code>answer</code>, loop <code>requirements</code>",
     "you answer the questions; approve or send back the requirements"),
    (BUILD, "Build", "plan → implement", "In reviewable pieces?",
     "<code>plan</code>, wait <code>approve-plan</code>, loop <code>implement</code> until <code>verify.sh</code> exits 0",
     "you approve the plan; the check decides the code is done"),
    (REVIEW, "Review", "checks → approve", "Is it right?",
     "bash <code>checks</code>, prompt <code>review</code> (READY / NOT-READY), wait <code>approve-change</code>",
     "you approve, or reject and the run is cancelled"),
    (SHIP, "Ship", "push → complete", "Is it in main?",
     "bash <code>push</code>; then <code>archon complete &lt;branch&gt;</code>",
     "OURS: the pull request, its review and the merge"),
]

TILES = [
    (REVIEW, "Workflow", "A YAML file that says how one kind of work is done: its nodes, the order, the checks and the pauses.",
     "The process moves out of the model's head into a file the team owns, reviews and changes by pull request.",
     "A recipe card pinned in the kitchen; every cook follows it.",
     "<code>.archon/workflows/&lt;pack&gt;/&lt;name&gt;/&lt;name&gt;.yaml</code> · <code>archon workflow list</code> · <code>validate workflows</code>"),
    (REVIEW, "Nodes: one job each", "One step with one body: <code>prompt</code>/<code>command</code> (an agent), <code>bash</code>/<code>script</code> (code), <code>loop</code>/<code>loop_group</code>, <code>wait</code>, <code>cancel</code>, <code>include</code>/<code>workflow</code>.",
     "YAML coordinates, code computes, agents judge: the certain steps stay code, the agent gets the judgment calls.",
     "A production line: skilled stations, machines, and an inspector's desk.",
     "<code>output_format</code> = JSON reply, read as <code>$plan.output.summary</code> · <code>mutates_checkout: false</code>"),
    (PLAN, "The graph", "<code>depends_on</code> orders nodes (no edge = parallel); <code>when:</code> skips a node unless a condition holds; <code>trigger_rule</code> joins parents.",
     "One file holds every path (approved, rejected) without a script deciding at run time.",
     "A wiring diagram; a switch decides which branch lights up.",
     "<code>when: \"$approve-plan.output.decision == 'reject'\"</code> · <code>--dry-run</code> walks it free"),
    (REVIEW, "Commands and packs", "A command is a Markdown prompt a <code>command:</code> node sends; a pack is a folder of workflows, each with its own <code>commands/</code>.",
     "Long prompts are reviewed and diffed like code, and two workflows' <code>review.md</code> never collide.",
     "\"Make the sauce, see card 12\": card 12 sits in the recipe's own folder.",
     "team pack: <code>commands/scan.md</code>, <code>implement.md</code> · not Claude Code's <code>.claude/commands/</code>"),
    (BUILD, "Loops and their checks", "<code>loop</code> repeats a step, <code>loop_group</code> a small graph, until <code>until_bash</code> exits 0 (or <code>until_field</code>, <code>until</code>), at most <code>max_iterations</code>.",
     "\"Until the tests pass\" is only safe when code, not the model, decides it is done.",
     "A driving test: three tries, and the examiner says when you pass.",
     "<code>implement</code>: <code>until_bash: ./scripts/verify.sh</code>, max 3, <code>fresh_context</code> · passed in 1"),
    (GOLD, "Waits and the attention queue", "A <code>wait:</code> pauses the run durably until someone answers; <code>form</code>: <code>message</code>, <code>approval</code>, <code>select</code>, <code>multi_select</code>.",
     "People decide without a terminal hanging: a paused run holds no process and survives restarts.",
     "A form in a manager's in-tray; the clerk carries on once it is signed.",
     "<code>workflow attention</code> · <code>wait &lt;run&gt;</code> · <b style=\"color:#9F1239;text-transform:none;letter-spacing:0\">reject does not cancel</b>: route it"),
    (PLAN, "Runs", "One execution: a 32-character id, a status, a JSONL transcript, tokens and cost, kept in <code>archon.db</code>.",
     "You can always say what ran, what the agent was told and said, who answered, and what it cost.",
     "A parcel's tracking number.",
     "<code>--detach</code> · <code>workflow runs</code> · <code>get</code> · <code>logs --format text</code> · <code>resume</code> · <code>abandon</code>"),
    (PLAN, "A worktree per run", "Each run works in its own git worktree and branch under <code>~/.archon/workspaces/</code>; your checkout stays as you left it.",
     "Several runs can change the same files at once; a result you don't like is a branch you drop.",
     "A builder draws on a copy of the plans, not the originals.",
     "<code>--branch</code> · <code>--no-worktree</code> · <code>isolation list</code> · <code>complete &lt;branch&gt;</code> · not a sandbox"),
    (PLAN, "Artifacts and variables", "Files a run writes to <code>$ARTIFACTS_DIR</code>, outside the repo; placeholders <code>$USER_MESSAGE</code>, <code>$BASE_BRANCH</code>, <code>$&lt;node&gt;.output</code>.",
     "Nodes hand work over through files, so a fresh session reads just <code>plan.md</code> and stays focused.",
     "The surveyor's folder of working papers; the house gets only the work.",
     "<code>scan.md</code> … <code>review.md</code> · <code>workflow artifacts &lt;run&gt; &lt;file&gt;</code> · never in git"),
    (SETUP, "Providers and tiers", "Archon runs the agent you have (Claude Code, Codex, Pi) with your login; a tier names a provider and model.",
     "The team keeps its agent and its <code>CLAUDE.md</code>; cheap steps can use a cheaper model.",
     "A staffing agency: Archon books the work, your agencies send the people.",
     "<code>assistant: claude</code> · small = haiku · medium = sonnet · large = opus · <code>ai tier list</code>"),
    (SETUP, "Where things live", "The repo's <code>.archon/</code> (workflows, config: shared, committed) and your <code>~/.archon/</code> (binary, plugins, <code>archon.db</code>, workspaces: yours).",
     "The process travels with the code; the runs stay on the machine that ran them.",
     "The cookbook in the restaurant; each cook's notebook in their locker.",
     "repo config wins over home · credentials in <code>.env</code> · first run registers the project"),
    (SHIP, f"Surfaces and the sdlc pack", f"Start and answer runs from the CLI, the Web UI (<code>archon serve</code>, :3090), chat or triggers. {BUNDLED} bundled workflows: <code>archon-ship</code> and its queues.",
     "A decision reaches whoever can make it; the pack shows what a full process looks like.",
     "A shop with a counter, a website and a phone; a car plant next to your garage.",
     "<code>archon-plan</code>, <code>-investigate</code>, <code>-review</code> alone · the factory needs <code>gh</code> and CI"),
]
assert len(TILES) == 12

MAPPING = [("Intent", "a run (run id)"), ("Scope", "which workflow you run"), ("Stage", "node"),
           ("Gate 1 / 2 &lt;why&gt;", "<code>wait</code>, <code>form: approval</code>"), ("Request Changes", "reject in a <code>loop_group</code>"),
           ("Verification command", "<code>until_bash</code> + bash node"), ("<code>aidlc/</code> record", "artifacts + transcript, not committed"),
           ("<code>/aidlc</code> in Claude", "<code>archon workflow run</code>")]
MIX = [("run ≠ workflow ≠ command", "one execution · the YAML process · one prompt file a node sends"),
       ("wait ≠ cancel ≠ reject", "a pause · a node that ends the run · an answer the YAML must route"),
       ("loop ≠ loop_group ≠ retry", "repeat one step · repeat a small graph · run a failed node again"),
       ("worktree ≠ sandbox ≠ branch", "a second checkout · isolation it doesn't give · what the worktree is on"),
       ("artifacts ≠ the repo", "per-run papers in <code>~/.archon</code> · only the code and tests")]
MYTHS = [("\"Reject stops the run.\"", "Only where a <code>cancel:</code> node says so."),
         ("\"It's an AI model.\"", "It is an engine that runs your agent."),
         ("\"The worktree keeps the agent safe.\"", "It keeps your checkout clean; it is not a sandbox."),
         ("\"Old workflow names still work.\"", "0.12.0 removed <code>archon-fix-github-issue</code> and others."),
         ("\"Telemetry is off.\"", "It is on: <code>ARCHON_TELEMETRY_DISABLED=1</code>.")]

phases = "".join(f'<div class="ph" style="--c:{c}"><b>{n}<span>{s}</span></b><div class="q">{q}</div><div class="o">{o}</div>'
                 f'<div class="pp"><i>You:</i> {p}</div></div>' for c, n, s, q, o, p in PHASES)
tiles = "".join(f'<article class="tile" style="--c:{c}"><h2>{h}</h2><p><b>What</b>{w}</p><p><b>Why</b>{y}</p>'
                f'<p class="ana"><b>Analogy</b> {a}</p><p class="tool">{tl}</p></article>' for c, h, w, y, a, tl in TILES)
side = ('<section class="side"><div><h3>AI-DLC → Archon</h3><table>'
        + "".join(f'<tr><td>{a}</td><td class="arrow">→</td><td>{b}</td></tr>' for a, b in MAPPING) + "</table></div>"
        + '<div><h3>Easy to mix up</h3>' + "".join(f'<div class="mix"><b>{a}</b><p>{b}</p></div>' for a, b in MIX) + "</div>"
        + '<div><h3>Five myths</h3><div class="myth">' + "".join(f'<p class="myth"><b>{a}</b> {b}</p>' for a, b in MYTHS) + "</div></div>"
        + '<div><h3>At a pause you type</h3><div class="gates"><code>archon workflow attention</code> (what waits) · '
          '<code>answer &lt;run&gt; --occurrence &lt;id&gt; --text "…"</code> · <code>approve &lt;run&gt; "why"</code> · '
          '<code>reject &lt;run&gt; "what to change"</code> · <code>respond &lt;run&gt; &lt;option&gt;</code></div>'
          '<h3 style="margin-top:1mm">From run to PR · OURS</h3><div class="gates">One run = one branch (<code>--branch</code>). '
          'Push from the workflow or by hand, open the PR, merge; then <code>archon complete &lt;branch&gt;</code>. '
          'A follow-up fix: <code>archon-implement --adopt &lt;run&gt;</code>.</div></div></section>')

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Archon Concepts, One Page</title>
<meta name="description" content="Archon {VERSION}'s concepts on one A4 page: the run's five phases, twelve concepts with what, why and an analogy, AI-DLC to Archon, mix-ups, myths, and what you type at a pause.">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Source+Code+Pro:wght@400;600&display=swap" rel="stylesheet">
<style>
{CSS}</style></head><body><div class="sheet">
<header class="head"><h1>Archon concepts on one page<small>Archon {VERSION} (coleam00/Archon, 29 Oct 2026) with Claude Code · one analogy throughout: a restaurant kitchen</small></h1><div class="idea"><b>The idea.</b> How your team works becomes a <b>YAML workflow</b>: a graph of nodes, some an <b>AI agent</b> with a prompt, some <b>plain code</b>, some a <b>pause where a person decides</b>. Archon runs it the same way every time, each run in <b>its own worktree and branch</b>, checks the agent's work with commands instead of taking its word, and keeps the transcript, the files each step wrote and the cost. It brings no model: it drives the agent you already use.</div><div class="legend"><i></i> wait: the run pauses until a person answers<br>phases and node ids: the course's <code>request-to-pr</code> · OURS = team convention, not the tool</div></header>
<section class="phases">{phases}</section>
<section class="body">{tiles}</section>
{side}
<footer class="foot"><span>Sources: github.com/coleam00/Archon (v{VERSION}) · archon.diy (Why Archon; Workflow language; Asking for an answer; Loop nodes; Worktrees; Archon directories; SDLC pack; Configuration), read at the v{VERSION} tag. Definitions paraphrased; examples from the course's run of 3 Nov 2026; analogies ours.</span><span>Companions: <a href="archon-concepts-explained.html">concepts explained</a> · <a href="archon-concepts-map.svg">concept map</a> · <a href="index.html">the course</a></span></footer>
</div></body></html>
"""
write(ROOT / "archon-concepts-onepage.html", page)
