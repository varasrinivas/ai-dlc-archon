"""Build archon-aidlc-on-archon.html: AWS AI-DLC's 33 stages, each drawn as the Archon nodes it becomes, with a scope switch.

Built from AI-DLC's own stage and scope tables (tools/data/aidlc/, via aidlc_map.py), the generated workflow
(tools/make_aidlc_workflow.py) and Archon's real validate and dry-run output (tools/capture_aidlc_map.py ->
tools/data/aidlc/steps.json). Asserts: the workflow validates; for every scope, the stages Archon's dry run ran are
exactly the stages the scope lists, minus the two runtime rules; the express run matches AI-DLC's real express run.

Usage: py -3.12 tools/make_aidlc_workflow.py; py -3.12 tools/capture_aidlc_map.py; py -3.12 tools/build_aidlc_map_page.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aidlc_map import (CODE, DATA, INIT_KIND, NEEDS_CODE, NEEDS_PIPELINE, PHASES, ROLE, SCOPE_ORDER, SCOPES, SLUGS, STAGES, WF_DIR,  # noqa: E402
                       WF_FILE, WF_REL, WORK, key, phase_check, runs)
from cli_parse import workflow_nodes  # noqa: E402
from pagekit import (ARROW_DEF, CLAUDE_MAP, DOC, E, REAL, ROOT, card, claude_facts, gate, io, note, page, phase, plain, rail, scrub, see, step, svg, t, table,  # noqa: E402
                     tabs, write, you)

WF = WF_FILE.read_text(encoding="utf-8")
STATE_TS = (WF_DIR / "scripts" / "state-init.ts").read_text(encoding="utf-8")
STUBS = (DATA / "stubs.yaml").read_text(encoding="utf-8")
NODES = workflow_nodes(WF)
STEPS = {s["label"]: s for s in json.loads((DATA / "steps.json").read_text(encoding="utf-8"))}
BY = {s["slug"]: s for s in STAGES}
GATED = [s for s in SLUGS if s not in INIT_KIND]
PH_COL = dict(zip(PHASES, ["--setup", "--plan", "--build", "--review", "--ship"]))


def x(s):
    return E(s)


# ---------------- facts, checked against Archon's own output ----------------
assert "aidlc-on-archon                          ok" in STEPS["validate"]["stdout"] and STEPS["validate"]["exit"] == 0
TOP = [n for n in NODES if n["parent"] is None]
INNER = [n for n in NODES if n["parent"]]
N_WAIT = sum(1 for n in INNER if n["kind"] == "wait")
assert len(GATED) == 30 and N_WAIT == 30 and sum(1 for n in TOP if n["kind"] == "loop_group") == 30
assert {n["id"] for n in TOP} == set(SLUGS) | {phase_check(p) for p in PHASES[1:]}
N_NODES = len(NODES)
WF_LINES = len(WF.splitlines())
STUBS_INIT_N = int(re.search(r"\((\d+) nodes\)", STEPS["stubs-init"]["stdout"]).group(1))

RUNS = {f"dry-{s}": (s, False, False) for s in SCOPE_ORDER} | {"dry-feature-pipeline": ("feature", False, True), "dry-poc-greenfield": ("poc", True, False)}


def ran(out):
    r = set(re.findall(r"^COMPLETED (\S+) \(loop_group\)", out, re.M))
    return r | {n for n in INIT_KIND if re.search(rf"^(COMPLETED|STUBBED)\s+{n} ", out, re.M)}


RAN = {}
for label, (sc, g, p) in RUNS.items():
    o = STEPS[label]["stdout"]
    assert STEPS[label]["exit"] == 0 and "Simulation outcome: completed" in o, label
    RAN[label] = ran(o)
    assert RAN[label] == set(runs(sc, g, p)), (label, RAN[label] ^ set(runs(sc, g, p)))
    assert all(f"{s}-work" not in o or s in RAN[label] for s in GATED)
SI_OUT = re.search(r"^COMPLETED state-init .*?^  output: (\{.*?\})$", STEPS["dry-express"]["stdout"], re.M | re.S).group(1)
SI = json.loads(SI_OUT)
assert SI["scope"] == "express" and {s for s in GATED if SI[key(s)]} == RAN["dry-express"] - set(INIT_KIND)
EXPRESS = [BY[s]["n"] for s in SLUGS if s in RAN["dry-express"]]
assert EXPRESS == ["0.1", "0.2", "0.3", "2.1", "2.3", "3.5", "3.6"], EXPRESS
assert "verify: passed" in STEPS["dry-express"]["stdout"]  # the real scripts/verify.sh ran inside the dry run
# AI-DLC's own express run (the AI-DLC course, sibling checkout): 0.1-0.3, 2.1, 2.3, 3.5, 3.6 ran; 4.1, 4.3, 4.4 skipped, no pipeline.
SIB = ROOT.parent / "ai-dlc-execution" / "tools" / "build_intro_page.py"
if SIB.exists():
    sib = SIB.read_text(encoding="utf-8")
    assert '(["4.1", "4.3", "4.4"], \'<a href="#s15">15</a>\', "Skipped: the workspace has no pipeline to work on.")' in sib
    for n in ('(["2.1"]', '(["2.3"]', '(["3.5"]', '(["3.6"]'):
        assert n in sib, n
AIDLC_RUN = "../ai-dlc-execution/aidlc-hello-world-java/aidlc-hello-world-java-run.html"

# ---------------- the real express run (tools/capture_aidlc_run.py -> tools/data/aidlc/run/) ----------------
RUNDIR = DATA / "run"
RS = {s["label"]: s for s in json.loads((RUNDIR / "steps.json").read_text(encoding="utf-8"))}
RN = json.loads((RUNDIR / "nodes.json").read_text(encoding="utf-8"))
RLOG = [json.loads(l) for l in (RUNDIR / "log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
REC = {p.relative_to(RUNDIR / "record").as_posix(): p.read_text(encoding="utf-8") for p in sorted((RUNDIR / "record").rglob("*.md"))}
GIT = {p.name: p.read_text(encoding="utf-8") for p in (RUNDIR / "git").iterdir()}
assert all(s["exit"] == 0 for s in RS.values())
RUN_ID = re.search(r"Run id: (\w+)", RS["run"]["stdout"]).group(1)
assert RN["workflow"] == "aidlc-on-archon" and "Status: completed" in RS["get"]["stdout"]
DONE = [n for n in RN["nodes"] if n["event"] == "node_complete"]
COST_RUN = sum(n["cost"] or 0 for n in DONE)
assert abs(COST_RUN - float(re.search(r"Cost: \$([\d.]+)", RS["get"]["stdout"]).group(1))) < 0.01 and f"{COST_RUN:.2f}" == "2.95", COST_RUN
assert RLOG[-1]["type"] == "workflow_complete" and abs(RLOG[-1]["cost_usd"] - COST_RUN) < 0.01


def mins(a, b):
    from datetime import datetime
    f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
    return round((f(b) - f(a)).total_seconds() / 60)


RUN_MIN = mins(RN["start"], RN["end"])
WORK_RUNS = {}
for n in DONE:
    WORK_RUNS.setdefault(n["node"], []).append(n)
REAL_GATED = {n["node"] for n in DONE if n["node"] in GATED}
assert REAL_GATED == RAN["dry-express"] - set(INIT_KIND), REAL_GATED  # the real run ran what the dry run predicted
assert [len(WORK_RUNS[f"{s}-work"]) for s in ("reverse-engineering", "requirements-analysis", "code-generation", "build-and-test")] == [1, 2, 2, 1]
AGENT_MIN = round(sum(n["ms"] for n in DONE if n["node"].endswith(("-work", "-detection")) or n["node"] == "workspace-detection") / 60000)


def gate_msg(label):
    a = json.loads(RS[label]["stdout"])["attention"]
    return a["nodeId"].split(".")[-1], a["message"]


WAITS = {lab: gate_msg(lab) for lab in ("wait-1", "wait-2", "wait-3", "wait-4", "wait-5", "wait-6")}
assert [WAITS[k][0] for k in sorted(WAITS)] == ["reverse-engineering-gate", "requirements-analysis-gate", "requirements-analysis-gate",
                                                "code-generation-gate", "code-generation-gate", "build-and-test-gate"]
assert "PA-10231 = 7, over limit; PA-10244 = 4; PA-10263 = 1" in WAITS["wait-3"][1]
assert all(f in WAITS["wait-4"][1] for f in ("16 tests", "6103fdd", "verify: passed"))
assert all(f in WAITS["wait-5"][1] for f in ("19 tests", "d4a98c9", "verify: passed"))
assert "If any pending row is dated after the server's today, every call returns 400" in WAITS["wait-6"][1]
COMMITS = GIT["branch-log.txt"].split("\n")[:-1]
assert [c[:7] for c in COMMITS] == ["6103fdd", "d4a98c9", "a0f6fa4"] and "d9aa178 priorauth-api 1.0.2" in GIT["main.txt"]
TESTS = re.search(r"(\d+) files? changed, (\d+) insertions\(\+\), (\d+) deletions", GIT["diffstat.txt"]).groups()
J1, J2 = RS["jar-check"]["stdout"], RS["jar-check-2"]["stdout"]
AGES = '"ageBusinessDays":7,"overLimit":true,"ageLabel":"7 bd OVER 5"'
assert AGES in J1 and AGES in J2 and '"ageBusinessDays":4' in J1 and '"ageBusinessDays":1' in J1
FAR = '$ curl -i "http://localhost:8093/requests/pending?asOf=%2B999999999-12-31"'
assert "HTTP/1.1" not in J1.split(FAR)[1] and RS["jar-check"]["seconds"] > 300  # no answer: the request never returned
assert J2.count("HTTP/1.1 400") == 2 and "latest allowed asOf is 2026-11-05" in J2.split(FAR.replace("$ curl -i", "$ curl -i"))[1]
assert "completed after 2 iterations" in RS["approve-code"]["stdout"] and "Workflow completed successfully." in RS["approve-build-and-test"]["stdout"]
assert "(none: no Operation stage ran in this scope)" in RS["approve-build-and-test"]["stdout"]
CTRL, FIXP = GIT["commit-6103fdd.patch"], GIT["commit-a0f6fa4.patch"]
assert "+        pending.stream().map(PriorAuthRequest::receivedAt).max(Comparator.naturalOrder())" in CTRL  # the 3.6 finding, as written in 3.5
assert "-        pending.stream().map(PriorAuthRequest::receivedAt).max(Comparator.naturalOrder())" in FIXP and "max(Comparator.naturalOrder())" not in GIT["diff.patch"]
# The course's request-to-pr run of the same request, for the comparison.
JNODES = json.loads((ROOT / "archon-hello-world-java" / "java-run" / "nodes.json").read_text(encoding="utf-8"))
J_COST = sum(n["cost"] or 0 for v in JNODES.values() if v["workflow"] in ("request-to-pr", "archon-implement") for n in v["nodes"] if n["event"] == "node_complete")
assert f"{J_COST:.2f}" == "4.36", J_COST
# The follow-up fix of 3.6's finding: archon-implement --adopt <the express run>, outside the workflow.
FN = json.loads((RUNDIR / "fix-nodes.json").read_text(encoding="utf-8"))
FIX_COST = sum(n["cost"] or 0 for n in FN["nodes"] if n["event"] == "node_complete")
FO = RS["fix-run"]["stdout"]
assert FN["workflow"] == "archon-implement" and f"{FIX_COST:.2f}" == "0.72" and abs(FIX_COST - float(re.search(r"Cost: \$([\d.]+)", FO).group(1))) < 0.01
assert f"Adopting run {RUN_ID}" in FO and "commit a0f6fa4" in FO and "22 tests run and none failing" in FO and "completed after 1 iteration" in FO
FIX_SUM = json.loads(next(l for l in FO.splitlines() if l.startswith('{"done":true')))["summary"]
VF = RS["verify-fix"]["stdout"]
assert "verify: passed" in VF and sum(int(n) for n in re.findall(r"Tests run: (\d+)", VF)) == 22
J3 = RS["jar-check-3"]["stdout"]
EARLY = '$ curl -i "http://localhost:8093/requests/pending?asOf=2026-10-05"'
assert AGES in J3 and "HTTP/1.1 200" in J3.split(EARLY)[1].split(FAR)[0] and '"ageBusinessDays":0,"overLimit":false,"ageLabel":"0 bd"' in J3
assert "HTTP/1.1 400" in J2.split(EARLY)[1].split(FAR)[0]  # before the fix the same query was refused
assert "latest allowed asOf is 2026-11-05" in J3.split(FAR)[1]


def dry_lines(label, keep=None):
    out = []
    for l in scrub(STEPS[label]["stdout"]).splitlines():
        if re.match(r"^(COMPLETED|STUBBED|SKIPPED|FAILED|PAUSED)\s", l) or l.startswith(("Dry-run:", "Simulation outcome", "  output: verify")):
            out.append(l)
    return "\n".join(out)


# ---------------- the map (inline SVG, theme tokens) ----------------
SHORT = {"aidlc-pipeline-deploy-agent": "release engineer", "aidlc-aws-platform-agent": "cloud engineer", "aidlc-operations-agent": "SRE",
         "aidlc-architect-agent": "architect", "(orchestrator)": "the engine"}
def stage_map():
    W, X0, CW, GAP, Y0, BH, BG = 1132, 10, 214, 10, 64, 50, 8
    parts = [ARROW_DEF]
    for i, ph in enumerate(PHASES):
        cx = X0 + i * (CW + GAP)
        col = PH_COL[ph]
        parts.append(f'<rect x="{cx}" y="10" width="{CW}" height="40" rx="10" style="fill:var({col});fill-opacity:.16;stroke:var({col});stroke-width:1.4"/>')
        parts.append(t(cx + CW / 2, 28, f"{i} {ph}", 13.5, 700, f"var({col})"))
        parts.append(t(cx + CW / 2, 43, "no gates: setup" if i == 0 else f"{sum(1 for s in STAGES if s['phase'] == ph)} stages, a gate after each", 10.5, 400, "var(--ink-3)"))
        if i:
            parts.append(f'<path d="M{cx - GAP + 1} 30 L{cx - 2} 30" style="stroke:var(--ink-3);stroke-width:1.4" marker-end="url(#ah)"/>')
        rows = [s for s in STAGES if s["phase"] == ph]
        for j, s in enumerate(rows):
            y = Y0 + j * (BH + BG)
            kind = INIT_KIND.get(s["slug"])
            label = {"bash": "bash node", "prompt": "agent node", "script": "script node"}[kind] if kind else (
                "agent → verify → gate" if s["slug"] == CODE else "agent → gate")
            role = SHORT.get(s["lead"], ROLE[s["lead"]])
            parts.append(f'<g class="st" data-slug="{s["slug"]}" tabindex="0" role="button" aria-label="{x(s["n"] + " " + s["name"])}">'
                         f'<rect x="{cx}" y="{y}" width="{CW}" height="{BH}" rx="9" style="fill:var({col});fill-opacity:.10;stroke:var({col});stroke-width:1.4"/>'
                         + t(cx + 10, y + 19, s["n"], 11.5, 700, f"var({col})", "start", mono=True)
                         + t(cx + 40, y + 19, s["name"] if len(s["name"]) <= 25 else s["name"][:24] + "…", 11.8, 650, "var(--ink)", "start")
                         + t(cx + 10, y + 38, f"{role} · {label}", 10.2, 400, "var(--ink-3)", "start"))
            if not kind:  # the gate diamond
                gx, gy = cx + CW - 15, y + 15
                parts.append(f'<rect x="{gx - 5}" y="{gy - 5}" width="10" height="10" transform="rotate(45 {gx} {gy})" style="fill:var(--gate)"/>')
            parts.append("</g>")
        if i:
            y = Y0 + len(rows) * (BH + BG) + 4
            dx, dy = cx + 18, y + 12
            parts.append(f'<g class="chk"><rect x="{dx - 7}" y="{dy - 7}" width="14" height="14" transform="rotate(45 {dx} {dy})" style="fill:none;stroke:var({col});stroke-width:1.6"/>'
                         + t(dx + 16, dy + 4, f"{phase_check(ph)} · bash", 10.5, 600, f"var({col})", "start", mono=True) + "</g>")
    H = Y0 + 9 * (BH + BG) + 34
    return svg(W, H, "".join(parts), "AWS AI-DLC's 33 stages as Archon nodes, by phase. Pick a scope to see which stages Archon ran in its dry run.")


SCOPE_BTNS = [(f"dry-{s}", s, f"{len(SCOPES[s])}") for s in SCOPE_ORDER] + [("dry-feature-pipeline", "feature + pipeline", "33"), ("dry-poc-greenfield", "poc, greenfield", "8")]
STAGE_INFO = {}
for s in STAGES:
    slug = s["slug"]
    if slug in INIT_KIND:
        nodes = [(slug, INIT_KIND[slug])]
    else:
        nodes = [(slug, "loop_group"), (f"{slug}-work", "agent prompt")] + ([(f"{slug}-verify", "bash: scripts/verify.sh")] if slug == CODE else []) + [(f"{slug}-gate", "wait, form: approval")]
    STAGE_INFO[slug] = {"n": s["n"], "name": s["name"], "phase": s["phase"], "execution": s["execution"], "lead": ROLE[s["lead"]],
                        "support": [ROLE[a] for a in s["support"]], "mode": s["mode"], "work": WORK[slug], "nodes": nodes,
                        "scopes": [sc for sc in SCOPE_ORDER if slug in SCOPES[sc]],
                        "rule": ("skipped on a greenfield workspace" if slug in NEEDS_CODE else "skipped when the workspace has no pipeline" if slug in NEEDS_PIPELINE else "")}
RAN_JSON = {label: sorted(v) for label, v in RAN.items()}

MAP_CSS = """<style>
.scopes{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 4px}
.scopes button{font:inherit;font-size:.82rem;padding:5px 10px;border-radius:999px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--ink-2);cursor:pointer}
.scopes button small{color:var(--ink-3);margin-left:4px}
.scopes button[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.scopes button[aria-pressed="true"] small{color:var(--bg)}
.mapcount{font-size:.92rem;color:var(--ink-2);margin:6px 0 0}
.mapwrap{overflow-x:auto;max-width:100%}.mapwrap figure.dia{min-width:820px;margin:8px 0 0}
g.st{cursor:pointer;transition:opacity .2s}g.st.off{opacity:.22}g.st.on rect:first-child{stroke-width:2.6}
g.st:focus{outline:none}g.st:focus rect:first-child,g.st.sel rect:first-child{stroke:var(--ink)!important;stroke-width:2.6}
.sdet{margin-top:12px;border:1px solid var(--line-2);border-radius:12px;padding:12px 14px;background:var(--bg-2);font-size:.92rem}
.sdet h4{margin:0 0 6px;font-size:1rem}.sdet dl{display:grid;grid-template-columns:150px minmax(0,1fr);gap:4px 12px;margin:0}
.sdet dt{color:var(--ink-3)}.sdet dd{margin:0}
@media (max-width:640px){.sdet dl{grid-template-columns:minmax(0,1fr)}}
</style>"""
MAP_JS = """<script>
(function(){
  var RAN=__RAN__, INFO=__INFO__, LAB=__LAB__;
  var gs=[].slice.call(document.querySelectorAll('g.st')), btns=[].slice.call(document.querySelectorAll('.scopes button'));
  var count=document.getElementById('mapCount'), det=document.getElementById('stageDet');
  function pick(label){
    var on=RAN[label]; btns.forEach(function(b){b.setAttribute('aria-pressed', b.dataset.run===label?'true':'false');});
    gs.forEach(function(g){var r=on.indexOf(g.dataset.slug)>=0; g.classList.toggle('on',r); g.classList.toggle('off',!r);});
    count.innerHTML='<b>'+LAB[label][0]+'</b>: Archon ran <b>'+on.length+'</b> of 33 stages in its dry run'+LAB[label][1];
  }
  function show(slug){
    var s=INFO[slug]; gs.forEach(function(g){g.classList.toggle('sel', g.dataset.slug===slug);});
    var nodes=s.nodes.map(function(n){return '<code>'+n[0]+'</code> ('+n[1]+')';}).join(' → ');
    det.innerHTML='<h4>'+s.n+' '+s.name+' <span style="color:var(--ink-3);font-weight:400">· '+s.phase+'</span></h4><dl>'
      +'<dt>Produces</dt><dd>'+s.work+'</dd>'
      +'<dt>AI-DLC</dt><dd>'+s.execution.toLowerCase()+'; led by the '+s.lead+(s.support.length?'; support: '+s.support.join(', '):'')+'; mode '+s.mode+'</dd>'
      +'<dt>Archon nodes</dt><dd>'+nodes+'</dd>'
      +'<dt>Runs in scopes</dt><dd>'+(s.scopes.length===11?'all 11':s.scopes.join(', ')||'none')+(s.rule?' · '+s.rule:'')+'</dd></dl>';
  }
  btns.forEach(function(b){b.addEventListener('click',function(){pick(b.dataset.run);});});
  gs.forEach(function(g){g.addEventListener('click',function(){show(g.dataset.slug);});
    g.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();show(g.dataset.slug);}});});
  pick('dry-express'); show('requirements-analysis');
})();
</script>
"""
def lab_note(label):
    sc = RUNS[label][0]
    miss = SCOPES[sc] - RAN[label]
    assert miss <= NEEDS_PIPELINE | NEEDS_CODE
    if not miss:
        return ": all of AI-DLC's list"
    why = ([f"{len(miss & NEEDS_PIPELINE)} Operation stage{'s' if len(miss & NEEDS_PIPELINE) > 1 else ''} (no pipeline)"] if miss & NEEDS_PIPELINE else []) \
        + (["2.1 Reverse Engineering (no code)"] if miss & NEEDS_CODE else [])
    return f". AI-DLC's list has {len(SCOPES[sc])}; skipped here: {' and '.join(why)}"


LAB = {label: (name, lab_note(label)) for label, name, _ in SCOPE_BTNS}
MAP_JS = MAP_JS.replace("__RAN__", json.dumps(RAN_JSON)).replace("__INFO__", json.dumps(STAGE_INFO)).replace("__LAB__", json.dumps(LAB))


# ---------------- small figures ----------------
def chain(boxes, title, loop_label, w=820):
    """boxes: [(id, sub, colour token, dashed)] in one loop_group, with the reject arrow back to the first."""
    n = len(boxes)
    BW, BH, G = 236, 50, 36
    x0 = (w - (n * BW + (n - 1) * G)) / 2
    parts = [ARROW_DEF, f'<rect x="{x0 - 22}" y="14" width="{n * BW + (n - 1) * G + 44}" height="150" rx="14" style="fill:var(--build);fill-opacity:.05;stroke:var(--build);stroke-width:1.4"/>',
             t(x0 - 10, 34, loop_label, 12, 700, "var(--build)", "start", mono=True)]
    for i, (nid, sub, col, dash) in enumerate(boxes):
        bx = x0 + i * (BW + G)
        d = ";stroke-dasharray:5 4" if dash else ""
        parts.append(f'<rect x="{bx}" y="56" width="{BW}" height="{BH}" rx="9" style="fill:var({col});fill-opacity:.13;stroke:var({col});stroke-width:1.6{d}"/>')
        parts.append(t(bx + BW / 2, 77, nid, 12.5, 700, mono=True))
        parts.append(t(bx + BW / 2, 94, sub, 10.5, 400, "var(--ink-3)"))
        if i:
            parts.append(f'<path d="M{bx - G + 2} 81 L{bx - 4} 81" style="stroke:var(--ink-3);stroke-width:1.5" marker-end="url(#ah)"/>')
    lx, fx = x0 + (n - 1) * (BW + G) + BW / 2, x0 + BW / 2
    parts.append(f'<path d="M{lx} 106 C{lx} 150, {fx} 150, {fx} 109" style="fill:none;stroke:var(--gate);stroke-width:1.5;stroke-dasharray:4 4" marker-end="url(#ah)"/>')
    parts.append(t((lx + fx) / 2, 152, "reject + what to change → the stage is redone (up to 3 times)", 11, 600, "var(--gate)"))
    parts.append(f'<path d="M{lx + BW / 2} 81 L{lx + BW / 2 + 30} 81" style="stroke:var(--ok);stroke-width:1.5" marker-end="url(#ah)"/>')
    parts.append(t(lx + BW / 2 + 34, 85, "approve", 11, 600, "var(--ok)", "start"))
    return svg(w + 60, 176, "".join(parts), title)


def init_flow():
    W = 900
    items = [("workspace-scaffold", "0.1 · bash", "--ship"), ("workspace-detection", "0.2 · agent: code? pipeline?", "--plan"),
             ("state-init", "0.3 · script: scope → 30 × true/false", "--ship")]
    parts, BW, G, x0 = [ARROW_DEF], 230, 34, 20
    for i, (nid, sub, col) in enumerate(items):
        bx = x0 + i * (BW + G)
        parts.append(f'<rect x="{bx}" y="20" width="{BW}" height="54" rx="9" style="fill:var({col});fill-opacity:.13;stroke:var({col});stroke-width:1.6"/>')
        parts.append(t(bx + BW / 2, 43, nid, 12.5, 700, mono=True))
        parts.append(t(bx + BW / 2, 61, sub, 10.5, 400, "var(--ink-3)"))
        if i:
            parts.append(f'<path d="M{bx - G + 2} 47 L{bx - 4} 47" style="stroke:var(--ink-3);stroke-width:1.5" marker-end="url(#ah)"/>')
    sx = x0 + 2 * (BW + G) + BW / 2
    for k, lab in enumerate(["when: \"$state-init.output.requirements_analysis == true\"", "when: \"$state-init.output.user_stories == true\"", "… one when: on each of the 30 stages"]):
        y = 112 + k * 26
        parts.append(f'<path d="M{sx} 74 L{sx} {y - 6} L{sx - 22} {y - 6}" style="fill:none;stroke:var(--ink-3);stroke-width:1.2" marker-end="url(#ah)"/>' if k == 0 else "")
        parts.append(t(sx - 30, y - 2, lab, 11, 400, "var(--ink-2)", "end", mono=True))
    parts.append(t(x0, 112 + 3 * 26 + 4, "--input scope=express   (default)", 11.5, 600, "var(--gate)", "start", mono=True))
    return svg(W, 112 + 3 * 26 + 18, "".join(parts), "Initialization: the scope and what detection found become one true/false per stage")


def yaml_block(slug):
    a = WF.index(f"  - id: {slug}\n")
    b = WF.index("\n\n", a)
    return WF[a:b]


# ---------------- steps ----------------
S = []
S.append(step(1, "The idea", "--setup", "why", "Two tools, one lifecycle",
              "AI-DLC says which stages a piece of work goes through. Archon runs a process written as a graph. Put together: AI-DLC's stages, run by Archon.", "read · 2 min", f"""
