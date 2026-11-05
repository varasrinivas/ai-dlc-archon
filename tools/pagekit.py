"""Shared page pieces for the Archon course's step pages (introduction, setup, hello-world run).

The frame (tools/frame/style.css + script.js) is the AI-DLC course's run-page frame, copied by make_frame.py,
so both courses look and behave alike: theme and OS toggles, copy buttons, tabs, highlighter, scroll-spy rail.
Phase colours: --setup (grey), --plan (teal), --build (orange), --review (purple), --ship (green), --gate (amber).
"""
import getpass
import html
import re
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAME = ROOT / "tools" / "frame"
E = html.escape

EXTRA_CSS = """
figure.dia{margin:14px 0}figure.dia figcaption{font-size:.82rem;color:var(--ink-3);text-align:center;margin-top:4px}
.gwrap{overflow-x:auto;max-width:100%}.gwrap figure.dia{min-width:760px}.gwrap table{display:table}
.kv{table-layout:fixed}.kv td:first-child,.kv th:first-child{width:34%}.kv td:first-child code{white-space:normal;overflow-wrap:anywhere}
.ref-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}
@media (max-width:760px){.ref-grid{grid-template-columns:minmax(0,1fr)}}
.ref-grid>div{background:var(--bg-2);border-radius:12px;padding:12px 14px;font-size:.92rem}
.ref-grid h3{margin:0 0 4px;font:700 1rem var(--font-display)}
.ref-grid h3 small{font:500 .78rem var(--font-mono);color:var(--ink-3);margin-left:6px}
.ref-grid p{margin:0 0 6px}.ref-grid ul{margin:0;padding-left:1.1em}.ref-grid li{margin:2px 0}
.filter{width:100%;padding:9px 12px;border:1.5px solid var(--line-2);border-radius:10px;background:var(--panel);color:var(--ink);font:500 .92rem var(--font-mono);margin:10px 0}
.flist{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:10px}.flist table{margin:0}
.flist td:first-child{font-family:var(--font-mono);font-size:.8rem;white-space:nowrap}.flist td:last-child{font-size:.86rem;color:var(--ink-2)}
.tag-yes{color:var(--ok);font-weight:600}.tag-no{color:var(--ink-3)}
.lbl{display:inline-block;font:600 .72rem var(--font-mono);padding:1px 7px;border-radius:999px;vertical-align:2px;margin-left:4px}
.lbl-real{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
.lbl-doc{background:color-mix(in srgb,var(--gate) 18%,transparent);color:var(--gate-ink)}
[data-theme="dark"] .lbl-doc{color:var(--gate)}
@media (max-width:680px){.who,.box__bar .tag{white-space:normal;overflow-wrap:anywhere;min-width:0}.box__bar{flex-wrap:wrap}}
.node{display:inline-block;font:600 .8rem var(--font-mono);padding:1px 8px;border-radius:6px;border:1.5px solid var(--c,var(--line-2));color:var(--ink)}
"""


def head(title, description):
    style = (FRAME / "style.css").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@600;700;800&family=Red+Hat+Text:wght@400;500;600&family=Red+Hat+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script>document.documentElement.classList.add('js');</script>
