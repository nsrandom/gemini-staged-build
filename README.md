# Antigravity Staged Build Plugin

A production-ready Google Antigravity and Antigravity CLI plugin that orchestrates development as a streamlined, staged, multi-model pipeline with strict separation of concerns, independent verification, and self-healing execution.

---

## Key Features

- **Progressive Specification:** High-level goals are architected into independently shippable stages ($\le 400$ diff lines each). Individual stage specs are written progressively and grounded in concise summaries of landed stages.
- **Comprehensive Test Coverage & Placement:** Stage architects design comprehensive test coverage, placing long-term useful tests into the project's main tests directory (creating it if needed).
- **Ephemeral Gitignored Scratchpad:** Isolates one-off exploratory verification code, experimental tests, and temporary databases in `specs/<feature>/scratchpad/`, ensuring internal data access without polluting production code or git history.
- **Universal Minor Decision Logging:** Captures minor decisions autonomously into single named places (constants, defaults, config keys) and logs them to `DECISIONS.md` during both `stage next` and `stage yolo`, enabling smooth implementation flow.
- **Interactive Cleanup & Remediation:** The `stage cleanup` command guides an interactive review of decisions (problem, decision taken, tradeoffs/alternatives/implications) with 5 user response paths, and automatically designs and executes a cleanup stage to apply remediations and delete scratchpads.
- **Unified Diff & Runtime Verification:** The `verifier` agent inspects the stage diff against acceptance contract criteria while actively executing verification commands and the project test suite via `run_command`.
- **Implementer Self-Healing:** Findings from failed verification runs route directly back to `implementer` for targeted root-cause self-healing, eliminating intermediary debugging hops.
- **Inter-Stage Context Bridging & Pruning:** Eliminates token bloat by pruning deep step details and raw diffs between stages, carrying forward only concise stage report summaries (~300–500 tokens).
- **Configurable Multi-Model Routing:** Dynamically routes subagents to model tiers configured per role in `pipeline.json` (defaults to `flash` across all roles for high speed and minimal latency).

---

## Directory Layout

```text
staged-build/ (Repository Root)
├── .gitignore                               # Ignore patterns (including specs/**/scratchpad/)
├── CHANGELOG.md                             # Release notes & version history
├── plugin.json                              # Plugin manifest
├── pipeline.json                            # Model routing configuration
├── README.md                                # This documentation
├── rules/
│   └── AGENTS.md                            # Rules: Orchestrator invariants, layout, branch policies, cleanup
└── skills/
    └── staged-build/
        ├── SKILL.md                         # Progressive skill definition & runbook
        ├── scripts/
        │   ├── context_resolver.py          # Fast VCS, scratchpad, & decision state inspector
        │   └── branch_helper.sh             # Feature branch, diff, gitignore & scratchpad helper
        └── references/
            ├── autonomy_policy.md           # Major vs minor decision rules, DECISIONS.md & cleanup protocol
            ├── roles.md                     # Role matrix & tool permissions
            └── agents/                      # Specialized subagent prompt definitions
                ├── plan_architect.md
                ├── stage_architect.md
                ├── implementer.md
                └── verifier.md
```

---

## Installation & Updates

### Option A: Workspace-Level Submodule (Recommended for Teams)
Add the plugin directly to your project's `.agents/plugins/` directory:
```bash
git submodule add https://github.com/nsrandom/gemini-staged-build.git .agents/plugins/staged-build
```

#### Updating Submodule
To pull the latest updates for an existing submodule:
```bash
git submodule update --remote .agents/plugins/staged-build
```

#### Reinstalling Submodule
If you want to perform a clean reinstall of the workspace submodule:
```bash
git submodule deinit -f .agents/plugins/staged-build 2>/dev/null || true
git rm -f .agents/plugins/staged-build 2>/dev/null || true
rm -rf .git/modules/.agents/plugins/staged-build .agents/plugins/staged-build
git submodule add https://github.com/nsrandom/gemini-staged-build.git .agents/plugins/staged-build
```

---

### Option B: Global Machine-Wide Installation
Make the plugin commands available across all workspaces on your machine:
```bash
git clone https://github.com/nsrandom/gemini-staged-build.git ~/.gemini/config/plugins/staged-build
```