<p><b>AWS AI-DLC</b> (the AI-Driven Development Lifecycle, run with AI-DLC Workflows {x('2.11')}) splits work into <b>33 stages</b> in five phases: set up, think about the idea (Ideation), decide exactly what to build (Inception), build it (Construction), run it (Operation). An AI <b>persona</b> leads each stage (product manager, architect, developer, QA lead …), a person approves each stage at a <b>gate</b>, and a <b>scope</b> decides how many stages run, from 8 for a proof of concept to all 33 for a feature.</p>
<p><b>Archon</b> runs any process you write as a graph of nodes, with a pause wherever a person decides. This page writes AI-DLC's lifecycle as one Archon workflow, <code>aidlc-on-archon</code>, and checks it with Archon: it validates, and in {len(RUNS)} dry runs Archon ran exactly the stages each AI-DLC scope lists.</p>
{plain("AI-DLC is the recipe book: which courses a meal has and who signs off each one. Archon is the kitchen's ticket rail: it calls the next course, holds it until the chef says yes, and keeps the tickets. This page puts the recipe book on the rail.")}
{note(f'New to AI-DLC? The <a href="../ai-dlc-execution/aidlc-introduction.html">AI-DLC course</a> runs the real engine. New to Archon? Start with the <a href="archon-introduction.html">introduction</a>.')}
"""))

TR = [
    ["A <b>stage</b> (e.g. 2.3 Requirements Analysis)", "a <code>loop_group</code> holding an <b>agent node</b> whose prompt names the stage, its lead persona and its output file", "<code>requirements-analysis</code> → <code>requirements-analysis-work</code>"],
    ["The <b>gate</b> after every stage", "a <code>wait:</code> node with <code>form: approval</code> inside the loop; reject (with what to change) redoes the stage, approve moves on", "<code>requirements-analysis-gate</code>"],
    ["The <b>lead persona</b> and its support", "the prompt: \u201cYou lead it as the team's product manager; weigh what a … would say\u201d", "one prompt per stage, from AI-DLC's stage table"],
    ["<b>ALWAYS / CONDITIONAL</b> and the <b>scope</b>", "<code>--input scope=…</code>, a script node that turns it into one true/false per stage, and a <code>when:</code> on every stage", "<code>state-init</code> + <code>when: \"$state-init.output.user_stories == true\"</code>"],
    ["Workspace detection (greenfield? a pipeline?)", "an agent node with <code>output_format</code>: its true/false answers feed the same script", "<code>workspace-detection</code>"],
    ["3.5 Code Generation (a separate subagent)", "an agent node with <code>context: fresh</code>, then a <b>bash</b> node that runs the team's <code>scripts/verify.sh</code>, then the gate", "<code>code-generation-work</code> → <code>-verify</code> → <code>-gate</code>"],
    ["The <b>phase check</b>", "a bash node after each phase that lists what the phase wrote", "<code>inception-check</code>"],
    ["The <b>record</b> (<code>aidlc-docs/</code>)", "the run's artifacts: <code>$ARTIFACTS_DIR/record/&lt;phase&gt;/&lt;stage&gt;.md</code>", "<code>record/inception/requirements-analysis.md</code>"],
]
S.append(step(2, "The idea", "--setup", "the translation", "How each AI-DLC part becomes Archon",
              "Eight things AI-DLC has, and the Archon feature that does the same job.", "read · 3 min",
              table(["AI-DLC", "In Archon", "In the workflow"], TR)
              + note("Each agent node then runs as one Claude Code session: the persona is words in its prompt, not a Claude subagent, and a <i>subagent</i> stage becomes <code>context: fresh</code>, a session of its own. The whole chain, and what the real run's sessions did: <a href='#claude'>What each AI node handed Claude Code</a>.")
              + plain("Every stage has the same shape in Archon: <b>an agent writes, a person approves</b>. The only exceptions are the three setup stages, which have no gate in AI-DLC either, and Code Generation, which runs the tests between the two.")))

S.append(step(3, "The map", "--plan", "every stage", "The 33 stages, as Archon nodes",
              "Pick a scope to see which stages Archon ran. Click a stage for its AI-DLC details and the Archon nodes it became.", "explore", f"""
{MAP_CSS}
<div class="scopes" role="group" aria-label="Scope">{''.join(f'<button type="button" data-run="{lab}" aria-pressed="false">{x(name)}<small>{cnt}</small></button>' for lab, name, cnt in SCOPE_BTNS)}</div>
<p class="mapcount" id="mapCount"></p>
<div class="mapwrap">{stage_map()}</div>
<p class="mapcount" style="font-size:.84rem;color:var(--ink-3)"><span style="color:var(--gate)">◆</span> a gate: an approval wait after the stage &nbsp;·&nbsp; ◇ a phase check: a bash node &nbsp;·&nbsp; each box: the stage number and name, its lead persona, and the Archon nodes it became</p>
<div class="sdet" id="stageDet" aria-live="polite"></div>
{note(f"The number on each scope is how many stages AI-DLC's scope list has. Each highlight is the set of stages Archon's real dry run of <code>aidlc-on-archon</code> ran for that scope ({REAL}), in this course's workspace: code but no CI pipeline, so the Operation stages are skipped as AI-DLC skips them. <b>feature + pipeline</b> is the same dry run with detection saying a pipeline exists (all 33); <b>poc, greenfield</b> says there is no code, so 2.1 Reverse Engineering drops out.")}
"""))

RA = BY["requirements-analysis"]
S.append(step(4, "The map", "--plan", "one stage", "One stage up close: 2.3 Requirements Analysis",
              "Every gated stage is this loop. Code Generation adds the team's check between the agent and the gate.", "read · 3 min",
              chain([("requirements-analysis-work", f"agent · the {ROLE[RA['lead']]}", "--plan", False), ("requirements-analysis-gate", "wait · approval · a person", "--gate", True)],
                    "2.3 as Archon nodes: the agent writes, a person approves or sends it back", "requirements-analysis · loop_group")
              + chain([("code-generation-work", "agent · developer · fresh context", "--plan", False), ("code-generation-verify", "bash · scripts/verify.sh", "--ship", False),
                       ("code-generation-gate", "wait · approval · a person", "--gate", True)], "3.5 Code Generation: the tests run before anyone is asked", "code-generation · loop_group")
              + tabs("st", [("2.3 in the YAML", WF_REL, "generated · validated", "yaml", yaml_block("requirements-analysis")),
                            ("3.5 in the YAML", WF_REL, "generated · validated", "yaml", yaml_block(CODE))])
              + note("<code>$LOOP_PREV.requirements-analysis-gate.output.text</code> is what the person typed with their reject, so the second pass knows what to change. <code>until_bash</code> ends the loop once the gate's decision is <code>approve</code>.")))

S.append(step(5, "The map", "--plan", "the scope", "How the scope picks the stages",
              "AI-DLC's engine decides which stages run. In Archon, three setup nodes decide it once, and every stage reads the answer.", "read · 3 min",
              init_flow()
              + io(you("archon workflow run aidlc-on-archon --dry-run --exec-code --stubs stubs.yaml --default-stubs --input scope=express \"Implement the request in docs-in/request.md\"", None, "any shell"),
                   see(x("COMPLETED state-init (script) — executed locally\n  output: " + SI_OUT
                         + "\n" + "\n".join(l for l in dry_lines("dry-express").splitlines() if l.startswith(("SKIPPED   intent", "SKIPPED   market", "COMPLETED ideation"))) + "\n…"),
                       "real · the express dry run", "Archon returns"))
              + f"<p>The script's answer for express: true for {', '.join(BY[s]['n'] + ' ' + BY[s]['name'] for s in GATED if SI[key(s)])}; false for the other {sum(1 for s in GATED if not SI[key(s)])}. Every stage's <code>when:</code> reads its own entry.</p>"
              + plain("The scope lists are AI-DLC's own, copied into the script. On top of them the workflow adds two rules AI-DLC's engine applies at run time: no code means no Reverse Engineering, and no pipeline means no Operation stages.")
              + tabs("si", [("state-init.ts", ".archon/workflows/aidlc/aidlc-on-archon/scripts/state-init.ts", "generated · ran in every dry run", "javascript", STATE_TS)])))

DRY_ROWS = []
for lab, name, cnt in SCOPE_BTNS:
    sc, g, p = RUNS[lab]
    nums = [BY[s]["n"] for s in SLUGS if s in RAN[lab] and s not in INIT_KIND]
    DRY_ROWS.append([f"<code>{x(name)}</code>", cnt, f"<b>{len(RAN[lab])}</b>", " ".join(nums) if len(nums) < 12 else f"{len(nums)} gated stages", "✓"])
S.append(step(6, "The check", "--build", "real dry runs", "Thirteen dry runs, all matching",
              "No model was called: the agent nodes and the gates were stubbed. The bash nodes and the scope script really ran, and so did the project's tests.", "read · 3 min",
              io(you("archon validate workflows aidlc-on-archon", None, "from the workspace root"), see(x(scrub(STEPS["validate"]["stdout"]).strip()), "real", "Archon returns"))
              + table(["Scope", "AI-DLC's list", "Archon ran", "Gated stages that ran", "Same as the list, after the two rules"], DRY_ROWS)
              + io(you(f"archon workflow run aidlc-on-archon --dry-run --exec-code --stubs stubs.yaml --default-stubs --input scope=express \"Implement the request in docs-in/request.md\"", None, "any shell"),
                   see(x(dry_lines("dry-express")), "real · express, every node", "Archon returns"))
              + plain(f'Express ran 0.1–0.3, 2.1, 2.3, 3.5 and 3.6 and skipped Operation: the same stages AI-DLC\'s engine ran for the same request in the <a href="{AIDLC_RUN}">AI-DLC course\'s express run</a>, where 4.1, 4.3 and 4.4 were skipped because the workspace has no pipeline.')
              + note("<code>--exec-code</code> runs the bash and script nodes for real; <code>--stubs</code> gives the agent nodes and the gates fixed answers (here: detection's facts, and every gate approved). A dry run doesn't run <code>until_bash</code>, so each loop is taken once. Stubs: <code>tools/data/aidlc/stubs.yaml</code>.")))

S.append(step(7, "The check", "--build", "honest limits", "What's the same, and what isn't",
              "The workflow runs AI-DLC's stages and gates. It is not AI-DLC's engine.", "read · 2 min",
              table(["", "AI-DLC's engine", "aidlc-on-archon"], [
                  ["Stages, phases, gates", "33, 5, a gate after each stage after setup", "the same 33, 5 and 30 gates"],
                  ["Which stages run", "decided by the engine from the scope, and re-planned as it goes", "fixed when the run starts: the scope list and two rules"],
                  ["Personas", "14 agent files with full instructions; support agents and two senior reviewers join in bigger scopes", "a role named in each stage's prompt; one agent per stage"],
                  ["Mob mode (2.4 User Stories)", "several personas work on one draft", "one agent asked to weigh their views (could be parallel nodes and a merge node)"],
                  ["The record", "<code>aidlc-docs/</code>, an audit log, a state file the next session reads", "the run's artifacts, transcript and cost in <code>~/.archon</code>"],
                  ["Pausing and resuming", "the session stops at a gate; you answer in Claude Code", "a durable wait: answer later with <code>archon workflow approve</code>, the Web UI or chat"],
                  ["Run with a model", "yes, in the AI-DLC course", f"yes: one express run, <a href=\"#s08\">step 8</a>"]], "kv")
              + note("Use AI-DLC when you want its full method and record. Use this workflow when your team already runs Archon and wants AI-DLC's stages and sign-offs in it, or wants to cut the lifecycle down to the stages it actually uses.")))

def reply(label):
    """The recorded `archon workflow approve|reject <run> <text>` as typed, the text quoted."""
    verb, rid, text = re.match(r"archon workflow (approve|reject) (\w+) (.*)", RS[label]["cmd"], re.S).groups()
    return f'archon workflow {verb} {rid} "{text}"'


def stage_cost(slug):
    ns = WORK_RUNS.get(f"{slug}-work") or WORK_RUNS.get(slug) or []
    return sum(n["cost"] or 0 for n in ns), round(sum(n["ms"] for n in ns) / 60000, 1)


def gate_text(label, keep):
    """The first `keep` lines of a gate's message (what the person reads), and a pointer to the rest."""
    lines = WAITS[label][1].split("\n")
    return x("\n".join(lines[:keep]) + ("\n…" if len(lines) > keep else ""))


