# Antigravity Staged Build Plugin

A production-ready Google Antigravity and Antigravity CLI plugin that orchestrates development as a staged, multi-model pipeline with strict separation of concerns, independent falsification, and black-box verification.

---

## Key Features

- **Progressive Specification:** High-level goals are architected into independently shippable stages ($\le 400$ diff lines each), and individual stage specs are written only after prior stages land.
- **Pre-Implementation Falsification:** The `plan-checker` agent validates all signatures, reachability, criteria coverage, and verification commands against the live codebase before an implementer writes any code.
- **Independent Black-Box Validation:** The `validator` agent is provided **ONLY the acceptance contract (`NN-slug.md`)** with zero inherited bias, verifying actual runtime behavior and test suite execution.
- **Configurable Multi-Model Routing:** Dynamically routes subagents to model tiers configured per role in `pipeline.json`.
- **Supervised & Autonomous Modes:** Run one stage at a time with `stage next`, or execute entire feature plans end-to-end with `stage yolo`.

---

## Directory Layout

```text
staged-build/ (Repository Root)
├── .gitignore                               # Ignore patterns
├── plugin.json                              # Plugin manifest
├── pipeline.json                            # Model routing configuration
├── README.md                                # This documentation
├── rules/
│   └── AGENTS.md                            # Rules: Orchestrator invariants, layout, branch policies
└── skills/
    └── staged-build/
        ├── SKILL.md                         # Progressive skill definition & runbook
        ├── scripts/
        │   ├── context_resolver.py          # Fast VCS & plan state inspector
        │   └── branch_helper.sh             # Feature branch & stage diff helper
        └── references/
            ├── autonomy_policy.md           # Major vs minor decision rules & DECISIONS.md schema
            ├── roles.md                     # Role matrix & tool permissions
            └── agents/                      # Specialized subagent prompt definitions
                ├── plan_architect.md
                ├── stage_architect.md
                ├── plan_checker.md
                ├── implementer.md
                ├── reviewer.md
                ├── validator.md
                └── debugger.md
```

---

## Installation

### Option A: Workspace-Level Submodule (Recommended for Teams)
Add the plugin directly to your project's `.agents/plugins/` directory:
```bash
git submodule add https://github.com/<username>/staged-build.git .agents/plugins/staged-build
```

### Option B: Global Machine-Wide Installation
Make the plugin commands available across all workspaces on your machine:
```bash
git clone https://github.com/<username>/staged-build.git ~/.gemini/config/plugins/staged-build
```

---

## Commands & Workflows

### 1. Plan a New Feature
```text
stage plan "Add OAuth2 authentication with refresh tokens"
```
Initiates a 2-pass interactive planning conversation:
1. `plan-architect` analyzes the codebase, flags unknowns (Stage 01 investigation), and presents a proposal.
2. Interactive refinement via `ask_question` and dialogue.
3. On approval, writes `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md`.

### 2. Execute Next Stage
```text
stage next
```
Advances the first pending stage:
1. Verifies clean git working tree and ensures `staged-build/<feature>` branch checkout.
2. `stage-architect` creates `NN-slug.md` (contract) and `NN-slug.detail.md` (spec).
3. `plan-checker` verifies whole stage plan and all `[large]` steps.
4. `implementer` writes the code.
5. `reviewer` reviews diff against contract.
6. `validator` runs black-box verification with isolated contract.
7. Generates `NN-slug.report.md`, marks stage `done`, and stops.

### 3. Run Unattended (YOLO Mode)
```text
stage yolo
```
Runs every stage end-to-end:
- Autonomously decides minor questions and logs them to `specs/<feature>/DECISIONS.md`.
- Automatically commits passing stages (`stage NN: <title>`).
- Halts only for major architectural decisions or pipeline errors.
- Concludes with an interactive decision review.

### 4. Check Status
```text
stage status
```
Displays current plan progress, active branch, and the most recent stage report.

### 5. Redo Active Stage
```text
stage redo
```
Safely resets current stage modifications and restarts execution.

---

## Model Configuration

Subagent routing is stored in `pipeline.json`. To override routing for a specific project, create `.agents/pipeline.json` in your project root.

The supported model options for each role are:
- `pro`: Advanced reasoning model tier for architecture, plan checking, code review, and root-cause debugging.
- `flash`: Fast, high-throughput model tier for implementation and test execution.
- `inherit`: Inherits the active model currently selected in your parent session. When you select a specific model version (such as Gemini 3.7 Flash) in your chat or environment settings, any role set to `inherit` will run with that exact model.

---

## License

MIT

