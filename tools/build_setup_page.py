"""Build archon-workspace-setup.html: install Archon, connect Claude Code, prepare one repo, and know every file.

Real output from: tools/data/cli/install.txt (the installer), cli.json (capture_cli.py), home-config.yaml, inventory.json,
archon-hello-world-java/java-run/setup-steps.json (setup_java_run.py), tools/data/setup/bash-probe.json and serve.json,
img/webui-*.png (screenshots of the real Web UI, display paths mapped). The team's files are tools/data/java/files/.

Usage: py -3.12 tools/build_setup_page.py
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pagekit import (DOC, E, REAL, ROOT, card, disk, io, note, page, phase, plain, rail, scrub, see, step, strip_ansi,  # noqa: E402
                     table, tabs, write, you)
from team_files import writes  # noqa: E402

DATA = ROOT / "tools" / "data"
CLI = json.loads((DATA / "cli" / "cli.json").read_text(encoding="utf-8"))
VERSION = re.search(r"Archon CLI v([\d.]+)", CLI["version"]["out"]).group(1)
INSTALL = scrub(strip_ansi((DATA / "cli" / "install.txt").read_text(encoding="utf-8-sig")))
HOMECFG = scrub((DATA / "cli" / "home-config.yaml").read_text(encoding="utf-8"))
INV = json.loads((DATA / "cli" / "inventory.json").read_text(encoding="utf-8"))
SETUP = {s["label"]: s for s in json.loads((ROOT / "archon-hello-world-java/java-run/setup-steps.json").read_text(encoding="utf-8"))}
RUNSTEPS = {s["label"]: s for s in json.loads((ROOT / "archon-hello-world-java/java-run/steps.json").read_text(encoding="utf-8"))}
PROBE = json.loads((DATA / "setup" / "bash-probe.json").read_text(encoding="utf-8"))
SERVE = json.loads((DATA / "setup" / "serve.json").read_text(encoding="utf-8-sig"))
HEALTH = json.loads(SERVE["health"])
FILES = DATA / "java" / "files"
TEAM = sorted((p.relative_to(FILES).as_posix(), p.read_text(encoding="utf-8")) for p in FILES.rglob("*") if p.is_file())
TEAM = [(p, t) for p, t in TEAM]
assert VERSION == "0.13.2" and "Checksum verified" in INSTALL and "Providers installed: claude" in INSTALL
assert "All checks passed." in CLI["doctor"]["out"]
assert SETUP["validate"]["exit"] == 0 and "request-to-pr" in SETUP["validate"]["stdout"]
assert len(TEAM) == 9, [p for p, _ in TEAM]
assert HEALTH["status"] == "ok" and HEALTH["version"] == VERSION


def x(s):
    return E(s)


def dirs_win(paths):
    ds = sorted({str(Path(p).parent).replace("/", "\\") for p in paths if "/" in p})
    return "New-Item -ItemType Directory -Force " + ", ".join(ds) + " | Out-Null"


def dirs_mac(paths):
    return "mkdir -p " + " ".join(sorted({str(Path(p).parent.as_posix()) for p in paths if "/" in p}))


team_paths = [p for p, _ in TEAM]
WRITE_WIN = dirs_win(team_paths) + "\n" + writes([(p, t) for p, t in TEAM if not p.endswith(".cmd")])
WRITE_MAC = dirs_mac(team_paths) + "\n" + writes([(p, t) for p, t in TEAM if not p.endswith(".cmd")], mac=True) + "\nchmod +x scripts/verify.sh"
# verify.cmd needs CRLF; it is written by its own short command on Windows and is not needed on macOS
WRITE_WIN += "\n[IO.File]::WriteAllText(\"$PWD\\scripts\\verify.cmd\", \"@echo off`r`nrem Windows twin of verify.sh, for running the checks by hand in cmd or PowerShell.`r`ncd /d `\"%~dp0..`\" && mvn -q test`r`n\")"

S = []
S.append(step(1, "Once per machine", "--setup", "install", "Install Archon and an agent",
              "One binary, plus the agent it drives. Archon brings no model: it runs Claude Code (or Codex, Pi) with your own login.", "Kiran · 5 min",
              table(["You need", "Why", "Check"], [
                  ["Claude Code, signed in", "the agent every AI node runs", "<code>claude --version</code>, then <code>claude</code> once to sign in"],
                  ["git", "worktrees, branches; on Windows also Git Bash, which runs every <code>bash:</code> node", "<code>git --version</code>"],
                  ["JDK 21 + Maven 3.9", "only for this course's Java repo", "<code>java -version</code> shows 21"]])
              + io(you("irm https://archon.diy/install.ps1 | iex", "curl -fsSL https://archon.diy/install | bash", "PowerShell", "Terminal"),
                   see(x(INSTALL.strip()), f"Windows · Archon {VERSION} · real, run with -Providers claude", "The installer returns"), stack=True)
              + note("The installer downloads the release binary, verifies its SHA-256 against the release's <code>checksums.txt</code>, copies it to <code>~/.archon/bin</code>, adds that folder to your <b>user</b> PATH (open a new terminal to pick it up) and asks which providers to add. To skip the question: <code>&amp; ([scriptblock]::Create((irm https://archon.diy/install.ps1))) -Providers claude</code> on Windows, <code>curl -fsSL https://archon.diy/install | bash -s -- --providers claude</code> on macOS. Homebrew: <code>brew install coleam00/archon/archon</code>.")
              + plain("A provider is a plug that fits Archon to one agent. Installing the plug doesn't install the agent: Claude Code must already be on the machine and signed in.")))

S.append(step(2, "Once per machine", "--setup", "check", "Check the install: version and doctor",
              "Two commands that tell you everything is wired before you spend a token.", "Kiran · 1 min",
              io(you("archon version\narchon doctor", None, "any shell"),
                 see(x(CLI["version"]["out"].strip() + "\n\n" + CLI["doctor"]["out"].strip()), "real", "Archon returns"))
              + table(["Line", "What it means"], [
                  ["<code>claude: Claude binary … (via autodetect, spawns OK)</code>", "Archon found Claude Code and started it"],
                  ["<code>Assistant login: claude: usable</code>", "Claude Code's own login (claude.ai) works; no API key needed"],
                  ["<code>Database: reachable (sqlite)</code>", "<code>~/.archon/archon.db</code>; set <code>DATABASE_URL</code> for PostgreSQL"],
                  ["<code>Bundled defaults: 25 workflow(s), 27 command(s)</code>", "the sdlc pack inside the binary"],
                  ["<code>○</code> lines", "optional pieces not set up (GitHub App, chat platforms, the Archon skill): fine for this course"]], "kv")
              + note("<b>Keep API keys out of it.</b> If <code>ANTHROPIC_API_KEY</code> is set in your shell, Claude Code (and so every Archon run) may use that key instead of your claude.ai login. The course cleared it for every run: <code>$env:ANTHROPIC_API_KEY=$null</code> in PowerShell, <code>unset ANTHROPIC_API_KEY</code> on macOS.")))

S.append(step(3, "Once per machine", "--setup", "privacy", "Turn telemetry off (or decide to keep it)",
              "Archon sends anonymous usage events by default. Know that before your first run.", "Kiran · 1 min",
              io(you("[Environment]::SetEnvironmentVariable('ARCHON_TELEMETRY_DISABLED', '1', 'User')\n$env:ARCHON_TELEMETRY_DISABLED = '1'\narchon telemetry status",
                     "echo 'export ARCHON_TELEMETRY_DISABLED=1' >> ~/.zshrc\nexport ARCHON_TELEMETRY_DISABLED=1\narchon telemetry status", "PowerShell", "Terminal"),
                 see(x(re.sub(r"Distinct ID: .*", "Distinct ID: (a random install id)", CLI["telemetry"]["out"].strip())), "real", "Archon returns"))
              + note("Per the docs, what is sent is categorical: bundled workflow names (your own workflows report as <code>custom</code>), node counts, provider and model ids, outcome, durations and usage totals. Never code, prompts, file paths or your workflow names. <code>DO_NOT_TRACK=1</code> works too. The course ran with it off.")))

S.append(step(4, "Once per machine", "--setup", "Windows only", "Windows: make sure Archon finds Git Bash",
              "Every bash: node and every until_bash check runs under bash, on Windows too. Archon looks for Git Bash in the usual places only.", "Kiran · 1 min",
              f"<p>On this machine Git for Windows was on another drive. A one-node workflow showed what happens; <code>archon validate</code> does <b>not</b> catch it:</p>"
              + tabs("probe", [("bash-probe.yaml", ".archon/workflows/bash-probe.yaml", "a one-node test", "yaml", PROBE["workflow"])])
              + io(see(x(scrub(PROBE["without"])), "real · without ARCHON_BASH_PATH", "Archon returns"),
                   you("[Environment]::SetEnvironmentVariable('ARCHON_BASH_PATH', 'D:\\Program Files\\Git\\bin\\bash.exe', 'User')", None, "PowerShell · only if Git is elsewhere"))
              + note("Archon checks <code>%ProgramFiles%\\Git\\bin\\bash.exe</code>, <code>%ProgramFiles%\\Git\\usr\\bin\\bash.exe</code>, the x86 Program Files, <code>%LOCALAPPDATA%\\Programs\\Git\\bin\\bash.exe</code> and scoop. With <code>ARCHON_BASH_PATH</code> set, the same probe printed <code>Workflow completed successfully.</code> macOS and Linux use the <code>bash</code> on PATH.")))

S.append(step(5, "The repo", "--plan", "clone", "Clone the starter repo",
              "The same Spring Boot API as the AI-DLC course, at v1.0.2: the code before the change.", "Kiran · 1 min",
              io(you("cd C:\\work\ngit clone --single-branch --no-tags https://github.com/varasrinivas/aidlc-priorauth-api priorauth-api\ncd priorauth-api",
                     "cd ~/work\ngit clone --single-branch --no-tags https://github.com/varasrinivas/aidlc-priorauth-api priorauth-api\ncd priorauth-api", "PowerShell", "Terminal"),
                 see("Cloning into 'priorauth-api'...\ndone.", "real · the course cloned a local copy of the same repo", "git returns"))
              + note("<code>--no-tags</code> leaves out the <code>v1.1.0</code> tag, the answer key: an agent that scans the repo would otherwise find it. There is no workspace folder to make: <b>for a one-repo change the repo is the project</b>, and Archon registers it on the first run. A feature across several repos uses a <i>folder project</i> around them instead, the counterpart of the AI-DLC workspace (<a href='archon-introduction.html#s07'>introduction, step 7</a>).")))

S.append(step(6, "The repo", "--plan", "ours", "Write the team's files",
              "Nine small files the team owns: the workflow and its two prompts, Archon's repo config, the agent's rules, the one check, the request.", "Kiran · 3 min",
              io(you(x(WRITE_WIN), x(WRITE_MAC), "PowerShell, from priorauth-api", "Terminal, from priorauth-api"), stack=True)
              + tabs("team", [(Path(p).name, p, "", "yaml" if p.endswith(".yaml") else "md" if p.endswith(".md") else "bash", t) for p, t in TEAM])
              + table(["File", "What it is for"], [
                  ["<code>.archon/workflows/team/request-to-pr/request-to-pr.yaml</code>", "the team's process: 15 nodes, 4 waits for people"],
                  ["<code>…/commands/scan.md</code>, <code>implement.md</code>", "the prompts of the <code>scan</code> node and each <code>implement</code> pass"],
                  ["<code>.archon/config.yaml</code>", "<code>assistant: claude</code>; runs branch from <code>main</code>"],
                  ["<code>CLAUDE.md</code>", "the agent's standing rules; Claude Code reads it in every AI node"],
                  ["<code>scripts/verify.sh</code> (+ <code>verify.cmd</code>)", "the one check: the implement loop ends when it exits 0"],
                  ["<code>.gitattributes</code>", "keeps <code>verify.sh</code> LF: a worktree is a fresh checkout, and with <code>core.autocrlf=true</code> bash would get CRLF and fail"],
                  ["<code>docs-in/request.md</code>", "Ravi's request, named in the run message"]], "kv")
              + plain("The workflow is the recipe, <code>CLAUDE.md</code> the kitchen rules every cook reads, and <code>verify.sh</code> the thermometer: the dish is done when it says so, not when the cook thinks so.")))

S.append(step(7, "The repo", "--plan", "check before spending", "Validate the workflow, then dry-run it",
              "Two free checks: the file parses and its references resolve; the graph walks the way you think.", "Kiran · 1 min",
              io(you("archon validate workflows request-to-pr", None, "any shell"),
                 see(x(SETUP["validate"]["stdout"].strip()), "real", "Archon returns"))
              + io(you('archon workflow run request-to-pr --dry-run --default-stubs "Implement the request in docs-in/request.md"', None, "any shell"),
                   see(x(RUNSTEPS["dry-run"]["stdout"].split("STUBBED   scan")[0].strip() + "\nSTUBBED   scan (command)\n…\nSTUBBED   questions (prompt)\n…\nPAUSED    answer (wait) — durable wait\n…\nSimulation outcome: paused"), "real · no run, no model call", "Archon returns"))
              + note("Run with no name, <code>archon validate workflows</code> also checks the 25 bundled ones; on Windows 24 of them warn <code>Runtime 'bun' is not available on PATH</code> for their <code>script:</code> nodes. In the course run the bundled <code>archon-plan</code> and <code>archon-implement</code> ran their script nodes anyway; install <a href=\"https://bun.sh\">Bun</a> if a bundled workflow's script node fails.")))

S.append(step(8, "The repo", "--plan", "ours", "Commit the team's files",
              "Worktrees are cut from the branch, so a run only sees what is committed.", "Kiran · 1 min",
              io(you("git add -A\ngit status --short\ngit commit -m \"Add the team's Archon files: CLAUDE.md, verify scripts, request-to-pr workflow\"\ngit push origin main", None, "any shell"),
                 see(x(SETUP["team-files"]["stdout"].strip()), "real · git status --short", "git returns"))
              + note("If the run must see a file that is git-ignored (a <code>.env</code>, local fixtures), list it under <code>worktree.copyFiles</code> in <code>.archon/config.yaml</code>; anything that needs installing goes in <code>worktree.postCreate</code>. This repo needs neither.")
              + io(you("./scripts/verify.sh", "./scripts/verify.sh", "Git Bash", "Terminal"),
                   see("…\nverify: passed", "real · at v1.0.2, before the change", "bash returns"))))

S.append(step(9, "First run", "--build", "the Web UI", "Open the Web UI",
              "The same runs as the CLI, with the graph, the log, the artifacts and approve/reject buttons.", "Kiran · 2 min",
              io(you("archon serve", None, "any shell · leave it running"),
                 see("server_listening  port 3090  hostname 0.0.0.0\nserver_ready      activePlatforms: [\"Web\"]\n\nGET /api/health →\n" + x(json.dumps({k: HEALTH[k] for k in ("status", "adapter", "version", "activePlatforms", "runningWorkflows")})),
                     "real · from the server's log and /api/health", "Archon returns"))
              + '<figure class="dia"><img src="img/webui-runs.png" alt="Archon Web UI: the priorauth-api project with the course\'s three runs" style="width:100%;border-radius:10px;border:1px solid var(--line)"><figcaption>The project page after the course run: request-to-pr (cancelled at the last gate), archon-implement (the fix), archon-plan (the comparison). Real screenshot; display paths mapped.</figcaption></figure>'
              + '<figure class="dia"><img src="img/webui-graph.png" alt="Archon Web UI: the graph of the request-to-pr run" style="width:100%;border-radius:10px;border:1px solid var(--line)"><figcaption>The run page\'s Graph tab for request-to-pr. Log and Artifacts are the other tabs.</figcaption></figure>'
              + note("<b>It listens on every interface (0.0.0.0), and a solo install has no login.</b> On a shared network, anyone who can reach port 3090 can see and answer your runs: keep a firewall on, or set up the docs' authentication before using it anywhere but your own laptop. The first <code>archon serve</code> downloads the server (92 MB) and the web UI (1.8 MB) into <code>~/.archon/server/</code> and <code>~/.archon/web-dist/</code>, checksums verified; <code>archon serve --download-only</code> does just that.")))

S.append(step(10, "First run", "--build", "ours", "Where pull requests come from",
              "Archon's own workflow can push a branch. Opening and merging the PR is a forge's job: gh, or a forge plugin.", "Kiran · reference",
              table(["Who opens the PR", "What it needs", "In this course"], [
                  ["You, by hand", "nothing", f"the course's way: the run pushes (or Kiran does), Kiran opens the PR {REAL}"],
                  ["The bundled <code>archon-pr</code> / <code>archon-ship</code>", "<code>gh auth login</code> (default), or <code>ARCHON_SDLC_FORGE=forge</code> + <code>archon plugin add coleam00/Archon/plugins/forge-github</code>", DOC],
                  ["Queues (<code>archon-intake</code> → <code>build-queue</code> → <code>merge-queue</code>)", "gh, a maintainers file on the default branch, CI checks on PRs", DOC]])
              + see(x(RUNSTEPS["complete"]["stderr"].split("{")[0].strip()), "real · archon complete, with no gh login", "Archon returns")
              + note("Without a <code>gh</code> login Archon still works; it only skips what needs GitHub, and says so (here <code>archon complete</code> skipped its open-PR check).")))

STEPS = [(1, "Install Archon"), (2, "version and doctor"), (3, "Telemetry"), (4, "Windows: Git Bash"),
         (5, "Clone the starter"), (6, "Write the team's files"), (7, "Validate, dry-run"), (8, "Commit"),
         (9, "Open the Web UI"), (10, "Where PRs come from")]
PH = {n: ("Once per machine", "--setup") for n in (1, 2, 3, 4)} | {n: ("The repo", "--plan") for n in (5, 6, 7, 8)} | {n: ("First run", "--build") for n in (9, 10)}

# ---------- reference ----------
top = collections.Counter()
for f in INV:
    parts = f["path"].split("/")
    key = parts[0] if len(parts) == 1 else parts[0] + "/" + (parts[1] if parts[0] in ("workspaces", "plugins", "server", "web-dist", "cache") and len(parts) > 2 else "")
    top[key] += 1
HOME_WHAT = {"bin/": "the CLI binary", "plugins/": "provider plugins and their install receipts", "config.yaml": "your defaults (all commented out at first)",
             "install.json": "which binary and version", "archon.db": "SQLite: projects, runs, events, sessions, costs", "archon.db-shm": "SQLite working file",
             "archon.db-wal": "SQLite write-ahead log", "workspaces/": "one folder per project: worktrees, logs, artifacts, state", "server/": "the Web UI server, downloaded by archon serve",
             "web-dist/": "the Web UI files", "cache/": "bundled workflows' scripts, unpacked", "logs/": "output of detached runs", "tier-notice.json": "remembers that the tier notice was shown",
             "update-check.json": "last update check"}
rows = []
for k, n in sorted(top.items()):
    base = k.split("/")[0] + ("/" if "/" in k else "")
    rows.append([f"<code>{x(k if k.endswith('/') or '/' not in k else k)}</code>", str(n), HOME_WHAT.get(base, "")])
ref_home = card("home", "~/.archon, folder by folder", f"<p>Every file under <code>~/.archon</code> after the course (install, three runs, the Web UI), counted by <code>capture_cli.py</code> ({len(INV)} files, real). Nothing here is committed.</p>"
                + table(["Path", "Files", "What it is"], rows, "kv"))
ref_cfg = card("config", "The two config.yaml files", "<p>Archon reads the repo's <code>.archon/config.yaml</code> over your <code>~/.archon/config.yaml</code>. The home one, as the installer wrote it (real):</p>"
               + tabs("cfg", [("~/.archon/config.yaml", "~/.archon/config.yaml", "written by the install · real", "yaml", HOMECFG),
                              ("repo .archon/config.yaml", ".archon/config.yaml", "the team's · committed", "yaml", (FILES / ".archon/config.yaml").read_text(encoding="utf-8"))]))
real = card("real", "What is real here", f"<p>Every output on this page is real, from Archon {VERSION} on Windows 10 (3 Nov 2026): the installer, <code>version</code>, <code>doctor</code>, <code>telemetry status</code>, the Git Bash probe, the clone, <code>validate</code>, the dry run, <code>git status</code>, <code>verify.sh</code>, <code>archon serve</code> and the Web UI screenshots. macOS commands are the documented equivalents and were not run. Items marked {DOC} are from the docs. The cast is fictional.</p>")

hero = f'''<section class="hero" id="top">
  <div>
    <h1>Set up Archon for a repo, and know what every file is for.</h1>
    <p class="lead">Install once per machine, then add nine small files to the repo: that is the whole setup. This page does both on the course's Spring Boot repo with real output from Archon {VERSION}, including the two Windows snags the course hit. Next: <a href="archon-hello-world-java/archon-hello-world-java-run.html">run one request through it</a>.</p>
    <div class="facts">
      <div><b>1</b>install command, checksum verified</div>
      <div><b>1</b>provider: Claude Code, your login</div>
      <div><b>9</b>team files, committed</div>
      <div><b>0</b>workspace folders for one repo: the repo is the project</div>
      <div><b>{len(INV)}</b>files under ~/.archon after the course</div>
      <div><b>3090</b>the Web UI's port</div>
    </div>
  </div>
  <aside class="slack" aria-label="Two places">
    <div class="slack__bar"><span>Two places</span><span>Archon {VERSION}</span></div>
    <div class="slack__body">
      <p style="margin:0 0 8px"><b>The repo, <code>.archon/</code></b><br><span style="color:var(--ink-3)">The team's workflows, prompts and config. Committed; every clone gets them.</span></p>
      <p style="margin:0 0 8px"><b>Beside it</b><br><span style="color:var(--ink-3)">CLAUDE.md for the agent, scripts/verify.sh for the check, docs-in/ for requests.</span></p>
      <p style="margin:0"><b>Your home, <code>~/.archon/</code></b><br><span style="color:var(--ink-3)">The binary, plugins, the database, and every run's worktree, transcript and artifacts. Never committed.</span></p>
    </div>
  </aside>
</section>
'''
main = (hero + phase("--setup", "Once per machine", "steps 1–4 · install, check, telemetry, Windows") + "".join(S[0:4])
        + phase("--plan", "The repo", "steps 5–8 · clone, write the team's files, check them, commit") + "".join(S[4:8])
        + phase("--build", "First run", "steps 9–10 · the Web UI, and where PRs come from") + "".join(S[8:10])
        + phase("--review", "Reference", "~/.archon and the config files") + ref_home + ref_cfg + real)
footer = (f'<footer class="foot">Set up Archon · Archon {VERSION} · next: <a href="archon-hello-world-java/archon-hello-world-java-run.html">the hello-world run</a> · '
          '<a href="archon-introduction.html">introduction</a> · <a href="index.html">all course pages</a> · <a href="#top">Back to top</a></footer>\n')
html_ = page("Set Up Archon for a Repo", f"Install Archon {VERSION}, connect Claude Code, and prepare a repo for it: every command and every file, with real output on Windows and the macOS equivalents.",
             "Archon setup", "install · the repo's files · real output", len(STEPS),
             rail(STEPS, PH, [("home", "~/.archon folder by folder"), ("config", "The config.yaml files"), ("real", "What is real here")]), main, footer)
write(ROOT / "archon-workspace-setup.html", html_)