TL = [  # stage, pass, what the agent produced, what the person did
    ("0.1–0.3 Initialization", "", f"Detection: code in <code>priorauth-api</code>, no CI pipeline. The script turned on 2.1, 2.3, 3.5, 3.6 and nothing else; the other {30 - len(REAL_GATED)} stages were skipped by their <code>when:</code>.", "no gate", "workspace-detection"),
    ("2.1 Reverse Engineering", "1", "A map of the repo (one endpoint, 3 tests, no date code) and 7 open questions: holidays, counting, the over-5 line, time zone, tenants, field names, version.", "<b>approve</b>: the questions go to requirements", "reverse-engineering"),
    ("2.3 Requirements Analysis", "1", "12 requirements, and the same 7 questions at the top.", "<b>reject</b> with Ravi's and Meena's answers and the screen team's field names", "requirements-analysis"),
    ("", "2", "No open questions. As of 13 Oct the sample gives 7 (over 5), 4, 1. Eight assumptions (A1–A8) the answers didn't cover.", "<b>approve</b>", None),
    ("3.5 Code Generation", "1", f"Branch <code>request-age/pending-list-age</code>, commit <code>6103fdd</code>; <code>verify.sh</code> passed, 16 tests (3 before).", "Kiran's jar check: the far-future <code>asOf</code> never answers → <b>reject</b>", "code-generation"),
    ("", "2", "Commit <code>d4a98c9</code>: an <code>asOf</code> after today is a 400; 19 tests; <code>verify.sh</code> passed.", "the jar check again: 7/4/1, both bad dates 400 → <b>approve</b>", None),
    ("3.6 Build and Test", "1", "Everything passes on the real jar too, and a requirement-to-test map. But reading the code it found that one pending row dated after today makes <b>every</b> call a 400.", "<b>approve</b> for the record, not for release; the fix is a follow-up", "build-and-test"),
    ("4 Operation", "", "Skipped: no pipeline, as in the dry run.", "no gate", None),
]
TL_ROWS = []
for stage, ps, did, person, slug in TL:
    c, m = stage_cost(slug) if slug else (None, None)
    TL_ROWS.append([f"<b>{stage}</b>" if stage else "", ps, did, person, f"${c:.2f} · {m} min" if slug else ""])

