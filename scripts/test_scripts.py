"""Tests for the studio scripts. Run: python scripts/test_scripts.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_studio import AGENTS, CAPS, plan_minutes, split_frontmatter  # noqa: E402

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

print("ok")
