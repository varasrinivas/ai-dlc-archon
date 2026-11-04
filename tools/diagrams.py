"""Inline-SVG diagrams for the step pages, drawn from data (theme tokens, so they follow light and dark mode)."""
from pagekit import ARROW_DEF, E, svg, t

KIND = {  # colour token, label
    "prompt": ("--plan", "AI prompt"), "command": ("--plan", "AI command"), "loop": ("--build", "AI loop"),
    "loop_group": ("--build", "loop group"), "bash": ("--ship", "bash"), "script": ("--ship", "script"),
    "wait": ("--gate", "wait"), "cancel": ("--bad", "cancel"),
}


def _rect(x, y, w, h, col, dash=False, op=.13, rx=9):
    d = ";stroke-dasharray:5 4" if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" style="fill:var({col});fill-opacity:{op};'
            f'stroke:var({col});stroke-width:1.6{d}"/>')


def _path(d, col="--ink-3", dash=False, marker=True):
    s = ";stroke-dasharray:4 4" if dash else ""
    m = ' marker-end="url(#ah)"' if marker else ""
    return f'<path d="{d}" style="fill:none;stroke:var({col});stroke-width:1.5{s}"{m}/>'


def workflow_dag(nodes, title, notes=None, highlight=()):
    """nodes from cli_parse.workflow_nodes. One row per layer; a loop_group is drawn as a box holding its body.
    notes: {node_id: short text shown to the right}. highlight: node ids drawn with a thicker outline."""
    notes = notes or {}
    by_id = {n["id"]: n for n in nodes}
    top = [n for n in nodes if n["parent"] is None]
    layer = {}
    for n in top:  # file order is a topological order for the course's workflow
        layer[n["id"]] = 1 + max((layer[d] for d in n["deps"]), default=-1)
    rows = {}
    for n in top:
        rows.setdefault(layer[n["id"]], []).append(n)
    W, NW, NH, GAP, X0 = 820, 200, 44, 26, 30
    y, pos, parts = 20, {}, []
    for L in sorted(rows):
        row = rows[L]
        is_group = any(n["kind"] == "loop_group" for n in row)
        h = NH + (74 if is_group else 0)
        for i, n in enumerate(row):
            x = X0 + i * (NW + 30) if len(row) > 1 else X0 + 115
            col, label = KIND[n["kind"]]
            if n["kind"] == "loop_group":
                body = [b for b in nodes if b["parent"] == n["id"]]
                gw = 2 * NW + 50
                gx = X0 + 10
                parts.append(_rect(gx, y, gw, h, col, dash=False, op=.05, rx=12))
                parts.append(t(gx + 12, y + 18, f'{n["id"]}  ·  loop_group', 12, 700, f"var({col})", "start"))
                for j, b in enumerate(body):
                    bx, by = gx + 15 + j * (NW + 20), y + 32
                    bc, bl = KIND[b["kind"]]
                    parts.append(_rect(bx, by, NW, NH, bc, dash=b["kind"] == "wait"))
                    parts.append(t(bx + NW / 2, by + 19, b["id"], 12.5, 700, mono=True))
                    parts.append(t(bx + NW / 2, by + 35, bl, 10.5, 400, "var(--ink-3)"))
                    pos[b["id"]] = (bx, by, NW, NH)
                # body edge + loop-back
                (ax, ay, aw, ah), (bx, by, bw, bh) = pos[body[0]["id"]], pos[body[1]["id"]]
                parts.append(_path(f"M{ax + aw} {ay + ah / 2} L{bx - 4} {by + bh / 2}"))
                parts.append(_path(f"M{bx + bw / 2} {by + bh} C{bx + bw / 2} {by + bh + 16}, {ax + aw / 2} {ay + ah + 16}, {ax + aw / 2} {ay + ah + 3}", "--gate", dash=True))
                parts.append(t((ax + bx + bw) / 2 - 40, by + bh + 27, "reject → revise", 10, 600, "var(--gate)"))
                pos[n["id"]] = (gx, y, gw, h)
            else:
                parts.append(_rect(x, y, NW, NH, col, dash=n["kind"] == "wait"))
                if n["id"] in highlight:
                    parts.append(f'<rect x="{x - 3}" y="{y - 3}" width="{NW + 6}" height="{NH + 6}" rx="11" style="fill:none;stroke:var({col});stroke-width:2.6"/>')
                parts.append(t(x + NW / 2, y + 19, n["id"], 12.5, 700, mono=True))
                parts.append(t(x + NW / 2, y + 35, label, 10.5, 400, "var(--ink-3)"))
                pos[n["id"]] = (x, y, NW, NH)
            if n["id"] in notes:
                px, py, pw, ph = pos[n["id"]]
                nx = px + pw + 14 if len(row) == 1 or i == len(row) - 1 else None
                if nx is not None:
                    parts.append(t(nx, py + ph / 2 + 4, notes[n["id"]], 11, 400, "var(--ink-2)", "start"))
        y += h + GAP
    # edges between top-level nodes
    for n in top:
        for d in n["deps"]:
            ax, ay, aw, ah = pos[d]
            bx, by, bw, bh = pos[n["id"]]
            x1, x2 = ax + aw / 2, bx + bw / 2
            parts.append(_path(f"M{x1} {ay + ah} C{x1} {ay + ah + 14}, {x2} {by - 14}, {x2} {by - 3}"))
            if n["when"]:
                verb = "approve" if "'approve'" in n["when"] else "reject" if "'reject'" in n["when"] else "when"
                parts.append(t(x2 + (8 if x2 >= x1 else -8), by - 8, verb, 10, 600, "var(--gate)", "start" if x2 >= x1 else "end"))
    H = y + 34
    lx = 30
    for k in ("prompt", "loop", "bash", "wait", "cancel"):
        col, label = KIND[k]
        parts.append(_rect(lx, H - 26, 14, 14, col, dash=k == "wait", rx=3))
        parts.append(t(lx + 20, H - 15, label, 11, 400, "var(--ink-3)", "start"))
        lx += 112
    return '<div class="gwrap">' + svg(W, H, ARROW_DEF + "".join(parts), title) + "</div>"


