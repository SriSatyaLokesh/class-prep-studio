"""Generate .agents/agents/*.md (Antigravity) from .claude/agents/*.md (PRD 8.5). Never hand-edit the output.

Usage: python scripts/sync_agents.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_studio import AGENTS, CAPS, TOOLS, split_frontmatter  # noqa: E402


def antigravity_text(claude_text: str) -> str:
    fm, body = split_frontmatter(claude_text)
    name = fm["name"]
    tools = "".join(f"  - {t}\n" for c in CAPS[name] for t in TOOLS[c][1])
    return (f"---\nname: {name}\ndescription: {fm['description']}\ntools:\n{tools}"
            "subagent: true\nmainAgent: false\nmodel: inherit\ncommandExecutionPolicy: sandbox\n---\n" + body)


def main():
    root = Path(__file__).resolve().parent.parent
    out = root / ".agents/agents"
    out.mkdir(parents=True, exist_ok=True)
    for n in AGENTS:
        text = (root / f".claude/agents/{n}.md").read_text(encoding="utf-8")
        (out / f"{n}.md").write_text(antigravity_text(text), encoding="utf-8", newline="")
        print(f"wrote .agents/agents/{n}.md")


if __name__ == "__main__":
    main()
