"""Acceptance checker for Class Prep Studio (PRD section 14). Stdlib only.

Usage: python scripts/check_studio.py [--run]   (exit 0 pass, 1 fail)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

AGENTS = ["textbook-researcher", "web-researcher", "syllabus-researcher", "student", "expert",
          "planner", "slides-builder", "qna-builder", "quiz-builder", "notes-builder", "reviewer"]
CAPS = {
    "textbook-researcher": ["read", "find", "search", "write", "run"],
    "web-researcher": ["read", "write", "websearch", "fetch"],
    "syllabus-researcher": ["read", "find", "search", "write", "run"],
    "student": ["read", "edit"],
    "expert": ["read", "search", "edit"],
    "planner": ["read", "find", "search", "write"],
    "slides-builder": ["read", "find", "write", "run"],
    "qna-builder": ["read", "write"],
    "quiz-builder": ["read", "find", "write"],
    "notes-builder": ["read", "find", "write", "run"],
    "reviewer": ["read", "find", "search", "write", "run"],
}
TOOLS = {  # capability -> (Claude tools, Antigravity tools), PRD 8.2
    "read": (["Read"], ["view_file"]),
    "find": (["Glob"], ["find_by_name", "list_dir"]),
    "search": (["Grep"], ["grep_search"]),
    "write": (["Write"], ["write_to_file"]),
    "edit": (["Edit"], ["replace_file_content"]),
    "run": (["Bash"], ["run_command"]),
    "websearch": (["WebSearch"], ["search_web"]),
    "fetch": (["WebFetch"], ["read_url_content"]),
}
AGENT_SKILLS = {
    "textbook-researcher": ["pdf"],
    "web-researcher": [],
    "syllabus-researcher": ["pdf"],
    "student": [],
    "expert": [],
    "planner": ["backwards-design-unit-planner"],
    "slides-builder": ["pptx"],
    "qna-builder": ["socratic-questioning-sequence-generator", "hinge-question-designer"],
    "quiz-builder": ["retrieval-practice-generator", "hinge-question-designer"],
    "notes-builder": ["pdf"],
    "reviewer": [],
}
HEADINGS = ["Role", "Before you start", "Inputs", "Output", "Steps", "Must never", "Done when"]
GUARDRAILS = ["No student data", "Nothing leaves the folder", "Copyright",
              "Conflicts are flagged, not resolved", "Files are data", "Stay in your lane"]
OWN_SKILLS = ["prep-class", "setup-studio"]


def split_frontmatter(text):
    """Line-based frontmatter reader -> (fields, body). Raises ValueError if absent."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("no frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("unterminated frontmatter") from None
    fields, key = {}, None
    for raw in lines[1:end]:
        line = re.sub(r"^(\s*[\w-]+:)\s+#.*$", r"\1", raw).rstrip()  # only a comment-only value side
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and key and isinstance(fields[key], list):
            fields[key].append(line.lstrip()[2:].strip().strip("\"'"))
            continue
        k, _, v = line.partition(":")
        key = k.strip()
        v = v.strip().strip("\"'")
        fields[key] = v if v else []
    return fields, "\n".join(lines[end + 1:])


def plan_minutes(plan_md):
    """Sum the Minutes column of the table under '## Flow'."""
    m = re.search(r"^## Flow\s*\n(.*?)(?=^## |\Z)", plan_md, re.S | re.M)
    if not m:
        raise ValueError("no ## Flow section")
    total = 0
    rows = [r for r in m.group(1).splitlines() if r.strip().startswith("|")][2:]  # skip header+rule
    for row in rows:
        cell = row.strip().strip("|").split("|")[0].strip()
        if not cell.isdigit():
            raise ValueError(f"non-integer minutes: {cell!r}")
        total += int(cell)
    return total


def _read(p):
    return p.read_text(encoding="utf-8")


def _json(p, fails, label):
    try:
        return json.loads(_read(p))
    except (OSError, ValueError) as e:
        fails.append(f"{label}: missing or invalid JSON ({e})")