def node_cycle():
    """How one node runs: inputs -> agent (or bash) in the worktree -> output -> next node; a wait goes to a person."""
    p = [ARROW_DEF]
    boxes = [(20, "Inputs", ["$USER_MESSAGE", "$plan.output", "$ARTIFACTS_DIR/*.md"], "--setup"),
             (220, "The node runs", ["prompt / command → Claude Code", "bash / script → code", "in the run's worktree"], "--plan"),
             (440, "Its output", ["final reply, or stdout", "JSON if output_format", "files in $ARTIFACTS_DIR"], "--build"),
             (640, "Next nodes", ["when: reads the output", "depends_on joins", "loop: until_bash checks"], "--review")]
    for x, title, lines, col in boxes:
        p.append(_rect(x, 30, 180, 120, col, op=.1, rx=12))
        p.append(t(x + 90, 54, title, 14, 700))
        for i, s in enumerate(lines):
            p.append(t(x + 90, 80 + i * 20, s, 11.5, 400, "var(--ink-2)", mono=s.startswith("$") or "→" in s))
    for x in (200, 420, 620):
        p.append(_path(f"M{x} 90 L{x + 18} 90"))
    p.append(_rect(330, 190, 200, 56, "--gate", dash=True, op=.12, rx=12))
    p.append(t(430, 213, "wait: a person answers", 13, 700))
    p.append(t(430, 232, "approve · reject · text", 11.5, 400, "var(--ink-2)", mono=True))
    p.append(_path("M530 150 C530 175, 470 175, 470 188", "--gate", dash=True))
    p.append(_path("M530 218 C640 218, 700 190, 700 152", "--gate", dash=True))
    p.append(t(20, 278, "A node never talks to the next node's agent: it hands over through its output and the run's artifact files.", 12, 400, "var(--ink-3)", "start"))
    return '<div class="gwrap">' + svg(840, 290, "".join(p), "How one node runs, and where a person comes in") + "</div>"
