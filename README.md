# Antigravity Staged Build Plugin

A production-ready Google Antigravity and Antigravity CLI plugin that orchestrates development as a streamlined, staged, multi-model pipeline with strict separation of concerns, independent verification, and self-healing execution.

---

## Key Features

- **Progressive Specification:** High-level goals are architected into independently shippable stages ($\le 400$ diff lines each). Individual stage specs are written progressively and grounded in concise summaries of landed stages.
- **Unified Diff & Runtime Verification:** The `verifier` agent inspects the stage diff against acceptance contract criteria while actively executing verification commands and the project test suite via `run_command`.
- **Implementer Self-Healing:** Findings from failed verification runs route directly back to `implementer` for targeted root-cause self-healing, eliminating intermediary debugging hops.
- **Inter-Stage Context Bridging & Pruning:** Eliminates token bloat by pruning deep step details and raw diffs between stages, carrying forward only concise stage report summaries (~300–500 tokens).
- **Configurable Multi-Model Routing:** Dynamically routes subagents to model tiers configured per role in `pipeline.json` (defaults to `flash` across all roles for high speed and minimal latency).
- **Supervised & Autonomous Modes:** Run one stage at a time with `stage next`, or execute entire feature plans end-to-end with `stage yolo`.

---

## Directory Layout

```text
staged-build/ (Repository Root)
├── .gitignore                               # Ignore patterns
├── CHANGELOG.md                             # Release notes & version history
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
                ├── implementer.md
                └── verifier.md
```

---

## Installation

### Option A: Workspace-Level Submodule (Recommended for Teams)
Add the plugin directly to your project's `.agents/plugins/` directory:
```bash
git submodule add https://github.com/nsrandom/gemini-staged-build.git .agents/plugins/staged-build
```

### Option B: Global Machine-Wide Installation
Make the plugin commands available across all workspaces on your machine:
```bash
git clone https://github.com/nsrandom/gemini-staged-build.git ~/.gemini/config/plugins/staged-build
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
2. `stage-architect` creates `NN-slug.md` (contract) and `NN-slug.detail.md` (spec), grounded by prior stage report summaries for Stage $N > 1$.
3. `implementer` writes the code.
4. `verifier` inspects the diff against contract criteria and runs verification commands & project tests.
5. If verification detects issues, `implementer` performs self-healing fixes (max 2 cycles).
6. Generates `NN-slug.report.md`, marks stage `done`, and stops.

### 3. Run Unattended (YOLO Mode)
```text
stage yolo
```
Runs every stage end-to-end:
- Autonomously decides minor questions and logs them to `specs/<feature>/DECISIONS.md`.
- Automatically commits passing stages (`stage NN: <title>`).
- Prunes previous stage implementation details and logs between stages to maintain a lightweight prompt context.
- Halts only for major architectural decisions, unrecoverable failures, or `REPLANNED` stage contracts.
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

```json
{
  "plan-architect": "flash",
  "stage-architect": "flash",
  "implementer": "flash",
  "verifier": "flash"
}
```

The supported model options for each role are:
- `flash`: Fast, cost-effective, high-throughput model tier (default for all roles).
- `pro`: Advanced reasoning model tier for complex planning or heavy architectural reviews.
- `flash_lite`: Lightweight tier for fast lookups.
- `inherit`: Inherits the active model currently selected in your parent session.

---

## License

MIT