S.append(step(8, "The real run", "--review", "a model run", "A real express run, gate by gate",
              f"The same request as the rest of the course, run with Claude Code on the claude.ai login: {len(REAL_GATED)} stages, 6 gate answers, 2 of them rejects, {RUN_MIN} minutes, ${COST_RUN:.2f} reported.", f"read · 6 min · {REAL}",
              f"<p>Before the run the workspace got a fresh clone of the public starter (priorauth-api 1.0.2, 3 tests, no tags), as in the course's own run: the java workspace in the course files already has the feature merged. Every command below went through <code>tools/archon_step.py</code>, which removes the API key, so the run used the claude.ai login. The answers at the gates are the ones Ravi and Meena gave in the <a href=\"archon-hello-world-java/archon-hello-world-java-run.html\">request-to-pr run</a>, so the two runs can be compared.</p>"
              + io(you('archon workflow run aidlc-on-archon --folder --detach --input scope=express "Implement the request in docs-in/request.md"', None, "from the workspace root"),
                   see(x(scrub(RS["run"]["stdout"]).strip()), "real", "Archon returns"))
              + table(["Stage", "Pass", "What the agent produced", "At the gate", "Agent cost · time, all passes"], TL_ROWS)
              + f'<h3 style="margin:22px 0 8px">2.3, first pass: the questions, answered by a reject</h3>'
              + io(see(gate_text("wait-2", 12), "real · archon workflow wait --json, the message", "The gate shows"),
                   you(x(reply("reject-requirements")), None, "Meena types"), stack=True)
              + gate("Approved on the second pass", x(WAITS["wait-3"][1].split("\n\n")[1][:400]) + " …", "approve-requirements: " + x(reply("approve-requirements").split('"')[1]))
              + f'<h3 style="margin:22px 0 8px">3.5, first pass: the tests pass, the jar doesn\'t</h3>'
              + io(see(gate_text("wait-4", 3), "real · the gate's first lines", "The gate shows"),
                   you(x(RS["jar-check"]["cmd"]), None, "Git Bash, from the workspace root"),
                   see(x(J1.strip()) + "\n<b>(no answer: the request never returned; the check was stopped after 5 minutes)</b>", "real · Kiran's jar check, port 8093", "Kiran sees"), stack=True)
              + plain("The tests passed and the agent said so, adding that it had not started the app. Started for real, the app counted business days one day at a time towards the year 999,999,999 and never answered. One such request ties up the server. Only a person trying the jar found it.")
              + io(you(x(reply("reject-code")), None, "Meena types"),
                   see(gate_text("wait-5", 4), "real · the redo, same branch, a new commit", "The gate shows"), stack=True)
              + io(see(x(J2.strip()), "real · the jar check on d4a98c9", "Kiran sees"))
              + f'<h3 style="margin:22px 0 8px">3.6: a defect found by reading the code</h3>'
              + io(see(x(WAITS["wait-6"][1].split("**Decisions for you")[1].split("\n2.")[0].strip()), "real · 3.6's first decision", "The gate shows"),
                   you(x(reply("approve-build-and-test")), None, "Meena types"), stack=True)
              + note("Checked: in the controller, with no <code>asOf</code> the date is today, and if the newest row's <code>receivedAt</code> is after it the whole call is a 400. It follows from assumption A3 (“if asOf is earlier than even one row, the whole call is a 400”), which was approved at 2.3. The sample data can't trigger it with no <code>asOf</code>. It could not be fixed inside this run: rejecting 3.6 would only redo 3.6, which may not change code. The fix is step 9.")
              + io(see(x(scrub(RS["approve-build-and-test"]["stdout"]).strip().split("Loop-group node 'build-and-test'")[1].strip().join(["Loop-group node 'build-and-test'", ""])), "real · the end of the run", "Archon returns"))
              + tabs("rr", [(f"{k.split('/')[-1]}", f"$ARTIFACTS_DIR/record/{k}", "real · written by the run", "markdown", v) for k, v in REC.items() if k != "workspace.md"])))

