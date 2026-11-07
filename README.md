# Class Prep Studio

Class Prep Studio prepares one 50-minute first-year lecture for you. You give it a topic, a textbook chapter and a syllabus unit. It gives back a matching class pack. You approve the plan before anything is built, and you approve the pack before anyone sees it.

## What it makes

| File | What it is |
|---|---|
| `outputs/plan.md` | A one-page lesson plan: objectives, timings, examples, questions to raise |
| `outputs/slides.pptx` | 10 to 14 slides with speaker notes |
| `outputs/qna.md` | 10 to 15 questions students may ask, with model answers |
| `outputs/quiz.md` | 10 practice questions with an answer key and explanations |
| `outputs/student-notes.pdf` | A student handout with key ideas, worked examples, a flowchart and an infographic |
| `review.md` | What the reviewer found, what was fixed, and anything left open |
| `status.md` | Which steps are done and which gates you approved |

Every step writes a file in this folder, so you can open and read any step yourself. The studio never emails, uploads or shares anything.

## What you need

- **One of these:** Claude Code (the command line, or the **Code** tab in the Claude Desktop app), the Antigravity CLI, or the Antigravity App version 2.5 or later.
- **Python 3.11 or later** and **Node.js 20 or later.**
- **Your two PDFs:** a textbook chapter you own and the syllabus unit with its course outcomes.

These do **not** work: the regular Claude chat, the Antigravity IDE, and headless runs (`claude -p` or Antigravity headless mode). They cannot load the studio's agents, or cannot stop at the approval gates.

## One-time setup

**1. Install Python and Node.js** if you don't have them. One example line for each system:

| System | Python | Node.js |
|---|---|---|
| Windows | `winget install Python.Python.3.12` | `winget install OpenJS.NodeJS.LTS` |
| macOS | `brew install python node` | (same line) |
| Linux | `sudo apt install python3 python3-pip nodejs npm` | (same line) |

**2. Install the packages.** In this folder, run:

```
python -m pip install -r requirements.txt
npm install
```

Or skip this and let `/setup-studio` do it. It asks you once before installing.

**3. Install the skills.** Open this folder in your tool and type `/setup-studio`. It downloads the seven skills listed in `skill-sources.json`, checks Python, Node.js and the packages, and shows a table of what it did. If you forget, `/prep-class` runs the same steps on its first run.

**4. Start a new session.** New skills and agents may only appear in a fresh session. In the Antigravity CLI you can type `/skills reload` instead.

## Put your PDFs here

| File | Put it at |
|---|---|
| Textbook chapter | `inputs/textbook-chapter.pdf` |
| Syllabus unit | `inputs/syllabus-unit.pdf` |

Use exactly these names. Your PDFs are git-ignored, so they are never committed.

To try the studio without your own files, run `python scripts/make_sample_inputs.py`. It makes two made-up sample PDFs on Ohm's law and Kirchhoff's laws. It never overwrites a file that is already there, so delete the samples before you copy your own PDFs in.

## Run it

Type `/prep-class` and then your topic. You can add what students usually get wrong:

```
/prep-class Ohm's law and Kirchhoff's laws. Students mix up series and parallel circuits.
```

Where to type it:

- **Claude Code CLI:** open a terminal in this folder, start `claude`, and type the command.
- **Claude Desktop, Code tab:** open the Code tab, choose this folder, and type the command.
- **Antigravity CLI:** start the CLI in this folder and type the command.
- **Antigravity App (v2.5+):** open this folder and type the command in the chat.

If you forget the topic, the studio asks for it. If a PDF is missing, it stops and tells you which file to put where.

## What happens, step by step

1. **Questions.** The studio asks you up to 6 numbered questions: your students' branch, how deep to go, where they struggle, what to stress, which examples you like, and what to leave out. Each comes with a suggested answer. Reply "yes" to accept all of them, or answer the ones you want to change. It writes your answers to `brief.md`.
2. **Research.** Three helpers read the textbook, search the web, and read the syllabus at the same time.
3. **Debate.** A "confused student" and an "expert" go back and forth for 3 rounds, recorded in `debate.md`.
4. **Plan.** A planner writes `outputs/plan.md`. Where the textbook and the web disagree, the plan shows both. You decide.