#### Updating Global Installation
To pull the latest updates to your global installation:
```bash
cd ~/.gemini/config/plugins/staged-build && git pull
```

#### Reinstalling Global Installation
To perform a clean reinstall:
```bash
rm -rf ~/.gemini/config/plugins/staged-build
git clone https://github.com/nsrandom/gemini-staged-build.git ~/.gemini/config/plugins/staged-build
```

> [!TIP]
> After updating or reinstalling, restart or reload your Antigravity / IDE session to ensure newly updated plugin manifests, subagent prompts, rules, and skills take effect.

---

## Commands & Workflows

### 1. Plan a New Feature
```text
stage plan "Add OAuth2 authentication with refresh tokens"
```
Initiates an interactive, plan-first conversation:
1. `plan-architect` analyzes the codebase, flags unknowns (Stage 01 investigation), initializes `specs/<feature>/DECISIONS.md`, ensures `specs/**/scratchpad/` is in `.gitignore`, and directly writes `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md` to disk first.
2. The orchestrator presents the saved plan to the user for review.
3. User feedback and answers to open questions are updated in place directly in `specs/<feature>/` until approved.

### 2. Execute Next Stage
```text
stage next
```
Advances the first pending stage:
1. Verifies clean git working tree and ensures checkout of feature branch `<feature>` (never builds on `main`; prompts user to confirm reuse if `<feature>` branch already exists).
2. `stage-architect` directly creates `NN-slug.md` (contract) and `NN-slug.detail.md` (spec) on disk under `specs/<feature>/stages/`, grounded by prior stage report summaries for Stage $N > 1$. Ensures comprehensive test coverage in the project's tests directory, and isolates one-off checks in `specs/<feature>/scratchpad/`.
3. In non-yolo mode, the orchestrator displays and verifies the stage plan with the user before delegating to `implementer`.
4. `implementer` writes the code, adds long-term tests to the project tests directory, places throwaway code in `scratchpad/`, and records minor decisions into `specs/<feature>/DECISIONS.md`.
5. `verifier` inspects the diff against contract criteria and runs verification commands & project tests.
6. If verification detects issues, `implementer` performs self-healing fixes (max 2 cycles).
7. Generates `NN-slug.report.md`, marks stage `done`, suggests commit message (`<feature>-stage-<num>: <title>`), and stops.

### 3. Run Unattended (YOLO Mode)
```text
stage yolo
```
Runs every stage end-to-end:
- Ensures development occurs on `<feature>` branch (confirms reuse if branch already exists).
- `stage-architect` writes stage specs directly to disk.
- Autonomously decides minor questions and logs them to `specs/<feature>/DECISIONS.md`.
- Automatically commits passing stages (`<feature>-stage-<num>: <title>`).
- Prunes previous stage implementation details and logs between stages to maintain a lightweight prompt context.
- Halts only for major architectural decisions, unrecoverable failures, or `REPLANNED` stage contracts.
- Automatically transitions to `stage cleanup` when all stages finish.

### 4. Interactive Decision Walkthrough & Cleanup
```text
stage cleanup
```
Reviews decisions and executes cleanup:
1. Goes through decisions in `specs/<feature>/DECISIONS.md` one by one, explaining:
   - **The Problem**
   - **What Decision Was Taken** (with file:line location)
   - **Tradeoffs, Alternatives & Implications**
2. User chooses: `confirm`, `reject the decision`, `defer`, `ask a follow up question`, or `suggest a modification`.
3. Deferred decisions are evaluated at the end of the loop.
4. If any decisions were rejected or modified, or if `specs/<feature>/scratchpad/` exists:
   - Automatically creates a new cleanup stage in `STATE.md`.
   - Starts design and implementation of the cleanup stage (`stage-architect` $\to$ `implementer` $\leftrightarrow$ `verifier` $\to$ commit).
   - Deletes `specs/<feature>/scratchpad/` and temporary data, remediates decisions, and verifies all tests pass.

### 5. Check Status
```text
stage status
```
Displays current plan progress, active branch, decision summary, scratchpad status, and the most recent stage report.

### 6. Redo Active Stage
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