FIX_MSG = re.match(r"archon workflow run archon-implement --adopt (\w+) (.*)", RS["fix-run"]["cmd"], re.S).groups()
FIX_OUT = "\n".join(l for l in scrub(FO).splitlines() if l.startswith(("Adopting run", "Folder project", "Loop node", "Workflow finished", "  Status", "  Cost")))
S.append(step(9, "The real run", "--review", "the follow-up fix", "The follow-up fix, outside the workflow",
              f"3.6's finding had no way back to 3.5, so it went to a second run: Archon's bundled <code>archon-implement</code>, adopting the express run, as the request-to-pr run fixed its 500. One iteration, ${FIX_COST:.2f}.", f"read · 3 min · {REAL}",
              io(you(x(f'archon workflow run archon-implement --adopt {FIX_MSG[0]} "{FIX_MSG[1]}"'), None, "from the workspace root, Meena's decision as the message"),
                 see(x(FIX_OUT + "\n\nThe agent's summary:\n" + FIX_SUM), "real", "Archon returns"), stack=True)
              + io(you('./scripts/verify.sh > /dev/null 2>&1 && echo "verify: passed"\ngit -C priorauth-api log --oneline -4\ngrep -h "Tests run" priorauth-api/target/surefire-reports/*.txt', None, "Git Bash, Kiran checks"),
                   see(x(VF.strip()), "real", "Kiran sees"))
              + io(see(x(J3.strip()), "real · the jar check on a0f6fa4", "Kiran sees"))
              + plain("Asked for 5 October, before two of the requests arrived, the API used to refuse the whole list with a 400 (step 8's checks). Now it answers, and those two rows are 0 days old. That is the same code path as a row received after today with no <code>asOf</code>, which the new test pins with a fixed clock. The far-future date is still a 400, and 7/4/1 still holds.")
              + note("The agent said the 3.6 record \u201cisn't in this workspace\u201d: an adopted run's files are in <code>$ADOPTED_RUN_DIR</code> (<code>~/.archon/workspaces/_folder/aidlc-workspace/artifacts/runs/&lt;id&gt;/</code>), not in the workspace, so it worked from the message alone. Put the decision in the message, as here.")
              + tabs("fx", [("the fix", "priorauth-api: commit a0f6fa4", "real", "diff", GIT["commit-a0f6fa4.patch"]),
                            ("the whole branch", f"priorauth-api: main..request-age/pending-list-age ({TESTS[0]} files, +{TESTS[1]} −{TESTS[2]})", f"real · {len(COMMITS)} commits", "diff", GIT["diff.patch"])])))

