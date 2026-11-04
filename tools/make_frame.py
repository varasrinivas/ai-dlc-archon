"""Copy the page frame (head CSS + main script) from the AI-DLC course's Java run page into tools/frame/.

The Archon course uses the same design so the two courses read as one series. Run once, or again after the
AI-DLC run page's frame changes:  py -3.12 tools/make_frame.py [path-to-ai-dlc-execution]

Changes made on the way: the phase colours are renamed for Archon's phases (setup, plan, build, review, ship),
the localStorage keys get the course's own prefix, and the highlighter learns jsonl and a bash prompt line.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "ai-dlc-execution"
RUN = (SRC / "aidlc-hello-world-java" / "aidlc-hello-world-java-run.html").read_text(encoding="utf-8")

style = RUN[RUN.index("<style>") + len("<style>"):RUN.index("</style>")]
start = RUN.index("<script>\n(function () {")
script = RUN[start + len("<script>"):RUN.index("</script>", start)]

# Phase colours: AI-DLC's four phases -> Archon's five. --operation (purple) becomes review; ship is new (green).
RENAME = [("--init", "--setup"), ("--inception", "--plan"), ("--construction", "--build"), ("--operation", "--review")]
for old, new in RENAME:
    style = re.sub(re.escape(old) + r"(?![\w-])", new, style)
assert "--inception" not in style and "--operation" not in style
style = style.replace("--review:#6D28D9;", "--review:#6D28D9; --ship:#15803D;", 1)
style = style.replace("--review:#A78BFA;", "--review:#A78BFA; --ship:#4ADE80;", 1)
assert style.count("--ship:") == 2, "phase token insert failed"
style = style.replace("linear-gradient(90deg,var(--plan),var(--build),var(--review))",
                      "linear-gradient(90deg,var(--plan),var(--build),var(--review),var(--ship))")

assert script.count("hwj-") == 4
script = script.replace("hwj-", "arc-")
# jsonl: highlight each line as json.
script = script.replace("case 'json': return", "case 'jsonl': case 'json': return", 1)
script = script.replace("/^(json|md|yaml|bash)$/", "/^(json|jsonl|md|yaml|bash|text)$/")
assert "case 'jsonl'" in script

out = ROOT / "tools" / "frame"
out.mkdir(parents=True, exist_ok=True)

# The concepts page has its own, quieter design (Source Sans, warm palette, print styles): copy it too.
CON = (SRC / "aidlc-concepts-explained.html").read_text(encoding="utf-8")
cstyle = CON[CON.index("<style>") + len("<style>"):CON.index("</style>")]
cscript = CON[CON.rindex("<script>") + len("<script>"):CON.rindex("</script>")]
assert "ce-theme" in cscript
cscript = cscript.replace("ce-theme", "arc-ce-theme")
# The concept map is drawn with theme tokens here (the AI-DLC one is a white picture), so the chart box follows the theme.
cstyle = cstyle.replace(".chart{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#fff}",
                        ".chart{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}")
cstyle = cstyle.replace(".chart svg{display:block;min-width:1100px;width:100%;height:auto}",
                        ".chart svg{display:block;min-width:900px;width:100%;height:auto}")
assert "background:var(--panel)}" in cstyle
(out / "concepts.css").write_text(cstyle.strip() + "\n", encoding="utf-8")
(out / "concepts.js").write_text(cscript.strip() + "\n", encoding="utf-8")
(out / "style.css").write_text(style.strip() + "\n", encoding="utf-8")
(out / "script.js").write_text(script.strip() + "\n", encoding="utf-8")
print(f"style.css {len(style)} chars, script.js {len(script)} chars")
