"""Parse the real `archon help` text and the team workflow YAML into data the pages draw from."""
import re


def help_sections(text):
    """-> {'commands': [(cmd, desc)], 'options': [(flag, desc)], 'examples': [str]} from `archon help`."""
    out = {"commands": [], "options": [], "examples": []}
    sec = None
    for line in text.splitlines():
        if line.strip() in ("Commands:", "Options:", "Examples:"):
            sec = line.strip()[:-1].lower()
            continue
        if sec is None or not line.strip():
            continue
        if sec == "examples":
            out["examples"].append(line.strip())
            continue
        if re.match(r"^  \S", line):
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
            out[sec].append([parts[0], parts[1] if len(parts) > 1 else ""])
        elif out[sec]:
            last = out[sec][-1]
            last[1] = (last[1] + " " + line.strip()).strip()
    return {k: [tuple(x) if isinstance(x, list) else x for x in v] for k, v in out.items()}


def workflow_nodes(yaml_text):
    """A small reader for the course's own workflow file (no YAML library needed):
    -> [{'id', 'kind', 'deps', 'when', 'parent'}] in file order. Nodes inside a loop_group get parent = the group id."""
    nodes, cur, group, group_indent = [], None, None, None
    kinds = ("prompt", "command", "bash", "script", "loop", "loop_group", "wait", "cancel", "include", "workflow", "approval")
    for line in yaml_text.splitlines():
        m = re.match(r"^(\s*)- id: ([\w-]+)", line)
        if m:
            indent = len(m.group(1))
            if group is not None and indent <= group_indent:
                group = None
            cur = {"id": m.group(2), "kind": None, "deps": [], "when": None, "parent": group, "indent": indent}
            nodes.append(cur)
            continue
        if cur is None:
            continue
        s = line.strip()
        d = re.match(r"depends_on: \[(.*)\]", s)
        if d and len(line) - len(line.lstrip()) == cur["indent"] + 2:
            cur["deps"] = [x.strip() for x in d.group(1).split(",") if x.strip()]
        w = re.match(r'when: "(.*)"', s)
        if w and len(line) - len(line.lstrip()) == cur["indent"] + 2:
            cur["when"] = w.group(1)
        k = re.match(r"(\w+):", s)
        if k and k.group(1) in kinds and cur["kind"] is None and len(line) - len(line.lstrip()) == cur["indent"] + 2:
            cur["kind"] = k.group(1)
            if k.group(1) == "loop_group":
                group, group_indent = cur["id"], cur["indent"]
    for n in nodes:
        assert n["kind"], f"no body found for node {n['id']}"
    return nodes