<style>
{style}{EXTRA_CSS}</style>
</head>
"""


def script():
    return "<script>\n" + (FRAME / "script.js").read_text(encoding="utf-8") + "</script>\n"


def header(brand, sub, total):
    return f'''<header class="top"><div class="top__in">
  <div class="brand">{brand}<small>{sub}</small></div>
  <div class="prog" aria-live="polite"><b id="progText">Step 0 of {total}</b><div class="bar"><i id="progBar"></i></div><span class="ph" id="progPhase">Start at the top</span></div>
  <div class="top__btns"><button class="btn" id="osToggle" type="button" title="Show the commands for your computer">Windows</button><button class="btn" id="themeToggle" type="button" aria-pressed="false">Dark mode</button></div>
</div></header>
'''


def rail(steps, phases, refs=()):
    """steps: [(n, label)]; phases: {n: (phase name, colour token)}; refs: [(anchor, label)] after the steps."""
    out, last = ['<nav class="rail" aria-label="Steps">'], None
    for n, label in steps:
        ph, col = phases[n]
        if ph != last:
            out.append(f"  <h4>{ph}</h4>")
            last = ph
        out.append(f'  <a class="rl" href="#s{n:02d}" data-step="{n}" style="--c:var({col})"><b>{n}</b><span>{label}</span></a>')
    if refs:
        out.append("  <h4>Reference</h4>")
        for anchor, label in refs:
            out.append(f'  <a class="rl" href="#{anchor}" style="--c:var(--review)"><b>·</b><span>{label}</span></a>')
    out.append("</nav>")
    return "\n".join(out)


def page(title, description, brand, sub, total, rail_html, main_html, footer_html, extra_js=""):
    return (head(title, description) + '<body>\n<a class="sr" href="#main">Skip to content</a>\n' + header(brand, sub, total)
            + '\n<div class="shell">\n' + rail_html + '\n\n<main id="main">\n' + main_html + "\n</main>\n</div>\n\n"
            + footer_html + script() + extra_js + "</body>\n</html>\n")


# ---------- boxes ----------
def you(win, mac=None, tag="", mac_tag=None):
    body = f"<pre>{win}</pre>" if mac is None else f'<pre class="os-win">{win}</pre><pre class="os-mac">{mac}</pre>'
    t = tag if mac_tag is None else f'<span class="os-win">{tag}</span><span class="os-mac">{mac_tag}</span>'
    return f'<div class="box you"><div class="box__bar">You type <span class="tag">{t}</span></div>{body}<button class="copy" type="button">copy</button></div>'


def see(text, tag="", label="You see"):
    return f'<div class="box claude"><div class="box__bar">{label} <span class="tag">{tag}</span></div><pre>{text}</pre></div>'


def disk(text, title="On disk now"):
    return f'<div class="box disk"><div class="box__bar">{title}</div><pre>{text}</pre></div>'


def io(*boxes, stack=False):
    return f'<div class="io{" io--stack" if stack else ""}">' + "".join(boxes) + "</div>"


def tabs(prefix, files):
    """files: [(label, path, note, lang, content)] -> tabbed, highlighted file viewers."""
    btns, panes = [], []
    for i, (label, path, note_, lang, content) in enumerate(files):
        pid = f"{prefix}-{i + 1}"
        btns.append(f'<button class="tab" role="tab" aria-selected="{"true" if i == 0 else "false"}" data-pane="{pid}">{label}</button>')
        panes.append(f'<div class="pane{" is-on" if i == 0 else ""}" id="{pid}"><div class="code code--wrap"><div class="code__bar"><span class="path">{path}</span><span>{note_}</span></div><textarea class="src" data-lang="{lang}">{E(content)}</textarea></div></div>')
    return f'<div class="open"><div class="tabs" role="tablist">{"".join(btns)}</div>{"".join(panes)}</div>'


def step(n, phase_, color, chip, title, why, who, body, ours=False):
    chipcls = "chip chip--ours" if ours else "chip"
    return f'''<section class="step" id="s{n:02d}" data-step="{n}" data-phase="{phase_}" style="--c:var({color})">
  <div class="step__head"><span class="step__n">{n}</span><div><span class="{chipcls}">{chip}</span><h2>{title}</h2><p class="step__why">{why}</p></div><span class="who">{who}</span></div>
{body}
</section>
'''


def card(anchor, title, body):
    return f'<section class="card" id="{anchor}">\n  <h2>{title}</h2>\n{body}\n</section>\n'


def gate(title, text, by=""):
    by_html = f'<p class="by">{by}</p>' if by else ""
    return f'<div class="gate"><div><b>{title}</b><p>{text}</p>{by_html}</div></div>'


def note(t):
    return f'<div class="note">{t}</div>'


def plain(t):
    return f'<div class="plain"><div><b>In plain words.</b> {t}</div></div>'


# Archon's own words, defined once for every page that has a glossary (term -> one line).
ARCHON_WORDS = {
    "workflow": "the YAML file with the team's process (<code>request-to-pr</code>): which steps, in which order, where to stop for people",
    "node": "one step of a workflow: an agent prompt, a bash command, a loop or a wait",
    "run": "one execution of a workflow, with a run id; it keeps a transcript, the files it wrote and what it cost",
    "wait": "a node that pauses the run until someone answers",
    "form": "what a wait accepts: message, approval, select",
    "loop_group": "a few nodes repeated until a check passes; here, until the requirements are approved",
    "until_bash": "the shell check that ends a loop on exit 0",
    "artifacts": "the files a run writes for people and later nodes: scan.md, requirements.md, plan.md…",
    "workspace": "the team's folder around the code repo: .archon/, CLAUDE.md, scripts, requests; a git repo of its own",
    "folder project": "a workspace registered with --folder: Archon runs in place, no worktree, the agent does the git",
    "worktree": "a second checkout of a repo in another folder, on its own branch; Archon makes one per run in a repo project",
    "provider": "the coding agent Archon drives: Claude Code here (Codex and Pi are the others)",
    "token": "the unit an AI model counts and bills text in, roughly ¾ of a word; agent nodes use them, bash and waits don't",
}


def gloss(pairs):
    """[(term, definition)] -> a <dl class="gloss"> with one row per term."""
    return '<dl class="gloss">' + "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in pairs) + "</dl>"


def three(cells):
    return '<div class="three">' + "".join(f"<div><b>{h}</b>{b}</div>" for h, b in cells) + "</div>"


def phase(color, name, sub):
    return f'<div class="phase" style="--c:var({color})"><i></i>{name}<span>{sub}</span></div>\n'


def row(cells):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def table(head_cells, rows, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f"<div class=\"gwrap\"><table{c}><thead><tr>" + "".join(f"<th>{h}</th>" for h in head_cells) + "</tr></thead><tbody>"
            + "".join(row(r) for r in rows) + "</tbody></table></div>")


REAL = '<span class="lbl lbl-real">real</span>'
DOC = '<span class="lbl lbl-doc">documented</span>'


# ---------- inline SVG (colours are the page's theme tokens, so diagrams follow light and dark mode) ----------
def svg(w, h, body, label):
    return (f'<figure class="dia"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(label)}" '
            f'style="width:100%;height:auto;font-family:var(--font-text);">{body}</svg><figcaption>{E(label)}</figcaption></figure>')


def t(x, y, text, size=13, weight=400, fill="var(--ink)", anchor="middle", mono=False):
    fam = "font-family:var(--font-mono);" if mono else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" style="{fam}fill:{fill};font-size:{size}px;font-weight:{weight}">{E(text)}</text>'


def box(x, y, w, h, color, fill_op=.14, rx=10, dash=False):
    d = ";stroke-dasharray:5 4" if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" style="fill:var({color});fill-opacity:{fill_op};'
            f'stroke:var({color});stroke-width:1.6{d}"/>')


def arrow(x1, y1, x2, y2, color="--ink-3", dash=False):
    d = ";stroke-dasharray:4 4" if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:var({color});stroke-width:1.6{d}" marker-end="url(#ah)"/>')


ARROW_DEF = '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--ink-3)"/></marker></defs>'


# ---------- privacy: no local paths on a page ----------
_U, _H = getpass.getuser(), socket.gethostname()  # this machine's user and hostname, read here, never written down


def _git_identity():
    """This machine's git name and email (commits made where no identity was set carry them), read, never written down."""
    import subprocess
    get = lambda k: subprocess.run(["git", "config", "--global", k], capture_output=True, encoding="utf-8").stdout.strip()  # noqa: E731
    return get("user.name"), get("user.email")