CMP = [
    ["The process", "request-to-pr: questions, requirements, plan, implement loop, review, push (15 nodes, 4 waits)", f"AI-DLC express: 2.1, 2.3, 3.5, 3.6, each an agent and a gate ({len(REAL_GATED)} gates reached)"],
    ["Questions to the team", "a questions node, answered with <code>archon workflow answer</code>", "at the top of the stage's file, answered by rejecting the stage"],
    ["Ages as of 13 Oct", "7 OVER 5 / 4 / 1", "7 OVER 5 / 4 / 1"],
    ["Far-future <code>asOf</code>", "a 500, found by Kiran's jar check", "no answer at all (a day-by-day loop), found by the same check"],
    ["Sending the change back", "reject cancelled the run; <code>archon-implement --adopt</code> fixed it in a second run", "reject redid 3.5 in the same run; 3.6's finding went to a second run, <code>archon-implement --adopt</code>"],
    ["Tests at the end", "21", "19, then 22 after the fix"],
    ["Found beyond the jar check", "nothing more: the review said READY", "3.6 read the code: a row dated after today blocks the whole list; fixed in a follow-up run"],
    ["Reported cost", f"${J_COST:.2f} (run + fix)", f"${COST_RUN + FIX_COST:.2f} (${COST_RUN:.2f} run + ${FIX_COST:.2f} fix)"],
]
S.append(step(10, "The real run", "--review", "what it showed", "What the real run showed",
              "The workflow does what the map says. A person still had to find the worst bug, and one finding had to leave the workflow to be fixed.", "read · 3 min",
              table(["", "This course's request-to-pr run (4 Nov)", "aidlc-on-archon, express (5 Nov)"], CMP)
              + f"""<ul>
<li><b>The map held.</b> Archon ran exactly the stages the express dry run ran (2.1, 2.3, 3.5, 3.6), skipped the other {30 - len(REAL_GATED)} by their <code>when:</code>, and the phase checks listed what each phase wrote.</li>
<li><b>Reject works as AI-DLC's gate.</b> Both rejects redid only their own stage, and the redo read what the person typed (<code>$LOOP_PREV</code>): the requirements took the answers, the code took Meena's 400 rule.</li>
<li><b>Green tests weren't enough.</b> <code>verify.sh</code> passed at 16 tests while one request could hang the server. Kiran's jar check, a person at the gate, caught it, as in the request-to-pr run.</li>
<li><b>A gate can only send back its own stage.</b> 3.6 found a code defect, but its reject redoes 3.6, which is told not to change code: the workflow has no way from 3.6's gate back to 3.5. The fix went to a follow-up run, <code>archon-implement --adopt</code>, as in the request-to-pr run (step 9).</li>
<li><b>Approved assumptions matter.</b> The 3.6 defect came from assumption A3, which was approved at 2.3 with “A1–A8 are fine”.</li>
</ul>"""
              + plain(f"The stages ran in order, a person signed each one off, two were sent back and redone, and the run cost ${COST_RUN:.2f} in about {RUN_MIN} minutes; fixing 3.6's finding took one more run and ${FIX_COST:.2f}. The agents wrote good code and good reports, and still missed what a person found by trying the app.")
              + note(f"Agent time across the run: about {AGENT_MIN} minutes; the rest was waiting at gates. Costs are what Archon reports (API-price equivalents); the run used a claude.ai plan. Run id <code>{RUN_ID}</code>. Captured by <code>tools/capture_aidlc_run.py</code> into <code>tools/data/aidlc/run/</code>.")))

