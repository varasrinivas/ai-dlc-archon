"""AWS AI-DLC's stage graph, read from the engine's own tables, and how each stage maps onto Archon.

Data (copied from ../ai-dlc-execution/aidlc-hello-world-java/scopes-data/, AI-DLC Workflows 2.11):
  tools/data/aidlc/stage-table.md   `aidlc engine gen stage-table`: 33 stages, phase, ALWAYS/CONDITIONAL, lead, support, mode
  tools/data/aidlc/scope-table.md   `aidlc engine gen scope-table`: 11 scopes and their stage counts
  tools/data/aidlc/scopes/scope-<scope>.txt   the stage slugs each scope executes

Used by tools/make_aidlc_workflow.py (writes the workflow) and tools/build_aidlc_map_page.py (draws the page).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data" / "aidlc"
WF_DIR = DATA / "files" / ".archon" / "workflows" / "aidlc" / "aidlc-on-archon"
WF_FILE = WF_DIR / "aidlc-on-archon.yaml"
WF_REL = ".archon/workflows/aidlc/aidlc-on-archon/aidlc-on-archon.yaml"


def _rows(md):
    rows = [l for l in md.splitlines() if l.startswith("|")]
    return [[c.strip() for c in l.strip().strip("|").split("|")] for l in rows[2:]]


STAGES = [dict(slug=r[0], n=r[1], name=r[2], phase=r[3], execution=r[4], lead=r[5],
               support=[s.strip() for s in r[6].split(",") if s.strip().startswith("aidlc-")], mode=r[7])
          for r in _rows((DATA / "stage-table.md").read_text(encoding="utf-8"))]
assert len(STAGES) == 33, len(STAGES)
PHASES = ["Initialization", "Ideation", "Inception", "Construction", "Operation"]
assert [p for p in PHASES if any(s["phase"] == p for s in STAGES)] == PHASES

SCOPE_ROWS = _rows((DATA / "scope-table.md").read_text(encoding="utf-8"))
SCOPES = {r[0]: set((DATA / "scopes" / f"scope-{r[0]}.txt").read_text(encoding="utf-8").split()) for r in SCOPE_ROWS}
for r in SCOPE_ROWS:
    assert len(SCOPES[r[0]]) == int(r[3].split("/")[0]), r
SCOPE_ORDER = sorted(SCOPES, key=lambda s: (len(SCOPES[s]), s))
SLUGS = [s["slug"] for s in STAGES]
assert all(SCOPES[s] <= set(SLUGS) for s in SCOPES)

# Persona -> its role in a few words (ours, not the agent files' text).
ROLE = {
    "(orchestrator)": "the engine itself",
    "aidlc-product-agent": "product manager",
    "aidlc-architect-agent": "solutions architect",
    "aidlc-aws-platform-agent": "cloud platform engineer",
    "aidlc-compliance-agent": "compliance officer",
    "aidlc-delivery-agent": "delivery lead",
    "aidlc-design-agent": "UX designer",
    "aidlc-developer-agent": "developer",
    "aidlc-pipeline-deploy-agent": "pipeline and release engineer",
    "aidlc-quality-agent": "QA lead",
    "aidlc-devsecops-agent": "security engineer",
    "aidlc-operations-agent": "site reliability engineer",
}
assert {s["lead"] for s in STAGES} | {a for s in STAGES for a in s["support"]} <= set(ROLE)

# What each stage produces, in one line (ours; the stage names are AI-DLC's).
WORK = {
    "workspace-scaffold": "make the record's folders",
    "workspace-detection": "look at the workspace: code or none, which repos, a pipeline or not",
    "state-init": "turn the scope and what detection found into the list of stages that run",
    "intent-capture": "restate the request: the problem, who has it, what success looks like",
    "market-research": "what others already do about it, and what that means for this request",
    "feasibility": "can it be built here: constraints, risks, rough effort",
    "scope-definition": "what is in, what is out, and why",
    "team-formation": "who is needed, and for which stages",
    "rough-mockups": "rough screens or API shapes to talk about",
    "approval-handoff": "one page for the sponsor to approve before Inception starts",
    "reverse-engineering": "a map of the existing code: modules, entry points, tests, how to build",
    "practices-discovery": "how this team builds, tests, reviews and ships today",
    "requirements-analysis": "numbered questions, then numbered requirements with their assumptions",
    "user-stories": "user stories with acceptance criteria",
    "refined-mockups": "the mockups, refined against the requirements",
    "domain-design": "the domain model: entities, rules, boundaries",
    "units-generation": "the work cut into units that can be built and reviewed one at a time",
    "contract-design": "the contracts between units and with other systems: APIs, events, schemas",
    "delivery-planning": "the order of the units, their branches, and who reviews what",
    "functional-design": "per unit: the logic, in enough detail to code from",
    "nfr-requirements": "per unit: performance, security, availability, compliance requirements",
    "nfr-design": "per unit: how the design meets those requirements",
    "infrastructure-design": "per unit: the cloud resources it needs",
    "code-generation": "the code and its tests, on the branch the plan named, until the team's check passes",
    "build-and-test": "build and test everything again, and map each requirement to a test",
    "ci-pipeline": "the CI pipeline that runs those checks on every push",
    "deployment-pipeline": "the pipeline that takes a build to each environment",
    "environment-provisioning": "the environments themselves",
    "deployment-execution": "the deployment, or the steps a person runs for it",
    "observability-setup": "logs, metrics, alarms and dashboards",
    "incident-response": "the runbook: what to do when the alarms fire",
    "performance-validation": "load and performance checks against the NFRs",
    "feedback-optimization": "what to improve next, from what production shows",
}
assert set(WORK) == set(SLUGS)

# How each AI-DLC stage becomes Archon nodes.
INIT_KIND = {"workspace-scaffold": "bash", "workspace-detection": "prompt", "state-init": "script"}
CODE = "code-generation"
# Runtime rules this workflow adds on top of the scope lists (both are what AI-DLC's engine does; see the AI-DLC course's runs).
NEEDS_CODE = {"reverse-engineering"}                       # skipped on a greenfield workspace
NEEDS_PIPELINE = {s["slug"] for s in STAGES if s["phase"] == "Operation"}  # skipped when the workspace has no pipeline


def key(slug):
    return slug.replace("-", "_")


def runs(scope, greenfield=False, has_pipeline=False):
    """The stages this workflow runs for a scope, by the same rule as its state-init script."""
    out = []
    for s in STAGES:
        if s["slug"] in INIT_KIND:
            out.append(s["slug"])
            continue
        on = s["slug"] in SCOPES[scope]
        if s["slug"] in NEEDS_CODE and greenfield:
            on = False
        if s["slug"] in NEEDS_PIPELINE and not has_pipeline:
            on = False
        if on:
            out.append(s["slug"])
    return out


def phase_check(phase):
    return f"{phase.lower()}-check"