_GN, _GE = _git_identity()
LEAKS = ["C:\\Users\\" + _U, "C:/Users/" + _U, "C:\\\\Users\\\\" + _U, r"D:\tmp", "D:/tmp", r"D:\\tmp", "/d/tmp", "@gmail.com",
         r"\AppData\Local\Temp", "Users-" + _U, _H, "/c/Users/" + _U] + ([_GE] if _GE else [])


def scrub(text):
    """Map this machine's paths, and its git identity, to the ones the pages show."""
    if _GE:
        text = text.replace(f"{_GN} <{_GE}>", "you <you@example.com>").replace(_GE, "you@example.com")
    for a, b in [("C:\\\\Users\\\\" + _U, r"C:\\Users\\you"), (r"D:\\tmp\\archon-java", r"C:\\work\\archon-java"),
                 (r"D:\\Program Files\\Git", r"C:\\Program Files\\Git"), ("Users-" + _U + "-", "Users-you-"),
                 (_H, "your-pc"), ("/c/Users/" + _U, "/c/Users/you"),
                 ("C:\\Users\\" + _U, r"C:\Users\you"), ("C:/Users/" + _U, "C:/Users/you"), (r"D:\tmp\archon-java", r"C:\work\archon-java"),
                 ("D:/tmp/archon-java", "C:/work/archon-java"), ("/d/tmp/archon-java", "/c/work/archon-java"),
                 (r"D:\Program Files\Git", r"C:\Program Files\Git"),
                 (r"D:\\tmp", r"C:\\work"), (r"D:\tmp", r"C:\work"), ("D:/tmp", "C:/work"), ("/d/tmp", "/c/work")]:  # other run folders, as scrub_captures.py maps them
        text = text.replace(a, b)
    return text