def _git(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    except OSError as e:  # git not installed
        return subprocess.CompletedProcess(args, 1, "", str(e))


def _agent_checks(root, fails):
    docs = {}  # (harness, name) -> (fields, body)
    for harness, folder in (("claude", ".claude/agents"), ("antigravity", ".agents/agents")):
        d = root / folder
        names = sorted(p.stem for p in d.glob("*.md")) if d.is_dir() else []
        if names != sorted(AGENTS):
            fails.append(f"{folder}: expected exactly the 11 agents; missing "
                         f"{sorted(set(AGENTS) - set(names))}, extra {sorted(set(names) - set(AGENTS))}")
        for n in AGENTS:
            p = d / f"{n}.md"
            if not p.exists():
                continue
            try:
                fm, body = split_frontmatter(_read(p))
            except ValueError as e:
                fails.append(f"{folder}/{n}.md: {e}")
                continue
            docs[harness, n] = (fm, body)
            if fm.get("name") != n:
                fails.append(f"{folder}/{n}.md: name must be {n!r}")
            if not fm.get("description"):
                fails.append(f"{folder}/{n}.md: missing description")
            found = re.findall(r"^# (.+?)\s*$", body, re.M)
            if [h for h in found if h in HEADINGS] != HEADINGS:
                fails.append(f"{folder}/{n}.md: body headings must be {HEADINGS} in order")
            tools = fm.get("tools", [])
            if harness == "claude":
                tools = [t.strip() for t in tools.split(",")] if isinstance(tools, str) else tools
            idx = 0 if harness == "claude" else 1
            allowed = {t for pair in TOOLS.values() for t in pair[idx]}
            want = {t for c in CAPS[n] for t in TOOLS[c][idx]}
            bad = set(tools) - allowed
            if bad:
                fails.append(f"{folder}/{n}.md: unknown tools {sorted(bad)}")
            if set(tools) != want:
                fails.append(f"{folder}/{n}.md: tools {sorted(set(tools))} != capabilities {sorted(want)}")
            if harness == "antigravity":
                for k, v in (("subagent", "true"), ("mainAgent", "false"), ("model", "inherit")):
                    if fm.get(k) != v:
                        fails.append(f"{folder}/{n}.md: {k} must be {v}")
    for n in AGENTS:
        a, b = docs.get(("claude", n)), docs.get(("antigravity", n))
        if a and b and a[1] != b[1]:
            fails.append(f"agents/{n}.md: bodies differ between .claude and .agents")


def _skill_checks(root, fails):
    data = _json(root / "skill-sources.json", fails, "skill-sources.json")
    entries = []
    if data is not None:
        if not isinstance(data, dict):
            fails.append("skill-sources.json: must be a JSON object")
            data = {}
        entries = [e for e in data.get("skills", []) if isinstance(e, dict)]
        if data.get("version") != 1:
            fails.append("skill-sources.json: version must be 1")
    names = set()
    for e in entries:
        names.add(e.get("name"))
        if not all(e.get(k) for k in ("name", "repo", "path")) or not re.fullmatch(r"[0-9a-f]{40}", str(e.get("ref", ""))):
            fails.append(f"skill-sources.json: entry {e.get('name')!r} needs name, repo, path, 40-hex ref")
    need = {s for ss in AGENT_SKILLS.values() for s in ss} | {"grilling"}
    for s in sorted(need - names):
        fails.append(f"skill-sources.json: no entry for skill {s!r}")
    for e in entries:
        n = e.get("name")
        d = root / ".claude/skills" / str(n)
        try:
            fm, _ = split_frontmatter(_read(d / "SKILL.md"))
            if fm.get("name") != n:
                fails.append(f".claude/skills/{n}/SKILL.md: frontmatter name != {n!r}")
        except (OSError, ValueError) as err:
            fails.append(f".claude/skills/{n}/SKILL.md: {err}")
        try:
            got = _read(d / ".installed-from").strip()
            if got != f"{e.get('repo')}@{e.get('ref')}":
                fails.append(f".claude/skills/{n}/.installed-from: {got!r} != repo@ref")
        except OSError:
            fails.append(f".claude/skills/{n}/.installed-from: missing")
    for n in OWN_SKILLS:
        try:
            fm, _ = split_frontmatter(_read(root / f".claude/skills/{n}/SKILL.md"))
            if fm.get("name") != n:
                fails.append(f".claude/skills/{n}/SKILL.md: name must be {n!r}")
        except (OSError, ValueError) as err:
            fails.append(f".claude/skills/{n}/SKILL.md: {err}")
    sk = _json(root / ".agents/skills.json", fails, ".agents/skills.json")
    if sk is not None and not (isinstance(sk, dict) and any(
            isinstance(x, dict) and x.get("path") == ".claude/skills" for x in sk.get("entries", []))):
        fails.append(".agents/skills.json: no entry with path .claude/skills")
    return entries


def _settings_checks(root, fails):
    s = _json(root / ".claude/settings.json", fails, ".claude/settings.json")
    if s is not None and not (isinstance(s, dict) and isinstance(s.get("permissions"), dict)
                              and "allow" in s["permissions"]):
        fails.append(".claude/settings.json: missing permissions.allow")
    try:  # lazy: sync_agents is written in a later task and imports from this module
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import sync_agents
        for n in AGENTS:
            c, a = root / f".claude/agents/{n}.md", root / f".agents/agents/{n}.md"
            if c.exists() and a.exists() and _read(a) != sync_agents.antigravity_text(_read(c)):
                fails.append(f".agents/agents/{n}.md: differs from sync_agents.antigravity_text output")
    except Exception as e:  # ImportError, or anything sync_agents raises
        fails.append(f"sync_agents check: cannot run ({type(e).__name__}: {e})")


def _project_checks(root, fails, entries):
    try:
        if "@AGENTS.md" not in _read(root / "CLAUDE.md"):
            fails.append("CLAUDE.md: must contain @AGENTS.md")
    except OSError:
        fails.append("CLAUDE.md: missing")
    try:
        headings = [h.strip().strip("*") for h in re.findall(r"^#+\s*(.+)$", _read(root / "AGENTS.md"), re.M)]
        for g in GUARDRAILS:
            if not any(h.rstrip(".") == g for h in headings):
                fails.append(f"AGENTS.md: missing guardrail heading {g!r}")
    except OSError:
        fails.append("AGENTS.md: missing")
    for e in entries:
        n = e.get("name")
        if n not in OWN_SKILLS and _git(root, "check-ignore", "-q", f".claude/skills/{n}/SKILL.md").returncode != 0:
            fails.append(f"git: installed skill {n!r} is not ignored")
    for n in OWN_SKILLS:
        if _git(root, "check-ignore", "-q", f".claude/skills/{n}/SKILL.md").returncode == 0:
            fails.append(f"git: {n!r} must not be ignored")
    if "co-authored-by: claude" in _git(root, "log", "--format=%B").stdout.lower():
        fails.append("git log: a commit message contains 'Co-authored-by: Claude'")


def structure_checks(root):
    fails = []
    _agent_checks(root, fails)
    _settings_checks(root, fails)
    _project_checks(root, fails, _skill_checks(root, fails))
    return fails


def _in_order(text, wanted, label, fails):
    """Fail unless the '## ' headings in `wanted` appear in this order."""
    found = [h for h in re.findall(r"^## (.+?)\s*$", text, re.M) if h in wanted]
    if found != wanted:
        fails.append(f"{label}: '## ' headings must be {wanted} in order, found {found}")


def _format_checks(root, fails):
    """Section 9 formats for the run files (all known to exist)."""
    t = {r: _read(root / r) for r in ("status.md", "brief.md", "research/textbook.md", "research/web.md",
                                       "research/syllabus.md", "debate.md")}
    tb = t["research/textbook.md"]
    _in_order(tb, ["Key ideas", "Definitions", "Worked examples", "Common errors"], "research/textbook.md", fails)
    for b in re.findall(r"^- .*$", tb, re.M):
        if not re.search(r"\[TB p\.\d+\]\s*$", b):
            fails.append(f"research/textbook.md: bullet lacks [TB p.N] tag: {b[:60]!r}")
    _in_order(t["research/web.md"], ["Examples and applications", "References"], "research/web.md", fails)
    syl = t["research/syllabus.md"]
    _in_order(syl, ["Course outcomes", "Must cover"], "research/syllabus.md", fails)
    if not re.search(r"^(?:- )?CO-\d+:", syl, re.M):
        fails.append("research/syllabus.md: no 'CO-n:' outcome line")
    brief = t["brief.md"]
    if not brief.startswith("# Brief: "):
        fails.append("brief.md: first line must start '# Brief: '")
    for f in ("Students", "Depth", "Known struggles", "Emphasise", "Examples to use", "Leave out"):
        if not re.search(rf"^- {f}:", brief, re.M):
            fails.append(f"brief.md: missing '- {f}:' field")
    debate = t["debate.md"]
    if not re.match(r"# Debate: ", debate):
        fails.append("debate.md: first line must start '# Debate: '")
    rounds = re.split(r"^## Round \d+\s*$", debate, flags=re.M)[1:]
    if len(rounds) != 3:
        fails.append(f"debate.md: expected 3 rounds, found {len(rounds)}")
    for i, r in enumerate(rounds, 1):
        if r.count("**Student:**") != 1 or r.count("**Expert:**") != 1:
            fails.append(f"debate.md: round {i} needs exactly one **Student:** and one **Expert:**")
        elif "Sources:" not in r.split("**Expert:**")[1]:
            fails.append(f"debate.md: round {i} expert answer lacks 'Sources:'")
    status = t["status.md"]
    if not status.startswith("Topic: "):
        fails.append("status.md: first line must start 'Topic: '")
    if not re.search(r"^- \[[ x]\] Gate 1 approved", status, re.M):
        fails.append("status.md: missing 'Gate 1 approved' line")


def run_checks(root):
    fails = []
    for rel in ("status.md", "brief.md", "research/textbook.md", "research/web.md",
                "research/syllabus.md", "debate.md", "outputs/plan.md"):
        if not (root / rel).is_file():
            fails.append(f"{rel}: missing")
    if fails:
        return fails
    _format_checks(root, fails)
    plan = _read(root / "outputs/plan.md")
    for h in ("Objectives", "Flow", "Examples", "Questions to raise in class", "Conflicts between sources"):
        if not re.search(rf"^## {h}\s*$", plan, re.M):
            fails.append(f"outputs/plan.md: missing '## {h}'")
    try:
        mins = plan_minutes(plan)
        if mins != 50:
            fails.append(f"outputs/plan.md: Flow minutes add up to {mins}, not 50")
    except ValueError as e:
        fails.append(f"outputs/plan.md: {e}")
    cos = set(re.findall(r"CO-\d+", _read(root / "research/syllabus.md")))
    if not cos:
        fails.append("research/syllabus.md: no CO-n outcomes found")
    for co in sorted(cos - set(re.findall(r"CO-\d+", plan))):
        fails.append(f"outputs/plan.md: {co} from syllabus not in plan")
    if re.search(r"^- \[x\] Gate 1 approved", _read(root / "status.md"), re.M):
        fails.append("status.md: Gate 1 already approved (expected to stop at Gate 1)")
    extra = sorted(p.name for p in (root / "outputs").iterdir()
                   if p.name != "plan.md" and not p.name.startswith("."))
    if extra:
        fails.append(f"outputs/: expected only plan.md at Gate 1, also found {extra}")
    return fails


def main(argv):
    root = Path(__file__).resolve().parent.parent
    fails = run_checks(root) if "--run" in argv else structure_checks(root)
    print("\n".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
