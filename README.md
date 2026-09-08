# Antigravity Staged Build Plugin

A production-ready Google Antigravity and Antigravity CLI plugin that orchestrates development as a streamlined, staged, multi-model pipeline with strict separation of concerns, independent verification, and self-healing execution.

---

## Key Features

- **Progressive Specification:** High-level goals are architected into independently shippable stages ($\le 400$ diff lines each). Individual stage specs are written progressively and grounded in concise summaries of landed stages.
- **Ephemeral Stage Runner Sub-Orchestrator:** Delegates single-stage execution to an ephemeral `stage-runner` sub-orchestrator. This isolates intermediate implementation and verification transcripts, keeping the Root Orchestrator lean ($\le 15$K tokens) across arbitrarily large multi-stage projects.
- **Role-Specific Compact Payloads & Disk Offloading:** Subagents write exhaustive test transcripts, diff breakdowns, and file logs directly to disk (`stages/NN-slug.report.md`, `NN-slug.verification.log`), returning strictly bounded structured payloads (`implementer` $\le 350$, `stage-architect` $\le 350$, `verifier` $\le 300$, `stage-runner` $\le 800$ tokens) to caller prompts to eliminate quadratic $O(N^2)$ token re-transmission.
- **Implementer Turn Ceilings & Checkpoint Relay Protocol:** Enforces a strict ceiling of 25 planner turns (hard max 30) on `implementer`. At turn 20, if thrashing or incomplete, the implementer writes `NN-slug.wip.md` and terminates with `STATUS: RELAY_REQUIRED`, prompting `stage-runner` to spawn a fresh, clean-slate implementer (~3k context vs 100k+).
- **Stage-Boundary Context Reset in YOLO Mode:** Clears root conversational context between stages in unattended YOLO mode, reinitializing with lean state (`SESSION_STATE.json`, `STATE.md`, `DECISIONS.md`, and prior report summary) to prevent 100+ turn accumulation traps.
- **Unified Feature `architecture.md` Synthesis:** Automatically synthesizes a single, permanent system reference (`specs/<feature>/architecture.md`, $\le 1,000\text{--}1,500$ tokens) at feature completion directly from confirmed disk metadata, eliminating downstream exploration taxes for future features.
- **Persistent Runtime State (`SESSION_STATE.json`):** Persists discovered environment paths, test shortcuts, sandbox preferences, and virtualenvs to disk, enabling safe context resets without operational amnesia.
- **Tiered Decision Cleanup & Batch Review:** Classifies minor decisions into Tier 1 (Routine Conventions) and Tier 2 (Substantive Architecture/Behavior). In `stage cleanup`, Tier 1 decisions are reviewed in a single consolidated batch modal/table (*"Confirm All N"*), cutting late-session conversation turns by ~90% and saving ~12M prompt tokens.
- **Comprehensive Test Coverage & Placement:** Stage architects design comprehensive test coverage, placing long-term useful tests into the project's main tests directory (creating it if needed).
- **Ephemeral Gitignored Scratchpad:** Isolates one-off exploratory verification code, experimental tests, and temporary databases in `specs/<feature>/scratchpad/`, ensuring internal data access without polluting production code or git history.
- **Universal Minor Decision Logging:** Captures minor decisions autonomously into single named places (constants, defaults, config keys) with Tier tags and logs them to `DECISIONS.md` during both `stage next` and `stage yolo`.
- **Unified Diff & Runtime Verification:** The `verifier` agent inspects the stage diff against acceptance contract criteria while actively executing verification commands and the project test suite via `run_command`, writing outputs to `.verification.log`.
- **Implementer Self-Healing:** Findings from failed verification runs route directly back to `implementer` for targeted root-cause self-healing, eliminating intermediary debugging hops.
- **Configurable Multi-Model Routing:** Dynamically routes subagents to model tiers configured per role in `pipeline.json` (defaults to `flash` across all roles for high speed and minimal latency).

---

## Directory Layout