def assert_clean(page_html, name):
    for leak in LEAKS:
        assert leak.lower() not in page_html.lower(), f"{name}: local path {leak!r} leaked onto the page"
    assert "ANTHROPIC_API_KEY=sk" not in page_html


# ---------- documented (not run) facts: checked against Archon's own text ----------
def doc_says(doc, *phrases):
    """Assert each phrase is in tools/data/docs/<doc> (copied from Archon v0.13.2's packages/docs-web, MIT)."""
    text = (ROOT / "tools" / "data" / "docs" / doc).read_text(encoding="utf-8")
    for p in phrases:
        assert p in text, f"{doc} no longer says {p!r}"


def multirepo_facts(cli):
    """What the pages say about work across several repos (a folder project), each line tied to the docs or the help."""
    doc_says("multi-repo-projects.md",
             "running in place (no worktree isolation)", "The first run registers the folder project; later runs from the root",
             "**Per-service git is the agent's job.** Archon does not create a worktree or manage branches/PRs for a folder project",
             "`--branch` and `--from` are rejected", "~/.archon/workspaces/_folder/<slug>/",
             "Archon does not create a composed multi-repo worktree", "register that service repo as its **own** project",
             "Opt into overlay-isolated, approval-gated container execution with `--container`")
    doc_says("global-workflows.md", "Workflows placed in `~/.archon/workflows/`", "they appear in every project")
    run_help = cli["help-workflow-run"]["out"]
    for flag in ["--folder                   Register the current directory (with or without git) as a folder project and run in place",
                 "--container                Run a folder project in container isolation",
                 "--workflow-source <path>   Read the workflow, its commands and scripts from this directory",
                 "instead of --cwd (which stays the workspace the run acts on)"]:
        assert flag in run_help, flag


def write(path, page_html):
    assert_clean(page_html, path.name)
    path.write_text(page_html, encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ROOT)}  {len(page_html):,} bytes")


def strip_ansi(s):
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", s)


def shell_group(steps, labels, quiet=("LF will be replaced by CRLF", "CRLF will be replaced by LF")):
    """The recorded setup commands `labels` (from a steps dict) as one Git Bash script, with a `cd` wherever the
    folder changes, and what they printed (stdout, plus stderr that is not git's line-ending chatter)."""
    cmds, outs, cwd = [], [], None
    for label in labels:
        s = steps[label]
        assert s["exit"] == 0, (label, s["exit"])
        d = s["cwd"].replace("\\", "/")
        if d != cwd:
            cmds.append(f"cd {d}")
            cwd = d
        cmds.append(s["cmd"].strip())
        err = "\n".join(ln for ln in s["stderr"].splitlines() if ln.strip() and not any(q in ln for q in quiet))
        out = (s["stdout"].strip() + ("\n" + err if err else "")).strip()
        if out:
            outs.append(out)
    return "\n".join(cmds), "\n".join(outs) or "(no output: git -q prints nothing when it succeeds)"
