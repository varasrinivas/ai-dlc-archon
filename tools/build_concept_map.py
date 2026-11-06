"""Build archon-concepts-map.svg: Archon's concepts in one standalone picture (the AI-DLC course's aidlc-concepts-map.svg).

Three columns answer a beginner's three questions: where does everything live, how does one run flow,
and who decides what; a bottom panel shows what each AI node hands Claude Code (pagekit.CLAUDE_MAP, condensed). Fixed light colours (it is opened on its own, not inside a themed page).

The middle column is drawn from the team workflow file (node ids, kinds, the loop checks), the left one is
checked against the captured ~/.archon inventory, so neither can drift from what the run actually had.

Usage: py -3.12 tools/build_concept_map.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli_parse import workflow_nodes  # noqa: E402
from pagekit import CLAUDE_MAP, E, ROOT, claude_facts, write  # noqa: E402

WF_TEXT = (ROOT / "tools/data/java/files/.archon/workflows/team/request-to-pr/request-to-pr.yaml").read_text(encoding="utf-8")
NODES = {n["id"]: n for n in workflow_nodes(WF_TEXT)}
assert len(NODES) == 15, len(NODES)
KIND = {k: n["kind"] for k, n in NODES.items()}
assert sum(1 for k in KIND.values() if k == "wait") == 4
assert KIND["requirements"] == "loop_group" and NODES["write-requirements"]["parent"] == "requirements"
assert KIND["implement"] == "loop" and "until_bash: ./scripts/verify.sh" in WF_TEXT and WF_TEXT.count("max_iterations: 3") == 2
assert "fresh_context: true" in WF_TEXT and "enum: [READY, NOT-READY]" in WF_TEXT and "required: [summary, files, tests]" in WF_TEXT
assert NODES["stop-plan"]["when"] == "$approve-plan.output.decision == 'reject'"
assert NODES["push"]["when"] == "$approve-change.output.decision == 'approve'"
assert "git -C priorauth-api push -u origin" in WF_TEXT and "git -C priorauth-api log --oneline main..HEAD" in WF_TEXT

INV = [x["path"] for x in json.loads((ROOT / "tools/data/cli/inventory.json").read_text(encoding="utf-8"))]
for p in ["archon.db", "bin/archon.exe", "config.yaml"]:
    assert p in INV, p
for pre in ["plugins/", "web-dist/", "workspaces/_folder/java-workspace/artifacts/runs/", "workspaces/_folder/java-workspace/logs/",
            "workspaces/_folder/java-workspace/workflow-source/runs/"]:
    assert any(x.startswith(pre) for x in INV), pre
assert not any(x.startswith("workspaces/_folder/java-workspace/worktrees/") for x in INV)
_NODES = json.loads((ROOT / "archon-hello-world-java/java-run/nodes.json").read_text(encoding="utf-8"))
RID = next(k for k, v in _NODES.items() if v["workflow"] == "request-to-pr")
ARTS = sorted(p.name for p in (ROOT / "archon-hello-world-java/java-run/artifacts" / RID).glob("*.md"))
_WS = ROOT / "archon-hello-world-java/java-workspace"
assert (_WS / ".gitignore").read_text(encoding="utf-8").strip().endswith("/priorauth-api/") and (_WS / "priorauth-api/pom.xml").exists()
assert ARTS == ["implementation.md", "plan.md", "questions.md", "requirements.md", "review.md", "scan.md"], ARTS
CLI = json.loads((ROOT / "tools/data/cli/cli.json").read_text(encoding="utf-8"))
VERSION = re.search(r"Archon CLI v([\d.]+)", CLI["version"]["out"]).group(1)
assert VERSION == "0.13.2"

# The bottom panel: CLAUDE_MAP condensed (its documented claims asserted against tools/data/docs/), and what the run's
# Claude sessions actually called, from the request-to-pr transcript.
claude_facts()
_LOG = next((ROOT / "archon-hello-world-java/java-run/logs").glob(f"{RID}*.jsonl")).read_text(encoding="utf-8")
TOOLS = {}
for _l in _LOG.splitlines():
    _d = json.loads(_l)
    if _d.get("type") == "provider_event" and _d["event"].get("type") == "tool_call":
        TOOLS[_d["event"]["name"]] = TOOLS.get(_d["event"]["name"], 0) + 1
assert "StructuredOutput" in TOOLS and not set(TOOLS) & {"Skill", "Task", "Agent"}, TOOLS
assert not re.search(r"^\s*(skills|agents|hooks|mcp):", WF_TEXT, re.M) and not (_WS / ".claude").exists()
CC_ROWS = [("prompt: · command:", "one session; command: is a prompt file, not a slash command"),
           ("loop + fresh_context", "a new session per pass (implement: 1 pass)"),
           ("context:", "a new, continued or forked session (questions continued scan's)"),
           ("output_format:", "a StructuredOutput tool call (questions, plan, review)"),
           ("allowed_tools", "the only limits: bypassPermissions, so no prompts"),
           ("skills: [name]", "only those skills, from .claude/skills/; none if left out"),
           ("agents:", "subagents that the node's agent starts with the Task tool"),
           ("hooks: · mcp: · plugins:", "SDK hooks, MCP servers, plugins: for this node only"),
           ("CLAUDE.md", "read in every session: project + user (settingSources)"),
           ("bash: · script: · wait:", "no Claude at all: Archon runs it, or waits for you")]
_MAPTXT = re.sub(r"<[^>]+>", "", " ".join(a + " " + b + " " + c for a, b, c in CLAUDE_MAP))
for _f in ["prompt:", "command: scan", "slash command", "fresh_context", "implement: 1 pass", "context:", "questions continued scan's session",
           "output_format:", "StructuredOutput", "3 calls: questions, plan, review", "allowed_tools", "bypassPermissions", "skills: [name]",
           ".claude/skills/", "no skills", "agents:", "Task", "hooks:", "mcp:", "plugins:", "for that node only", "CLAUDE.md", "settingSources",
           "bash:", "script:", "wait:", "no Claude at all"]:
    assert _f in _MAPTXT, _f  # each condensed row says what the full mapping says

INK, INK2, LINE, PANEL, SOFT = "#1C1917", "#6B6560", "#E7E5E4", "#FAFAF9", "#F5F5F4"
AI, CODE, WAIT, STOP = "#6D28D9", "#15803D", "#D97706", "#9F1239"
PH = {"setup": "#5B6B7F", "plan": "#0E7490", "build": "#C2410C", "review": "#6D28D9", "ship": "#15803D"}
SANS = "'Segoe UI', system-ui, sans-serif"
MONO = "ui-monospace, Consolas, Menlo, monospace"
COLOR = {"command": AI, "prompt": AI, "loop": AI, "loop_group": AI, "bash": CODE, "script": CODE, "wait": WAIT, "cancel": STOP}

P = []


def t(x, y, s, size=12, w=400, fill=INK, anchor="start", mono=False):
    P.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" '
             f'font-family="{MONO if mono else SANS}">{E(s)}</text>')


def r(x, y, w, h, fill="#FFFFFF", stroke=INK2, sw=1.8, rx=8, dash=False):
    d = ' stroke-dasharray="6 4"' if dash else ""
    P.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def path(d, col=INK2, dash=False):
    da = ' stroke-dasharray="5 4"' if dash else ""
    P.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.6"{da} marker-end="url(#ah)"/>')


def a(x1, y1, x2, y2, col=INK2, dash=False):
    path(f"M{x1} {y1} L{x2} {y2}", col, dash)


def files(x, y0, rows, step=20, size=11, gap=14, right=None):
    """Mono file name, then its note right after it (width estimated, asserted to fit)."""
    for i, (f, d) in enumerate(rows):
        y = y0 + i * step
        t(x, y, f, size, 600, mono=True)
        dx = x + len(f) * size * 0.56 + gap
        if right is not None:
            assert dx + len(d) * 5.1 <= right, (f, d)
        t(round(dx), y, d, 10, 400, INK2)


def node(nid, x, y, w=150, sub=None):
    k = KIND[nid]
    c = COLOR[k]
    r(x, y, w, 44, fill="#FFFBEB" if k == "wait" else "#FFFFFF", stroke=c, dash=(k == "wait"))
    t(x + 10, y + 19, nid, 12, 700, INK, mono=True)
    t(x + 10, y + 35, sub or k, 10, 400, INK2)


# ---- header ----
t(30, 42, "Archon concepts in one picture", 24, 700)
t(30, 66, "Three questions a beginner asks: where does everything live, how does one run flow, and who decides what. "
          "Analogy throughout: a restaurant kitchen with a recipe card for every dish.", 12.5, 400, INK2)

# ==== column 1: where things live =========================================================
r(30, 92, 500, 650, fill=PANEL, stroke=LINE, sw=1, rx=16)
t(48, 122, "Where things live", 17, 700, PH["setup"])
t(48, 142, "two places: the team's workspace with its repos, and your machine's ~/.archon", 11.5, 400, INK2)

r(48, 158, 464, 268, rx=12, stroke=INK)
t(60, 180, "java-workspace/", 13, 700, mono=True)
t(190, 180, "the team's workspace · its own git repo · committed", 11, 400, INK2)
t(60, 198, "the kitchen: the cookbook lives here; a folder project", 10.5, 400, PH["setup"])
r(60, 208, 440, 104, fill=SOFT, rx=8)
t(72, 226, ".archon/", 12, 700, mono=True)
t(140, 226, "what Archon reads from the workspace root", 10.5, 400, INK2)
files(84, 246, [("config.yaml", "assistant: claude (no worktree settings)"),
                ("workflows/team/request-to-pr/", "a pack (team) with one workflow")], step=18, right=496)
files(100, 282, [("request-to-pr.yaml", "the recipe card: 15 nodes, 4 waits"),
                 ("commands/scan.md, implement.md", "long prompts, kept out of YAML")], step=18, right=496)
r(60, 318, 440, 44, fill="#FFFFFF", stroke=INK2, dash=True, rx=8)
t(72, 336, "CLAUDE.md · scripts/verify.sh · docs-in/ · .gitignore", 11, 600, mono=True)
t(72, 352, "OURS: the rules (read in every AI node), the check, the request", 10, 400, INK2)
r(60, 368, 440, 50, fill="#FFFFFF", stroke=INK, rx=8)
t(72, 387, "priorauth-api/", 12, 700, mono=True)
t(184, 387, "the code repo · cloned inside · its own git, PRs", 10.5, 400, INK2)
t(72, 405, "the pantry: .gitignore keeps it out; the agent branches here", 10, 400, PH["setup"])

r(48, 440, 464, 286, rx=12, stroke=INK)
t(60, 462, "~/.archon/", 13, 700, mono=True)
t(146, 462, "your machine · never committed · the cook's locker", 11, 400, INK2)
files(72, 486, [("bin/archon.exe", "the CLI, one binary"),
                ("config.yaml · .env", "your defaults (tiers) · credentials"),
                ("plugins/", "providers: archon provider add claude"),
                ("archon.db", "every run: status, answers, tokens, cost"),
                ("web-dist/ · server/", "the Web UI, fetched by archon serve")], right=500)
r(60, 584, 440, 130, fill=SOFT, rx=8)
t(72, 604, "workspaces/_folder/java-workspace/", 12, 700, mono=True)
t(72, 620, "a folder project: no worktrees/, the run works in place", 10, 400, INK2)
files(84, 644, [("artifacts/runs/<run-id>/", "scan.md … review.md"),
                ("logs/<run-id>.jsonl", "the transcript: every event"),
                ("workflow-source/runs/<run-id>/", "the workflow as run")], step=22, right=496)

# ==== column 2: how one run flows ==========================================================
X2 = 568
r(X2 - 18, 92, 580, 650, fill=PANEL, stroke=LINE, sw=1, rx=16)
t(X2, 122, "How one run flows", 17, 700, PH["plan"])
t(X2, 142, 'cd java-workspace; archon workflow run request-to-pr --folder "…"', 11, 400, INK2, mono=True)


def band(y, h, ph, label, right=True):
    P.append(f'<rect x="{X2}" y="{y}" width="544" height="{h}" rx="10" fill="{PH[ph]}" fill-opacity=".05" '
             f'stroke="{PH[ph]}" stroke-opacity=".5" stroke-width="1"/>')
    t(X2 + 534 if right else X2 + 10, y + 16, label, 11, 700, PH[ph], anchor="end" if right else "start")


# Plan
band(156, 176, "plan", "PLAN · what exactly?")
node("scan", X2 + 12, 180, 150, "command · read only")
node("questions", X2 + 196, 180, 150, "prompt · JSON out")
node("answer", X2 + 380, 180, 152, "wait · free text")
a(X2 + 162, 202, X2 + 194, 202)
a(X2 + 346, 202, X2 + 378, 202)
a(X2 + 456, 224, X2 + 456, 237)
P.append(f'<rect x="{X2 + 12}" y="238" width="520" height="86" rx="10" fill="#FFFFFF" stroke="{AI}" stroke-width="1.4" stroke-dasharray="3 3"/>')
t(X2 + 22, 254, "requirements · loop_group · max 3 · until the decision is approve", 10.5, 700, AI)
node("write-requirements", X2 + 22, 262, 190, "prompt · requirements.md")
node("review-requirements", X2 + 252, 262, 190, "wait · form: approval")
a(X2 + 212, 284, X2 + 250, 284)
path(f"M{X2 + 347} 306 C{X2 + 347} 322, {X2 + 117} 322, {X2 + 117} 308", WAIT, True)
t(X2 + 450, 280, "reject →", 10, 700, WAIT)
t(X2 + 450, 293, "revise", 10, 700, WAIT)

# Build
band(342, 132, "build", "BUILD · in reviewable pieces")
a(X2 + 87, 324, X2 + 87, 364)
node("plan", X2 + 12, 366, 150, "prompt · files, tests")
node("approve-plan", X2 + 196, 366, 150, "wait · form: approval")
node("implement", X2 + 380, 366, 152, "loop · when approve")
a(X2 + 162, 388, X2 + 194, 388)
a(X2 + 346, 388, X2 + 378, 388)
node("stop-plan", X2 + 196, 422, 150, "cancel · when reject")
a(X2 + 271, 410, X2 + 271, 421, col=STOP)
t(X2 + 356, 432, "until_bash: ./scripts/verify.sh", 10, 700, mono=True)
t(X2 + 356, 448, "exit 0 ends it; 3 failed passes fail it", 10, 400, INK2)
t(X2 + 356, 462, "the code, not the model, says done", 10, 400, INK2)

# Review
band(484, 132, "review", "REVIEW · is it right?")
path(f"M{X2 + 532} 388 L{X2 + 552} 388 L{X2 + 552} 479 L{X2 + 87} 479 L{X2 + 87} 506")
node("checks", X2 + 12, 508, 150, "bash · tests, log, diff")
node("review", X2 + 196, 508, 150, "prompt · a verdict")
node("approve-change", X2 + 380, 508, 152, "wait · form: approval")
a(X2 + 162, 530, X2 + 194, 530)
a(X2 + 346, 530, X2 + 378, 530)
node("stop-change", X2 + 196, 564, 150, "cancel · when reject")
a(X2 + 420, 552, X2 + 348, 576, col=STOP)

# Ship
band(626, 62, "ship", "SHIP", right=False)
node("push", X2 + 380, 636, 152, "bash · git -C … push")
a(X2 + 490, 552, X2 + 490, 634, col=CODE)
t(X2 + 498, 598, "approve", 9, 700, CODE)
t(X2 + 12, 652, "pushes the branch the agent made in priorauth-api;", 10.5, 400, INK2)
t(X2 + 12, 668, "the pull request, the merge, the tidy-up are yours (OURS)", 10.5, 400, INK2)

# legend
for i, (lab, c, dash) in enumerate([("AI node: Claude Code runs it", AI, False), ("code: bash, no model", CODE, False),
                                     ("wait: the run pauses for you", WAIT, True), ("cancel: ends the run", STOP, False)]):
    x, y = X2 + (i % 2) * 272, 704 + (i // 2) * 16
    r(x, y - 10, 14, 11, fill="#FFFFFF", stroke=c, sw=1.6, rx=3, dash=dash)
    t(x + 20, y, lab, 10, 400, INK2)
t(X2, 734, "each run: in place in the workspace, artifacts and transcript, and a run id to find it by", 10.5, 600, PH["plan"])

# ==== column 3: who decides what ===========================================================
X3 = 1168
r(X3 - 18, 92, 480, 650, fill=PANEL, stroke=LINE, sw=1, rx=16)
t(X3, 122, "Who decides what", 17, 700, PH["review"])
t(X3, 142, "you decide; Archon runs and records; the agent works; code checks", 11.5, 400, INK2)

cards = [
    ("You · the chef at the pass", WAIT, True,
     [("write the workflow (a PR on the YAML), start the run", False),
      ("answer at every wait; archon workflow attention lists them:", False),
      ("answer <run> --occurrence <id> --text \"…\"", True),
      ("approve <run> \"why\" · reject <run> \"what to change\"", True),
      ("in the run: 7 questions answered, requirements rejected", False),
      ("once, plan approved, change rejected (a 500, by hand)", False)]),
    ("Archon · the expediter calling the orders", PH["plan"], False,
     [("walks the graph: depends_on, when, trigger_rule", False),
      ("starts each node in the workspace, pauses at waits", False),
      ("routes reject only where the YAML says (when: … 'reject')", False),
      ("records transcript, artifacts, tokens and cost per run", False)]),
    ("The agent · the cooks", AI, False,
     [("Claude Code (or Codex, Pi) inside AI nodes only", False),
      ("reads CLAUDE.md; one session per node or loop pass", False),
      ("tiers: small = haiku · medium = sonnet · large = opus", True)]),
    ("The code · the timer and the thermometer", CODE, False,
     [("until_bash: ./scripts/verify.sh ends the loop", True),
      ("bash nodes check and push without a model", False),
      ("mutates_checkout: false fails a node that edits files", False)]),
]
y = 160
for title, c, dash, lines in cards:
    h = 30 + 16 * len(lines) + 6
    r(X3, y, 444, h, fill="#FFFBEB" if dash else "#FFFFFF", stroke=c, dash=dash, rx=10)
    t(X3 + 12, y + 21, title, 13, 700, c)
    for i, (s, mono) in enumerate(lines):
        assert len(s) * (6.0 if mono else 5.4) < 420, s
        t(X3 + 12, y + 40 + i * 16, s, 10 if mono else 10.5, 400, INK, mono=mono)
    y += h + 12
r(X3, y, 444, 728 - y, fill=SOFT, stroke=LINE, sw=1, rx=10)
t(X3 + 12, y + 22, "Reject is an answer, not a stop.", 12.5, 700, STOP)
t(X3 + 12, y + 40, "Inside a loop_group it means \"revise\"; before a cancel node", 10.5, 400, INK2)
t(X3 + 12, y + 55, "it ends the run. In place means your own clones:", 10.5, 400, INK2)
t(X3 + 12, y + 70, "what the agent committed stays on its branch.", 10.5, 400, INK2)
t(X3 + 12, y + 92, "Every answer is kept with the run:", 10.5, 700, INK)
t(X3 + 12, y + 107, "who said what, and when, is in archon.db and the transcript.", 10.5, 400, INK2)

# ==== bottom: what an AI node hands Claude Code ===========================================
YB = 762
r(30, YB, 1600, 262, fill=PANEL, stroke=LINE, sw=1, rx=16)
t(48, YB + 30, "What an AI node hands Claude Code", 17, 700, AI)
t(48, YB + 50, "each prompt, command or loop pass is one Claude Code session, started by Archon's Claude provider through the "
               "Claude Agent SDK, in the workspace, with your login", 11.5, 400, INK2)
# the chain: node → Archon → session
r(48, YB + 70, 150, 44, stroke=AI)
t(58, YB + 89, "scan", 12, 700, mono=True)
t(58, YB + 105, "an AI node in the YAML", 10, 400, INK2)
a(198, YB + 92, 236, YB + 92, col=AI)
r(238, YB + 70, 300, 44, stroke=PH["plan"])
t(250, YB + 89, "Archon · the Claude provider", 12, 700, PH["plan"])
t(250, YB + 105, "Claude Agent SDK · bypassPermissions", 10, 400, INK2)
a(388, YB + 114, 388, YB + 130, col=AI)
r(48, YB + 132, 490, 92, stroke=AI, sw=2)
t(60, YB + 152, "a Claude Code session in java-workspace/", 12.5, 700, AI)
for i, chip in enumerate(["prompt", "tools", "skills", "subagents", "hooks", "MCP", "CLAUDE.md"]):
    cx = 60 + sum(len(c) * 6.4 + 22 for c in ["prompt", "tools", "skills", "subagents", "hooks", "MCP", "CLAUDE.md"][:i])
    r(round(cx), YB + 162, round(len(chip) * 6.4 + 14), 20, fill=SOFT, stroke=AI, sw=1, rx=10)
    t(round(cx + 7), YB + 176, chip, 10.5, 600, AI, mono=True)
assert 60 + sum(len(c) * 6.4 + 22 for c in ["prompt", "tools", "skills", "subagents", "hooks", "MCP", "CLAUDE.md"]) < 538
t(60, YB + 202, "each one set per node by the fields on the right", 10.5, 400, INK2)
t(60, YB + 217, "bash · script · wait: no session; Archon runs them", 10.5, 400, CODE)
# the mapping, two columns
for col in range(2):
    x = 572 + col * 526
    for i, (f, d) in enumerate(CC_ROWS[col * 5:col * 5 + 5]):
        y = YB + 92 + i * 24
        t(x, y, f, 11, 700, INK, mono=True)
        assert len(f) * 6.6 < 168 and 170 + len(d) * 5.4 < 515, (f, d)
        t(x + 170, y, d, 10.5, 400, INK2)
_TOOLS_TXT = ", ".join(k for k, _ in sorted(TOOLS.items(), key=lambda kv: -kv[1]))
_RUNLINE = f"In the course's run: no skills:, agents: or hooks: and no .claude/ folder; the agents called {_TOOLS_TXT}. No Skill, no Task."
assert len(_RUNLINE) * 5.4 < 1040, _RUNLINE
t(572, YB + 222, _RUNLINE, 10.5, 600, PH["plan"])

t(1630, 1046, f"Archon {VERSION} (29 Oct 2026) and its docs at archon.diy · node ids and settings read from the course's "
             "request-to-pr.yaml · analogies ours", 10, 400, INK2, anchor="end")

svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1660 1060" width="1660" height="1060" role="img" aria-labelledby="t1">'
       '<title id="t1">Archon concepts: where things live, how one run flows, who decides what, and what an AI node hands Claude Code</title>\n'
       f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
       f'<path d="M0 0 L10 5 L0 10 z" fill="{INK2}"/></marker></defs>\n'
       '<rect width="1660" height="1060" fill="#FFFFFF"/>\n' + "\n".join(P) + "\n</svg>\n")
write(ROOT / "archon-concepts-map.svg", svg)