```text
staged-build/ (Repository Root)
├── .gitignore                               # Ignore patterns (including specs/**/scratchpad/)
├── CHANGELOG.md                             # Release notes & version history
├── plugin.json                              # Plugin manifest (v1.6.0)
├── pipeline.json                            # Model routing configuration
├── README.md                                # This documentation
├── rules/
│   └── AGENTS.md                            # Rules: Orchestrator invariants, layout, branch policies, cleanup
└── skills/
    └── staged-build/
        ├── SKILL.md                         # Progressive skill definition & runbook
        ├── scripts/
        │   ├── analyze_tokens.py            # Token & telemetry analyzer CLI script
        │   ├── context_resolver.py          # Fast VCS, session state, scratchpad, & decision inspector
        │   └── branch_helper.sh             # Feature branch, diff, gitignore & scratchpad helper
        └── references/
            ├── autonomy_policy.md           # Major vs minor decision tiers, DECISIONS.md & cleanup protocol
            ├── roles.md                     # Role matrix & tool permissions
            └── agents/                      # Specialized subagent prompt definitions
                ├── plan_architect.md
                ├── stage_runner.md
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
1. `plan-architect` analyzes the codebase, flags unknowns (Stage 01 investigation), initializes `specs/<feature>/DECISIONS.md` and `specs/<feature>/SESSION_STATE.json`, ensures `specs/**/scratchpad/` is in `.gitignore`, and directly writes `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md` to disk first.
2. The orchestrator presents the saved plan to the user for review.
3. User feedback and answers to open questions are updated in place directly in `specs/<feature>/` until approved.

### 2. Execute Next Stage
```text
stage next
```
Advances the first pending stage:
1. Verifies clean git working tree and ensures checkout of feature branch `<feature>` (never builds on `main`; prompts user to confirm reuse if `<feature>` branch already exists).
2. Persists detected virtualenv paths, test runner shortcuts, and sandbox settings to `specs/<feature>/SESSION_STATE.json`.
3. Invokes ephemeral `stage-runner` to coordinate the single stage lifecycle:
   - `stage-architect` writes `NN-slug.md` (contract) and `NN-slug.detail.md` (spec) on disk, returning compact summary ($\le 350$ tokens).
   - In non-yolo mode, `stage-runner` displays and verifies the stage plan with the user.
   - `implementer` writes code, adds long-term tests to project test directory, isolates scratch checks in `scratchpad/`, operates within a 25-turn ceiling (spawning clean-slate relay if thrashing at turn 20 via `NN-slug.wip.md`), writes full evidence to disk, and returns a compact structured YAML payload ($\le 350$ tokens).
   - `verifier` independently inspects diff and executes tests with `run_command`, writing full output to `NN-slug.verification.log` and returning a concise checklist ($\le 300$ tokens).
   - On `VERDICT: FAIL`, `implementer` self-heals (max 2 cycles).
   - On `VERDICT: PASS`, commits stage (`<feature>-stage-<num>: <title>`), cleans up `wip.md`, and finalizes `NN-slug.report.md`.
4. `stage-runner` returns a compact stage summary ($\le 800$ tokens) to the Root Orchestrator and terminates. Root marks stage `done` in `STATE.md` and stops.

### 3. Run Unattended (YOLO Mode)
```text
stage yolo
```
Runs every stage end-to-end:
- Ensures development occurs on `<feature>` branch (confirms reuse if branch already exists).
- **Stage-Boundary Context Reset:** Clears Root Orchestrator conversational context between stages, reloading only `SESSION_STATE.json`, `STATE.md`, `DECISIONS.md`, and the prior stage report summary.
- Runs an isolated ephemeral `stage-runner` for each stage (with checkpoint relay handling).
- Minor decisions are resolved autonomously into single named places with Tier tags and logged to `specs/<feature>/DECISIONS.md`.
- Automatically commits passing stages (`<feature>-stage-<num>: <title>`).
- Intermediate step breakdowns, raw diffs, and test outputs remain inside the terminated `stage-runner`, preventing context accumulation in the Root Orchestrator.
- Halts only for major architectural decisions, unrecoverable failures, or `REPLANNED` stage contracts.
- Automatically resets context and transitions to `stage cleanup` when all stages finish.

### 4. Interactive Decision Walkthrough & Cleanup
```text
stage cleanup
```
Reviews decisions with minimum token overhead, executes cleanup, and synthesizes `architecture.md`:
1. **Context Reset:** Clears conversational history, reloading ONLY `SESSION_STATE.json`, `SPEC.md`, `STATE.md`, `DECISIONS.md`, and the `scratchpad/` listing (reducing context from ~160K tokens to ~10K tokens).
2. **Tier 1 Consolidated Batch Review:** Presents all routine Tier 1 decisions in a single consolidated modal/table:
   > *"N routine decisions followed standard codebase conventions (see table). [Confirm All N (Recommended)] or [Select specific decision to inspect]."*
3. **Tier 2 (and Flagged) Targeted Walkthrough:** Walks through substantive Tier 2 decisions and flagged items one by one (Problem, Decision taken with `Change it here: path/to/file:line`, Tradeoffs/alternatives/implications). User choices: `confirm`, `reject the decision`, `defer`, `ask a follow up question`, or `suggest a modification`.
4. Deferred decisions are evaluated at the end of the loop.
5. If any decisions were rejected or modified, or if `specs/<feature>/scratchpad/` exists:
   - Automatically creates a new cleanup stage in `STATE.md`.
   - Executes the cleanup stage via `stage-runner` (`stage-architect` $\to$ `implementer` $\leftrightarrow$ `verifier` $\to$ commit).
   - Deletes `specs/<feature>/scratchpad/` and temporary data, remediates decisions, and verifies all tests pass.
6. **Unified Feature `architecture.md` Synthesis:**
   - Synthesizes `specs/<feature>/architecture.md` ($\le 1,000\text{--}1,500$ tokens) in a single pass from confirmed metadata on disk (`DECISIONS.md`, report summaries, `SESSION_STATE.json`).
   - Serves as the authoritative cheat-sheet for downstream features and maintenance tasks without re-reading dozens of historical files.

### 5. Check Status
```text
stage status
```
Displays current plan progress, active branch, session state (`SESSION_STATE.json`), decision summary (Tier 1 & Tier 2 counts), scratchpad status, and the most recent stage report.

### 6. Redo Active Stage
```text
stage redo
```
Safely resets current stage modifications and restarts execution.

### 7. Analyze Token Efficiency & Telemetry
```text
stage analyze_tokens [--feature <name>]
```
Aliases: `stage tokens`, `stage telemetry`
Parses subagent and orchestrator transcripts in `~/.gemini/antigravity/brain/` for the active feature:
- **Post-Feature Mode:** Run after stage completion or `stage cleanup` to evaluate full-build token consumption, wall-clock latency, tool call distributions, invariant compliance, and YOLO vs. single-stage tradeoffs.
- **Mid-Feature Diagnostic Mode:** Run halfway through development (e.g., at Stage 5 of 20) to detect runaway turn counts (>30 turns), excessive `view_file` calls, and retry bottlenecks before the full feature finishes.
- Writes standardized `specs/<feature>/tokens_efficiency_report.md` and `tokens_efficiency_report.json`.
- Prints a compact terminal summary ($\le 250$ tokens).

---

## Model Configuration

Subagent routing is stored in `pipeline.json`. To override routing for a specific project, create `.agents/pipeline.json` in your project root.

```json
{
  "plan-architect": "flash",
  "stage-runner": "flash",
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