TRY_WIN = ("cd C:\\work\\archon-java\\java-workspace\n"
           "Copy-Item -Recurse <course>\\tools\\data\\aidlc\\files\\.archon\\workflows\\aidlc .archon\\workflows\\\n"
           "archon validate workflows aidlc-on-archon\n"
           "archon workflow run aidlc-on-archon --dry-run --default-stubs --input scope=express \"Implement the request in docs-in/request.md\"")
TRY_MAC = ("cd ~/work/archon-java/java-workspace\n"
           "cp -R <course>/tools/data/aidlc/files/.archon/workflows/aidlc .archon/workflows/\n"
           "archon validate workflows aidlc-on-archon\n"
           "archon workflow run aidlc-on-archon --dry-run --default-stubs --input scope=express \"Implement the request in docs-in/request.md\"")
S.append(step(11, "Try it", "--ship", "your workspace", "Run it in your workspace",
              "Copy one folder into the workspace from the setup page, check it, then run it for real.", "about 5 minutes, then a real run",
              io(you(TRY_WIN, TRY_MAC, "PowerShell", "Terminal"), see("aidlc-on-archon                          ok\n…\nSimulation outcome: paused", "what to expect · real output above", "Archon returns"))
              + f'<h3 style="margin:20px 0 8px">A real run: the commands of <a href="#s08">step 8</a></h3>'
              + io(you("archon workflow run aidlc-on-archon --folder --detach --input scope=express \"Implement the request in docs-in/request.md\"\narchon workflow attention\narchon workflow approve <run-id> \"OK\"\narchon workflow reject <run-id> \"Name the fields ageBusinessDays and overLimit\"", None, "any shell"))
              + note("Without stubs, a dry run stops at the first gate. A real express run asks at four gates (2.1, 2.3, 3.5, 3.6; step 8 needed six answers), each answered with <code>approve</code> or <code>reject</code> plus what to change; Code Generation makes the branch and commits in <code>priorauth-api/</code> as the workspace's <code>CLAUDE.md</code> says. The workflow names <code>&lt;course&gt;</code> for wherever you cloned this course.")))

S.append(step(12, "Try it", "--ship", "the files", "The files",
              f"The workflow is generated from AI-DLC's stage table by <code>tools/make_aidlc_workflow.py</code>: {WF_LINES} lines, {N_NODES} nodes ({len(TOP)} at the top level, {len(INNER)} inside the loops).", "reference",
              tabs("wf", [("aidlc-on-archon.yaml", WF_REL, "generated · validated", "yaml", WF),
                          ("state-init.ts", ".archon/workflows/aidlc/aidlc-on-archon/scripts/state-init.ts", "generated", "javascript", STATE_TS),
                          ("stubs.yaml", "tools/data/aidlc/stubs.yaml", "the dry runs' stubs", "yaml", STUBS)])
              + table(["Stage", "Phase", "AI-DLC", "Lead", "Archon nodes"],
                      [[f"{s['n']} {x(s['name'])}", s["phase"], s["execution"].lower() + " · " + s["mode"], ROLE[s["lead"]],
                        " → ".join(f"<code>{n}</code>" for n, _ in STAGE_INFO[s["slug"]]["nodes"][1:]) or f"<code>{s['slug']}</code> ({INIT_KIND[s['slug']]})"] for s in STAGES])))

# ---------------- what each AI node handed Claude Code ----------------
# The shared mapping (asserted against tools/data/docs/), AI-DLC's execution modes as node fields, and, from the real
# run's two transcripts, every Claude Code session: its stage, pass, new or continued, tool calls.
claude_facts()
FRESH = {n["id"].removesuffix("-work") for n in NODES if n["id"].endswith("-work") and re.search(rf"- id: {re.escape(n['id'])}\n(?:\s+\w+:.*\n)*?\s+context: fresh\n", WF)}
assert FRESH == {s_["slug"] for s_ in STAGES if s_["mode"] in ("subagent", "pipeline")}, FRESH
assert not re.search(r"^\s*(skills|agents|hooks|mcp|plugins|model):", WF, re.M)
assert not any(".claude" in q.parts for q in (DATA / "files").rglob("*"))
assert "You lead it as the team's" in WF


def cc_sessions(path):
    rows, rid = [], None
    for ln in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(ln)
        rid = rid or d.get("workflow_id")
        if d.get("workflow_id") != rid:
            continue
        if d.get("type") == "node_start" and d["execution"]["node"]["kind"] in ("agent", "loop"):
            n, b = d["execution"]["node"], d["execution"]["binding"]
            assert b["provider"] == "claude" and not n.get("skills")
            rows.append([d["step"], b["sessionOrigin"], b["model"].get("requested"), {}])
        if d.get("type") == "provider_event":
            e = d["event"]
            if e.get("type") == "tool_call":
                rows[-1][3][e["name"]] = rows[-1][3].get(e["name"], 0) + 1
            if e.get("type") == "subtask":
                assert e.get("taskType") in ("local_bash", None), e
    assert rows and not any({"Skill", "Task", "Agent"} & set(r[3]) for r in rows)
    return rid, rows


_rid, CC = cc_sessions(RUNDIR / "log.jsonl")
assert _rid == RUN_ID
_, CC_FIX = cc_sessions(RUNDIR / "fix-log.jsonl")
assert [(r[0], r[1]) for r in CC] == [("workspace-detection", "fresh"), ("reverse-engineering-work", "fresh"), ("requirements-analysis-work", "fresh"),
                                     ("requirements-analysis-work", "resumed"), ("code-generation-work", "fresh"), ("code-generation-work", "fresh"),
                                     ("build-and-test-work", "fresh")], [(r[0], r[1]) for r in CC]
assert all(r[2] is None for r in CC) and [(r[0], r[2]) for r in CC_FIX] == [("implement", "opus")]
assert CC[0][3].get("StructuredOutput") == 1  # workspace-detection's output_format
_pass, cc_rows = {}, []
for node, origin, _m, tools in CC:
    slug = node.removesuffix("-work")
    _pass[slug] = _pass.get(slug, 0) + 1
    st_ = BY[slug]
    how = ("<code>context: fresh</code> (AI-DLC: " + st_["mode"] + ")") if slug in FRESH else ("no <code>context:</code>" + ("" if slug in INIT_KIND else " (AI-DLC: " + st_["mode"] + ")"))
    cc_rows.append([f"{st_['n']} {x(st_['name'])}", str(_pass[slug]), how,
                    {"fresh": "new", "resumed": "continued pass 1's"}[origin], ", ".join(f"{k} {v}" for k, v in sorted(tools.items(), key=lambda kv: -kv[1]))])
cc_rows.append(["the follow-up fix (step 9)", "1", "<code>archon-implement</code>'s bundled <code>command: implement</code>, model <code>opus</code>", "new",
                ", ".join(f"{k} {v}" for k, v in sorted(CC_FIX[0][3].items(), key=lambda kv: -kv[1]))])
