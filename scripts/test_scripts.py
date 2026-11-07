"""Tests for the studio scripts. Run: python scripts/test_scripts.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_studio import AGENTS, CAPS, plan_minutes, run_checks, split_frontmatter  # noqa: E402

fm, body = split_frontmatter("---\nname: student\ntools: Read, Edit\nskills:   # c\n  - pdf\n---\n# Role\nx\n")
assert fm == {"name": "student", "tools": "Read, Edit", "skills": ["pdf"]}
assert body == "# Role\nx\n"

flow = "## Flow\n| Minutes | Activity | Content | Source tags |\n|---|---|---|---|\n| 10 | a | b | [TB p.1] |\n| 40 | c | d | [CO-1] |\n\n## Examples\n"
assert plan_minutes(flow) == 50
try:
    plan_minutes(flow.replace("| 10 |", "| 5–7 |"))
    assert False
except ValueError as e:
    assert "5–7" in str(e)
assert len(AGENTS) == 11 and set(CAPS) == set(AGENTS)

fm, _ = split_frontmatter("---\nname: x\ndescription: Uses C# and a # sign\nskills:   # c\n  - pdf\n---\n")
assert fm == {"name": "x", "description": "Uses C# and a # sign", "skills": ["pdf"]}

# --run against a minimal valid run fixture
FILES = {
    "status.md": "Topic: T\n- [x] Brief — 2026-11-07 10:00\n- [ ] Gate 1 approved\n- [ ] Gate 2 approved\n",
    "brief.md": "# Brief: T\n- Students: a\n- Depth: intro\n- Known struggles: b\n- Emphasise: c\n- Examples to use: d\n- Leave out: nothing\n",
    "research/textbook.md": "## Key ideas\n- x [TB p.1]\n## Definitions\n- y [TB p.2]\n## Worked examples\n- z [TB p.3]\n## Common errors\n- w [TB p.4]\n",
    "research/web.md": "## Examples and applications\n- a [WEB-1]\n## References\n1. t — http://x — accessed 2026-11-07\n",
    "research/syllabus.md": "## Course outcomes\nCO-1: one\nCO-2: two\n## Must cover\n- a [CO-1]\n",
    "debate.md": "# Debate: T\n" + "".join(
        f"\n## Round {i}\n**Student:** q?\n\n**Expert:** a. Sources: [TB p.1]\n" for i in (1, 2, 3)),
    "outputs/plan.md": "## Objectives\n- a [CO-1]\n- b [CO-2]\n## Flow\n| Minutes | Activity | Content | Source tags |\n"
                       "|---|---|---|---|\n| 10 | a | b | [TB p.1] |\n| 40 | c | d | [CO-1] |\n"
                       "## Examples\nx\n## Questions to raise in class\nx\n## Conflicts between sources\nNone found\n",
}
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for rel, text in FILES.items():
        (root / rel).parent.mkdir(exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    assert run_checks(root) == [], run_checks(root)
    (root / "outputs/.gitkeep").write_text("")
    assert run_checks(root) == []
    (root / "outputs/quiz.md").write_text("x")
    assert len(run_checks(root)) == 1, run_checks(root)


# pdf_text / make_sample_inputs / check_copy
import subprocess  # noqa: E402
import make_sample_inputs  # noqa: E402
from check_copy import overlaps  # noqa: E402
from pdf_text import page_texts  # noqa: E402

make_sample_inputs.main()  # inputs/*.pdf are git-ignored; no overwrite
src = "the current through a conductor is directly proportional to the voltage across it at constant temperature"
assert overlaps(src, "we know " + src) != []
eleven = " ".join(src.split()[:11])
assert overlaps(src, eleven + " banana") == []
assert overlaps("the \ufb01rst connec-\ntion " + src, "the first connection " + src)  # Review Focus 2
pages = page_texts(Path("inputs/textbook-chapter.pdf"))
assert len(pages) == 5 and all(p.strip() for p in pages)

from reportlab.pdfgen import canvas  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    blank = Path(tmp) / "blank.pdf"
    c = canvas.Canvas(str(blank))
    c.showPage()
    c.save()
    script = Path(__file__).resolve().parent / "pdf_text.py"
    r = subprocess.run([sys.executable, str(script), str(blank)], capture_output=True, text=True)
    assert r.returncode == 2 and "no text layer" in r.stderr, (r.returncode, r.stderr)  # Review Focus 1

print("ok")
