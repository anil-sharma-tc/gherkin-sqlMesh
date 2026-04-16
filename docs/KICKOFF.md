# Kickoff Prompt for Claude Code (Sonnet)

Copy-paste the block below into Claude Code on the web (claude.ai/code), pointed at this repo. Use **Claude Sonnet 4.6** for the work — it's the right cost/quality point for a project like this, with Opus available for hard debugging if you hit a wall.

---

## The Prompt

```
I'm building gherkin-sqlmesh, a compiler that turns Gherkin .feature files into
native SQLMesh test YAML and audit SQL files.

Before writing any code, read these three files end-to-end and confirm you understand
the rules:

1. CLAUDE.md  — the TDD discipline you MUST follow. Red-Green-Refactor every time.
2. README.md  — what the project does and the input/output shape.
3. docs/EXECUTION_PLAN.md  — the staged roadmap. We will execute stages in order.

Then:

Step 1: Run Stage 0 (environment bootstrap) and confirm the dev environment is
working. Report back when pytest runs cleanly on zero tests.

Step 2: Stop and wait for my go-ahead before starting Stage 1.

Important rules for this session:
- Do NOT write any implementation code before its test exists and fails.
- One Red-Green-Refactor cycle per commit.
- If you catch yourself about to write a function without a failing test, stop
  and write the test first.
- After every file edit the PostToolUse hook runs pytest automatically — pay
  attention to its output.
- If a stage's task list feels too big for one cycle, break it into smaller cycles.
  Never batch multiple untested changes.
```

---

## How to Run This

### Option A — Claude Code on the web (recommended for this project)

1. Push this scaffold to a GitHub repo (public or private).
2. Go to **claude.ai/code**.
3. Click **"New task"** and connect the repo.
4. Select **Claude Sonnet 4.6** as the model.
5. Paste the prompt above.
6. Let it run Stage 0. Review. Approve Stage 1. Continue stage by stage.

Cloud sessions keep running when you close the tab, which is ideal for the longer stages.

### Option B — Claude Code locally

```bash
# Install Claude Code if you haven't
curl -fsSL https://claude.ai/install.sh | bash

# From this repo's root
cd gherkin-sqlmesh
claude
```

Then paste the prompt. The `.claude/settings.json` hook will auto-run pytest after every edit.

### Option C — Terminal, headless (for CI or batch work)

```bash
claude -p "$(cat docs/KICKOFF.md)" --model sonnet-4.6
```

---

## Model Choice Guidance

| Task | Model |
|---|---|
| Stages 1–6 (clear spec, iterative TDD) | **Sonnet 4.6** — fast, cheap, plenty capable |
| Stage 7 (real SQLMesh integration debugging) | Sonnet 4.6 first; escalate to Opus 4.7 if stuck |
| Reviewing and refactoring after each milestone | Opus 4.7 for one pass, then back to Sonnet |

Sonnet will breeze through the well-specified stages. The execution plan is deliberately written so there's no ambiguity — each task has a test name and an expected outcome. That's where Sonnet shines.

---

## What Good Progress Looks Like

After Stage 1 you should see:
- `src/gherkin_sqlmesh/parser.py` with `Feature`, `Scenario`, `Step` dataclasses and a `parse()` function.
- `tests/test_parser.py` with ~5 tests, all passing.
- `tests/fixtures/features/` with 3–5 small `.feature` files used by the tests.
- A handful of commits labeled `red:`, `green:`, `refactor:`.

If you see a single giant commit that introduces the whole parser at once, **stop the session** and push back. That's the failure mode the CLAUDE.md guardrails are designed to prevent.

---

## If Claude Skips TDD

Likely causes and fixes:

| Symptom | Fix |
|---|---|
| Writes implementation before the test | Remind it: "Revert that. Per CLAUDE.md, write the failing test first." |
| Writes multiple tests in one go | "One test at a time. Red, then green, then the next red." |
| "Fixes" failing tests by changing assertions | "Don't modify the test to match the code. Understand why it fails first." |
| Claims a test is "trivial" and skips it | "Per CLAUDE.md, trivial tests still get written. Please add it." |

Consider installing **TDD Guard** (https://github.com/nizos/tdd-guard) if you want hard enforcement via hooks rather than prompt-level discipline.