_fresh_ns = ", ".join(BY[s_]["n"] for s_ in sorted(FRESH, key=lambda z: [int(v) for v in BY[z]["n"].split(".")]))
ccard = card("claude", "What each AI node handed Claude Code",
             "<p>AI-DLC's stages become Archon nodes (step 2); Archon's Claude provider then starts <b>one Claude Code session per agent node, and per pass of a loop</b>, through the Claude Agent SDK, in the workspace, with the claude.ai login. So each AI-DLC part ends up as one of Claude Code's own pieces, or as none:</p>"
             + table(["AI-DLC", "In the workflow", "What Claude Code gets"], [
                 ["the stage's <b>lead persona</b> and its support", "words in the stage's prompt (“You lead it as the team's …”)", "the first message of a session. Not a Claude subagent: no <code>agents:</code>, no <code>Task</code>"],
                 ["an <b>inline</b> or <b>mob</b> stage", "an agent node with no <code>context:</code>", "a new session; a redo after a reject <b>continues</b> it, so the agent keeps what it already read and wrote"],
                 [f"a <b>subagent</b> or <b>pipeline</b> stage ({_fresh_ns})", "<code>context: fresh</code>", "a new session every pass, with nothing from earlier nodes but the files on disk. AI-DLC's separate subagent becomes a separate session, not a <code>Task</code> call"],
                 ["Workspace detection's answers", "<code>output_format</code>", "a <code>StructuredOutput</code> tool call the agent ends with"],
                 ["the <b>record</b>", "<code>$ARTIFACTS_DIR/record/…</code> in the prompt", "files the agent writes with <code>Write</code>"],
                 ["the <b>gate</b>, the scope, the phase check, Code Generation's tests", "<code>wait:</code>, <code>script:</code>, <code>bash:</code>, <code>when:</code>", "nothing: Archon runs these without Claude"]])
             + f"<p style=\"margin-top:14px\"><b>The real express run's sessions</b>, from its two transcripts ({len(CC) + 1} in all, real):</p>"
             + table(["Stage", "Pass", "Node field", "Session", "Tool calls"], cc_rows)
             + note("Both redos were asked for by a reject, and they differ because of one field: 2.3's second pass continued its session; 3.5's second pass (<code>context: fresh</code>) started over and read the code from disk. No session called <code>Skill</code> or <code>Task</code>: the workflow names no <code>skills:</code>, <code>agents:</code> or <code>model:</code> (so Claude Code's default model ran), and the workspace has no <code>.claude/</code> folder; the one Claude Code file every session read was the workspace's <code>CLAUDE.md</code>. The transcripts' <i>subtasks</i> are background shell commands, not subagents.")
             + "<p style=\"margin-top:14px\"><b>What each workflow field hands the session</b> (the third column is the course's <code>request-to-pr</code> run):</p>"
             + table(["In the workflow", "What Claude Code gets", "In the course's run"], [list(r_) for r_ in CLAUDE_MAP], "kv")
             + note("Checked against the Archon 0.13.2 docs (workflow language, skills, hooks, authoring commands, security). More: <a href=\"archon-introduction.html#s11\">the introduction, step 11</a>; where Claude Code's own files go in a workspace: <a href=\"archon-workspace-setup.html#claude\">the setup page</a>."))

STEPS_RAIL = [(1, "Two tools, one lifecycle"), (2, "The translation"), (3, "The 33 stages"), (4, "One stage up close"), (5, "How the scope picks"),
              (6, "Thirteen dry runs"), (7, "Same, and not"),
              (8, "A real express run"), (9, "The follow-up fix"), (10, "What it showed"), (11, "Run it yourself"), (12, "The files")]
PH = {1: ("The idea", "--setup"), 2: ("The idea", "--setup"), 3: ("The map", "--plan"), 4: ("The map", "--plan"), 5: ("The map", "--plan"),
      6: ("The check", "--build"), 7: ("The check", "--build"), 8: ("The real run", "--review"), 9: ("The real run", "--review"), 10: ("The real run", "--review"),
      11: ("Try it", "--ship"), 12: ("Try it", "--ship")}
assert len(S) == len(STEPS_RAIL)

hero = f'''<section class="hero" id="top">
  <div>
    <h1>AWS AI-DLC, stage by stage, as an Archon workflow.</h1>
    <p class="lead">AI-DLC's 33 stages, each drawn as the Archon nodes it becomes: an agent that does the stage's work and a gate where a person approves it. The workflow is generated from AI-DLC's own stage table, validated by Archon, dry-run for every scope, and run for real once with Claude (express: four stages, two sent back at their gates). Pick a scope on the map and see which stages Archon ran.</p>
    <div class="facts">
      <div><b>33</b>AI-DLC stages, one Archon loop each</div>
      <div><b>30</b>gates: approval waits</div>
      <div><b>11</b>scopes, one input</div>
      <div><b>{len(RUNS)}</b>real dry runs, all matching</div>
      <div><b>{N_NODES}</b>nodes in one workflow file</div>
      <div><b>${COST_RUN + FIX_COST:.2f}</b>one real express run and its follow-up fix</div>
    </div>
  </div>
  <aside class="slack" aria-label="The short version">
    <div class="slack__bar"><span>The short version</span><span>Archon 0.13.2 · AI-DLC 2.11</span></div>
    <div class="slack__body">
      <p style="margin:0 0 8px"><b>Stage</b> → agent node + approval wait<br><span style="color:var(--ink-3)">in a loop_group: reject redoes it</span></p>
      <p style="margin:0 0 8px"><b>Scope</b> → <code>--input scope=…</code><br><span style="color:var(--ink-3)">a script turns it into true/false per stage</span></p>
      <p style="margin:0 0 8px"><b>Conditional</b> → <code>when:</code><br><span style="color:var(--ink-3)">on every stage</span></p>
      <p style="margin:0"><b>Record</b> → the run's artifacts<br><span style="color:var(--ink-3)">record/&lt;phase&gt;/&lt;stage&gt;.md</span></p>
    </div>
  </aside>
</section>
'''
real = card("real", "Where this comes from", f"""<p>AI-DLC's 33 stages, their phases, lead and support personas and modes, and the 11 scope lists are AI-DLC Workflows 2.11's own tables (<code>aidlc engine gen stage-table</code> and <code>gen scope-table</code>), copied from the AI-DLC course into <code>tools/data/aidlc/</code>. The personas' short roles and each stage's one-line job are this course's words. The workflow and its script are generated by <code>tools/make_aidlc_workflow.py</code>. Every Archon output on the page is real, from Archon 0.13.2 on Windows (5 Nov 2026), captured by <code>tools/capture_aidlc_map.py</code> in a copy of the course's java workspace. The real express run and its follow-up fix (steps 8–10; Claude Code on the claude.ai login, 5 Nov 2026) started from the public starter and was captured by <code>tools/capture_aidlc_run.py</code>; the gate answers are the course cast's. Items marked {DOC} were not run.</p>""")
main = (hero + phase("--setup", "The idea", "steps 1–2 · what each tool does, and how one maps onto the other") + "".join(S[0:2])
        + phase("--plan", "The map", "steps 3–5 · every stage, one up close, and how the scope picks them") + "".join(S[2:5])
        + phase("--build", "The check", "steps 6–7 · Archon's real dry runs, and the limits") + "".join(S[5:7])
        + phase("--review", "The real run", "steps 8–10 · one express run with Claude, gate by gate, its follow-up fix, and what it showed") + "".join(S[7:10])
        + phase("--ship", "Try it", "steps 11–12 · in your workspace, and the files") + "".join(S[10:12]) + ccard + real)
footer = ('<footer class="foot">AI-DLC on Archon · Archon 0.13.2 · AI-DLC Workflows 2.11 · <a href="archon-introduction.html">introduction</a> · '
          '<a href="../ai-dlc-execution/aidlc-introduction.html">the AI-DLC course</a> · <a href="index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("AI-DLC on Archon", "AWS AI-DLC's 33 stages written as one Archon workflow: each stage an agent node and an approval gate, the scope an input, with an interactive map of which stages run in each scope, checked by Archon's real validate and dry runs.",
             "AI-DLC on Archon", "33 stages · 30 gates · 11 scopes", len(STEPS_RAIL), rail(STEPS_RAIL, PH, [("claude", "What Claude Code got"), ("real", "Where this comes from")]), main, footer, MAP_JS)
write(ROOT / "archon-aidlc-on-archon.html", html_)