**Gate 1: approve the plan.** The studio shows you the full plan and stops. Reply **"approved"** to build the class pack, or say what to change. It rewrites the plan and asks again. Nothing else is built until you approve.

5. **Build.** Slides, Q&A and quiz are built together, then the student notes.
6. **Review.** A reviewer checks every file: citations, quiz answers, reading level, no copying from the textbook, course outcomes covered, and that all files agree. Each problem gets one fix pass. Anything still open is listed under "Unresolved" in `review.md`.

**Gate 2: approve the pack.** The studio shows `review.md` and the list of files, then stops. Reply **"approved"** to finish, or say what to change. Only the affected files are rebuilt and checked again. If a problem is in the plan itself, you can go back to Gate 1 or accept it as is. Nothing has been shared with anyone at this point, and the studio never shares anything after it either.

## Permission prompts you'll see

**Claude Code.** The file `.claude/settings.json` is part of this folder. It pre-allows web search, web page reading, writing and editing files, and running `python`, `py`, `node`, `npm install` and `markitdown`. **This means the studio can run Python and Node commands in this folder without asking you.** The PowerShell rules in that file repeat the Bash rules on purpose, so Windows works the same way. Anything else still asks. When it asks about something in this folder, approving it is fine.

**Antigravity.** It asks you to approve each web page the studio reads. That is expected. Commands run in a sandbox.

## Resume or start over

You can close the session at either gate and come back later. When you type `/prep-class` again with the same topic, the studio reads `status.md` and asks: *Resume from <next step>, or start over?*

Starting over moves every generated file into `archive/<date-time>/` first. Nothing is deleted.

## Adding a skill

Add one entry to `skill-sources.json` with the skill's `name`, `repo`, `path` and `ref` (a full 40-character commit ID, never a branch name). Then type `/setup-studio`. No code changes are needed.

## Troubleshooting

- **A builder's `node` or `python` command fails in Antigravity.** The sandbox may be blocking it. For that one agent only, open its file in `.agents/agents/` (for example `.agents/agents/slides-builder.md`) and change `commandExecutionPolicy: sandbox` to `commandExecutionPolicy: auto`. Leave every other agent on `sandbox`. This is a local change: `python scripts/check_studio.py` will report that file as different, and `python scripts/sync_agents.py` puts it back to `sandbox`.
- **`review.md` says the render check was skipped.** LibreOffice is not installed, so the slides were not turned into pictures for a visual check. The deck is still built and checked in other ways. Install LibreOffice if you want the visual check.
- **The studio stops on a PDF.** Your PDF is probably a scan with no text layer. The studio cannot read it, so it stops. Use a PDF where you can select the text, or run it through OCR first.
- **A skill fails to install.** The `/setup-studio` table shows the manual fix: download the repository at that commit and copy the skill folder into `.claude/skills/<name>/`.
- **`/prep-class` does not appear.** Start a new session. In the Antigravity CLI, type `/skills reload`.

## For maintainers

- `python scripts/check_studio.py` checks the project structure. `python scripts/check_studio.py --run` also checks a run stopped at Gate 1.
- `python scripts/test_scripts.py` tests the helper scripts. It prints `ok`.
- Never hand-edit `.agents/agents/`. Edit `.claude/agents/` and run `python scripts/sync_agents.py`.
- The design is in `docs/PREP_CLASS_PRD.md`.

## Human-verified checklist

- [ ] Fresh Claude Code session: run the test in PRD §13.2 to Gate 1; `python scripts/check_studio.py --run` passes.
- [ ] Antigravity CLI: `/agents` lists all 11 agents with no warnings, `/skills` lists all 7 installed skills plus `prep-class` and `setup-studio` with no warnings, `/prep-class` appears, and a run reaches Gate 1.
- [ ] Antigravity App: `/prep-class` appears in the slash command list and starts the grill step.
- [ ] Claude Desktop, Code tab: `/prep-class` appears and starts the grill step.
- [ ] One full run to Gate 2 on real PDFs, then open the deck in PowerPoint and the notes in a PDF viewer.
