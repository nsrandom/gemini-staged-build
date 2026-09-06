---
name: staged-build
description: >-
  Run the staged multi-agent build pipeline: plan goals, execute stages with independent verification,
  implement changes with self-healing feedback, or run full plans unattended with yolo mode.
  Use when the user asks to plan a feature, execute the next build stage, check build status, redo a stage, or run staged builds.
---

# Staged Build Pipeline

A multi-agent development pipeline in which complex software engineering goals are broken into independently shippable stages. Every stage is rigorously specified, grounded in prior stage results, implemented, verified independently against diff criteria and live test execution, and self-healed if necessary.

---

## Quick Reference

| Command / Trigger | Primary Action | Stop Condition |
|---|---|---|
| `stage plan "<goal>"` | Interactive planning conversation with `plan-architect`. Saves plan directly to `specs/<feature>/SPEC.md` and `STATE.md`, initializes `DECISIONS.md` and `SESSION_STATE.json`, ensures `specs/**/scratchpad/` is gitignored, presents to user, and iterates on feedback before approval. | Stops after plan is approved. Never implements. |
| `stage next [--new-branch]` | Executes exactly **one** pending stage via ephemeral `stage-runner`: creates specs on disk $\to$ verifies stage plan with user $\to$ implement $\leftrightarrow$ verify $\to$ compact report handoff. Minor decisions logged to `DECISIONS.md`. | Stops after verifying stage and producing report. Never auto-advances. |
| `stage yolo ["<goal>"]` | Runs the entire plan end-to-end unattended via isolated `stage-runner` per stage. Context remains minimal between stages. Commits each stage and transitions to `stage cleanup`. | Stops on major architectural decisions, unrecoverable failures, or transitions to `stage cleanup`. |
| `stage cleanup [--feature <name>]` | Resets conversational context to lean state (`SESSION_STATE.json` + specs). Presents Tier 1 decisions in a single batch review table ("Confirm All N"). Walks through Tier 2 and flagged decisions one-by-one. Automatically designs and executes cleanup stage for remediations and scratchpad deletion. | Stops after verifying and committing cleanup stage. |
| `stage status` | Displays active plan state, current git/jj branch, runtime session state, decision summary, and most recent stage report. | Read-only. |
| `stage redo` | Discards current stage work with confirmation, resets stage to `pending`, and re-runs `next`. | Stops after user confirmation. |
| `stage analyze_tokens [--feature <name>]` | Parses subagent transcripts in `~/.gemini/antigravity/brain/` to produce standardized `tokens_efficiency_report.md` and `.json`. Supports post-completion benchmark reports and mid-feature bottleneck diagnostics. Aliases: `stage tokens`, `stage telemetry`. | Read-only analysis. Prints compact terminal summary ($\le 250$ tokens). |

---

## Architectural Principles & Invariants

1. **Root Orchestrator & Ephemeral Stage Runner Separation:** The Root Orchestrator manages the user dialogue, overall plan state, and the stage tracker table. When executing Stage $N$, it delegates to an ephemeral `stage-runner` sub-orchestrator. `stage-runner` executes the inner lifecycle (`stage-architect` $\to$ verify plan $\to$ `implementer` $\leftrightarrow$ `verifier` $\to$ commit $\to$ report), writes evidence to disk, and returns a concise completion payload ($\le 1000$ tokens) to the root. The Root Orchestrator never accumulates intermediate transcripts or bloats beyond ~15K tokens.
2. **Compact Subagent Return Payloads & Disk Offloading:** Subagents (`implementer`, `stage-architect`) write exhaustive breakdowns, test logs, and diff analyses directly to disk (`NN-slug.report.md`, `NN-slug.detail.md`). Subagents return strictly bounded structured YAML payloads ($\le 250$ tokens) to their caller, prohibiting raw terminal transcripts or code diff dumps in conversational messages.
3. **Persistent Runtime State (`SESSION_STATE.json`):** Environment parameters (detected virtualenvs, test shortcuts, sandbox bypass preferences, runtime paths) are persisted to `specs/<feature>/SESSION_STATE.json`. This eliminates environment amnesia and allows safe context reset.
4. **Plan-First Architecture:** Feature planning (`stage plan`) saves the working plan directly to `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md` first, initializes `DECISIONS.md` and `SESSION_STATE.json`, and ensures `specs/**/scratchpad/` is gitignored. The orchestrator presents the plan to the user, and updates are made in place before final approval.
5. **Comprehensive Test Coverage & Main Tests Directory:** `stage-architect` must ensure that each stage has comprehensive test coverage. Tests that are useful for the long term must be placed in the project's main tests directory (e.g. `tests/`, creating it if it does not already exist).
6. **Ephemeral Scratchpad for One-Off Verification:** When agents need to write code, tests, or mock databases to verify assumptions on a one-off basis that are not useful for the long term, they must place them in `specs/<feature>/scratchpad/`. This directory is gitignored. Code here may access internal data structures not available as public API, with the explicit assumption that it will be deleted later.
7. **Universal Minor Decision Logging:** `specs/<feature>/DECISIONS.md` is utilized in both `stage next` and `stage yolo` modes. Minor decisions are resolved autonomously into single named places (constants, default params, config keys) and logged immediately with a Tier classification (`Tier: 1 | 2`), allowing implementation flow to proceed smoothly while deferring review to `stage cleanup`.
8. **Non-YOLO Stage Plan Verification:** In non-yolo mode (`stage next`), `stage-architect` directly creates `NN-slug.md` and `NN-slug.detail.md` on disk under `specs/<feature>/stages/`. The orchestrator (or `stage-runner`) **must show and verify the stage plan with the user** before delegating to `implementer`.
9. **Inter-Stage Context Bridging:** Subagents start blank and share no conversational context. All file dependencies and prior findings must be passed verbatim in the delegation prompt. When invoking `stage-architect` for Stage $N$ ($N > 1$), pass `SPEC.md`, `STATE.md`, and the **Summary & Changes sections** of all previous `stages/*.report.md` files (stripping raw execution logs) to ground specifications in landed code without token bloat.
10. **Verifier Independence & Scope:** The `verifier` receives **ONLY the stage acceptance contract (`NN-slug.md`)** and the stage diff (`git diff <base_commit>`). Never pass implementation specs (`.detail.md`), implementer thoughts, or decision logs.
11. **Feature Branch & Commit Standards:**
   - **No building on main:** Never build directly on `main` or `master`. Every feature requires its own branch.
   - **Branch naming:** The branch is named simply `<feature>` (do not add a `staged-build/` prefix).
   - **Branch reuse check:** If branch `<feature>` already exists, ask the user whether to reuse it.
   - **Commit format:** All commits on the branch must use the `<feature>-stage-<num>: ` prefix (e.g. `git commit -m "<feature>-stage-<num>: <title>"`).
12. **Context Reset & Tiered Decision Cleanup:** Prior to `stage cleanup`, the orchestrator resets conversational context to a lean state loaded only with `SESSION_STATE.json` and spec files. It presents Tier 1 decisions in a single consolidated batch review modal/table, and walks through Tier 2 and flagged decisions one-by-one, automatically executing a cleanup stage if remediations or scratchpads remain.

---

## Directory & File Layout

```text
specs/<feature>/
  SPEC.md                         # High-level architecture, approach, stages, non-goals
  STATE.md                        # Stage tracker table and branch binding
  DECISIONS.md                    # Log of minor decisions taken in next and yolo modes (Tier 1 & Tier 2)
  SESSION_STATE.json              # Runtime environment state, test shortcuts, sandbox preferences
  tokens_efficiency_report.md     # Standardized token usage and efficiency benchmark report
  tokens_efficiency_report.json   # Structured telemetry dataset for cross-feature comparisons
  scratchpad/                     # One-off verification code, tests, mock DBs (gitignored, deleted later)
  stages/
    NN-slug.md                    # Black-box acceptance contract & verification command
    NN-slug.detail.md             # Deep implementation plan & large step breakdowns
    NN-slug.report.md             # Stage completion report with verification evidence
```

### `SESSION_STATE.json` Schema
```json
{
  "branch": "<feature>",
  "sandbox_bypass_required": true,
  "python_runtime": ".venv/bin/python",
  "test_command_shortcuts": {
    "web": "npm --prefix web test",
    "python": ".venv/bin/python -m unittest discover -s ."
  },
  "global_user_preferences": []
}
```

---

## Subagent Setup & Model Routing

When delegating, resolve model tiers from `pipeline.json` (or `.agents/pipeline.json` override):

```json
{
  "plan-architect": "flash",
  "stage-runner": "flash",
  "stage-architect": "flash",
  "implementer": "flash",
  "verifier": "flash"
}
```

### Spawning Subagents in Antigravity

Subagents are invoked using `invoke_subagent` (or defined via `define_subagent`):
- `TypeName`: The role name (`plan-architect`, `stage-runner`, `stage-architect`, `implementer`, `verifier`).
- `Role`: Descriptive role title (e.g. `Stage Runner`, `Staged Build Verifier`).
- `Model`: Resolved model tier (`"flash"`, `"pro"`, `"flash_lite"`, `"inherit"`).
- `Workspace`: `"inherit"`.
- `Prompt`: Subagent persona instructions concatenated with the verbatim task payload.

> [!IMPORTANT]
> **Subagent Tool Permissions for `stage-runner` & `verifier`:**
> - `stage-runner` requires `enable_subagent_tools: true` and `enable_write_tools: true` to coordinate child agents, manage git commits, and write reports.
> - `verifier` requires `enable_write_tools: true` so that `run_command` is available in its environment to execute verification scripts and test suites (otherwise commands fail with `exit: 127`).

---

## Workflows

### 1. `stage plan "<goal>"`

Planning is an interactive conversation grounded in disk artifacts from the start.

```mermaid
flowchart TD
    Start([User provides Goal]) --> PlanDraft[Delegate to plan-architect\nAnalyze repo & save plan to\nspecs/<feature>/SPEC.md & STATE.md\nInit DECISIONS.md, SESSION_STATE.json & gitignore scratchpad]
    PlanDraft --> UserReview{Present Saved Plan\n& Inquire via ask_question}
    UserReview -- "User requests edits" --> UpdatePlan[Delegate updates to\nplan-architect in specs/<feature>/]
    UpdatePlan --> UserReview
    UserReview -- "User Approves" --> Stop([Lock plan & STOP])
```

1. **Draft & Save to Disk:** Invoke `plan-architect` on model `flash` with the goal and instruction: `"Analyze codebase, assess feasibility, isolate unknowns into Stage 01, save draft plan directly to specs/<feature>/SPEC.md and specs/<feature>/STATE.md, initialize specs/<feature>/DECISIONS.md and specs/<feature>/SESSION_STATE.json, and ensure specs/**/scratchpad/ is in .gitignore."`
2. **User Presentation & Alignment:** Present the saved plan to the user with clickable links to `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md`.
   - Use `ask_question` for discrete choices, highlighting defaults.
   - Solicit additions, removals, renames, or reordering of stages.
3. **Iterate & Update:** If the user requests changes, pass feedback back to `plan-architect` to update `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md` directly in place.
4. **Approve & Complete:** Upon explicit user approval, the plan is settled. Present the final stage table and halt.

---

### 2. `stage next [--new-branch]`

Executes exactly **one** pending stage via the ephemeral `stage-runner` sub-orchestrator.

```mermaid
flowchart TD
    A[Read STATE.md & pick first non-done stage] --> B[Verify clean git status & check branch]
    B --> B2{Branch exists?}
    B2 -- Yes --> B3[Ask user to confirm reuse] --> C
    B2 -- No --> B4[Create branch <feature>] --> C
    C[Mark stage in-progress in STATE.md] --> SR[Invoke ephemeral stage-runner\nwith SPEC, STATE, & prior report summaries]
    SR --> D[Delegate to stage-architect\nDirectly writes NN-slug.md & .detail.md\nReturns compact summary <=250 tokens]
    D --> D2{Non-YOLO Mode:\nShow & verify stage plan with user}
    D2 -- "Edits requested" --> D3[Update specs in place] --> D2
    D2 -- "Approved" --> E[Record Base Commit\nDelegate to implementer\nWrites code, tests in main dir, scratchpad in scratchpad/\nReturns compact YAML payload <=250 tokens]
    E --> F[Delegate to verifier\nInspects diff & executes test suite\nStrict VERDICT PASS/FAIL]
    F -- FAIL (max 2) --> G[Implementer Self-Healing\nFix root cause & re-verify] --> F
    F -- PASS --> H[Commit stage: <feature>-stage-<num>: <title>\nWrite NN-slug.report.md to disk\nReturn compact summary <=1000 tokens]
    H --> I[Root marks stage done in STATE.md\nSuggest commit & STOP]
```

1. **Select Stage:** First non-`done` row in `STATE.md`. If `blocked`, halt and explain why.
2. **VCS & Session Setup:**
   - Verify `git status --porcelain -- ':!specs'` is clean. If uncommitted code exists, halt.
   - **Never build on main/master:** Ensure a feature branch `<feature>` is used.
   - Check if branch `<feature>` already exists:
     - If it exists, ask the user whether to reuse it (`git checkout <feature>`).
     - If it does not exist, create and check out the branch: `git checkout -b <feature>`.
   - Record the branch and environment parameters (virtualenv paths, sandbox settings, test runners) in `specs/<feature>/SESSION_STATE.json` and `STATE.md`.
   - Ensure `specs/**/scratchpad/` is added to `.gitignore`.
3. **Delegate to `stage-runner`:**
   - The Root Orchestrator invokes `stage-runner` (model `flash`, `enable_subagent_tools: true`, `enable_write_tools: true`).
   - Pass `SPEC.md`, `STATE.md`, the stage's row, and the **Summary & Changes sections** of all previous `stages/*.report.md` files (stripping raw execution logs).
4. **`stage-runner` Lifecycle Execution:**
   - **Specification:** `stage-runner` invokes `stage-architect` (model `flash`).
     - `stage-architect` ensures comprehensive test coverage in the project's main tests directory and isolates temporary checks to `specs/<feature>/scratchpad/`.
     - Writes `specs/<feature>/stages/NN-slug.md` (contract) and `NN-slug.detail.md` (implementation spec) directly to disk.
     - Returns a **compact structured summary ($\le 250$ tokens)** to `stage-runner`.
   - **Plan Verification (Non-YOLO):** `stage-runner` presents the stage plan to the user: links to `NN-slug.md` and `NN-slug.detail.md`, summary of acceptance criteria, test coverage, and verification command. Solicits user approval.
   - **Implementation:** `stage-runner` invokes `implementer` (model `flash`).
     - `implementer` writes production code, long-term tests to main test directory, and throwaway checks to `scratchpad/`.
     - Minor decisions are resolved into single named places and output with Tier classification.
     - `implementer` writes exhaustive notes and execution logs to disk (`NN-slug.report.md`).
     - Returns a **compact structured YAML payload ($\le 250$ tokens)**:
       ```yaml
       STATUS: PASS | FAIL | REPLANNED
       FILES_MODIFIED:
         - path/to/file1
       DECISIONS_LOGGED:
         - ID: D07
           Tier: 1 | 2
           Call: Strict boolean checking
           File: web/server.js:180
       SUMMARY: 1-2 sentence description of landed changes.
       ```
     - Transcribes any autonomous decisions into `specs/<feature>/DECISIONS.md`.
   - **Verification & Self-Healing:** `stage-runner` invokes `verifier` (model `flash`, `enable_write_tools: true`) with `NN-slug.md` and git diff (`git diff <base_commit>`).
     - `verifier` inspects diff against acceptance criteria and executes verification command and test suites.
     - **On FAIL:** Route findings directly back to `implementer` to self-heal (max 2 cycles).
     - **On `REPLANNED`:** Mark stage `blocked` in `STATE.md` and halt.
   - **Commit & Report:** Upon verification `PASS`:
     - Commit stage changes: `git commit -m "<feature>-stage-<num>: <title>"`.
     - Finalize `specs/<feature>/stages/NN-slug.report.md` on disk.
     - `stage-runner` terminates and returns a **compact completion summary ($\le 1000$ tokens)** to the Root Orchestrator.
5. **Root Orchestrator Completion:**
   - Mark stage `done` in `STATE.md`.
   - Report stage success to the user and halt.

---

### 3. `stage yolo ["<goal>"]`

Unattended execution of all stages from start to finish with isolated `stage-runner` invocations per stage, automatically transitioning to `stage cleanup` upon completion.

1. **Setup:**
   - If goal provided and no plan exists, run the interactive planning flow first.
   - Initialize `specs/<feature>/DECISIONS.md` and `specs/<feature>/SESSION_STATE.json`.
   - Ensure clean branch setup on `<feature>` (if branch exists, confirm reuse with user). Never build on `main`.
   - Ensure `specs/**/scratchpad/` is added to `.gitignore`.
2. **Execution Loop:**
   - Pick next pending stage.
   - Invoke ephemeral `stage-runner` to execute the full stage lifecycle unattended.
   - Apply the **Unattended Addendum** (from `references/autonomy_policy.md`).
   - `stage-runner` oversees `stage-architect`, `implementer`, and `verifier`, commits passing code automatically, writes `NN-slug.report.md` to disk, and returns a compact status summary.
   - Transcribe all `Autonomous decisions` into `DECISIONS.md` immediately with Tier tags.
   - Root Orchestrator updates `STATE.md` and advances to the next stage.
   - Intermediate file diffs, implementation thoughts, and raw test logs remain confined to the terminated `stage-runner`, preventing context accumulation in the Root Orchestrator.
3. **Major Stop Conditions:**
   - Implementer stalls, stage-architect splits stage, implementer returns `REPLANNED`, or verification retry budget (2 cycles) is exhausted.
   - Halt, output the blocker in subagent's verbatim words, and leave repository intact for user inspection.
4. **Transition to Cleanup:**
   - When all implementation stages are `done`, automatically invoke `stage cleanup` to review all decisions and clean up scratchpad data.

---

### 4. `stage cleanup [--feature <name>]`

Interactive review of decisions taken during feature development followed by automated cleanup stage execution, optimized for minimal token overhead.

```mermaid
flowchart TD
    Start([Invoke stage cleanup]) --> Reset[Context Reset:\nLoad ONLY SESSION_STATE.json, SPEC, STATE,\nDECISIONS, & scratchpad listing]
    Reset --> Inspect[Categorize Decisions in DECISIONS.md:\nTier 1: Routine Conventions\nTier 2: Substantive Behavior]
    Inspect --> BatchReview{Tier 1 Batch Review Modal:\nConsolidated table of N decisions}
    BatchReview -- "Confirm All N (Recommended)" --> MarkAllTier1[Mark all Tier 1 confirmed in DECISIONS.md] --> Tier2Check
    BatchReview -- "Flag specific decisions" --> MarkFlagged[Queue flagged decisions for walkthrough] --> Tier2Check
    Tier2Check{Tier 2 or Flagged Decisions exist?}
    Tier2Check -- Yes --> ReviewOne[Present Decision:\nProblem, Decision taken, Change it here,\nTradeoffs/alternatives/implications]
    ReviewOne --> UserAction{User Action}
    UserAction -- "Confirm" --> MarkConfirm[Mark confirmed in DECISIONS.md] --> NextDecision[Next Decision]
    UserAction -- "Reject" --> MarkReject[Mark rejected in DECISIONS.md] --> NextDecision
    UserAction -- "Defer" --> QueueDefer[Add to Deferred Queue] --> NextDecision
    UserAction -- "Ask Follow-up" --> AnswerQ[Answer user question & re-prompt] --> UserAction
    UserAction -- "Suggest Modification" --> MarkMod[Mark modified in DECISIONS.md] --> NextDecision
    NextDecision --> Tier2Check
    Tier2Check -- No --> ProcessDeferred{Deferred items exist?}
    ProcessDeferred -- Yes --> ProcessOne[Re-present Deferred Decision] --> UserAction
    ProcessDeferred -- No --> AssessCleanup{Rejected / Modified decisions\nOR scratchpad exists?}
    AssessCleanup -- No --> AllClean([All decisions confirmed & no scratchpad. Done!])
    AssessCleanup -- Yes --> CreateStage[Create Cleanup Stage in STATE.md\nAdd spec details for remediation & scratchpad removal]
    CreateStage --> ExecuteCleanup[Design & Implement Cleanup Stage via stage-runner:\nstage-architect -> implementer <-> verifier -> commit]
    ExecuteCleanup --> Done([Cleanup Stage Complete & Committed])
```

1. **Conversational Context Reset:**
   - Clear conversational history to drop prompt size from ~160K tokens to ~10K tokens.
   - Initialize clean context with ONLY:
     - `specs/<feature>/SESSION_STATE.json`
     - `specs/<feature>/SPEC.md`, `STATE.md`, and `DECISIONS.md`
     - File listing of `specs/<feature>/scratchpad/`
2. **Decision Categorization:**
   - Read `specs/<feature>/DECISIONS.md` and classify decisions into:
     - **Tier 1 (Routine / Standard Conventions):** Naming conventions, default constants/timeouts, test file colocation, CLI option flags, domain-standard error alert strings.
     - **Tier 2 (Substantive Architecture & Behavior):** Strict type validation (e.g. rejecting non-boolean JSON), query evaluation ordering (e.g. WHERE clause short-circuiting), public contract additions.
3. **Tier 1 Consolidated Batch Review:**
   - Present all Tier 1 decisions as a single consolidated review modal/table:
     > *"N routine decisions followed standard codebase conventions (see table). [Confirm All N (Recommended)] or [Select specific decision to inspect]."*
   - If the user selects **Confirm All N**, mark all Tier 1 decisions as `confirmed` in `DECISIONS.md`.
   - If the user flags specific decisions for closer review, queue those flagged decisions for the individual walkthrough.
4. **Tier 2 (and Flagged) Individual Walkthrough Loop:**
   - Walk through Tier 2 decisions and user-flagged Tier 1 decisions **one at a time**.
   - For each decision, clearly present:
     - **The Problem:** What was unresolved or what challenge was encountered.
     - **What Decision Was Taken:** The choice made and its exact location in code (`Change it here: path/to/file:line`).
     - **Tradeoffs, Alternatives & Implications:** Alternatives considered, what was traded off, and downstream consequences.
   - Present the 5 user options:
     1. **Confirm:** User agrees with the decision. Mark status as `confirmed` in `DECISIONS.md`.
     2. **Reject the decision:** User rejects the decision. Mark status as `rejected` in `DECISIONS.md`, and record the user's preferred replacement or rollback direction.
     3. **Defer:** Postpone this decision. Move it to the deferred queue to be re-evaluated after the current pass finishes.
     4. **Ask a follow-up question:** Provide answers, elaborate on nuances, and re-prompt the user with the options.
     5. **Suggest a modification to the decision:** User provides adjustments. Mark status as `modified: <details>` in `DECISIONS.md`.
5. **Deferred Decisions Resolution:**
   - After completing the initial pass, process all deferred decisions in order using the same walkthrough protocol until the deferred queue is empty.
6. **Cleanup Stage Creation & Execution:**
   - If any decisions were rejected or modified, **or** if `specs/<feature>/scratchpad/` exists:
   - Add a new cleanup stage to `specs/<feature>/STATE.md` (e.g., `Stage NN: Cleanup and decision remediation`).
   - Populate the requirements for the cleanup stage:
     - Remediate rejected decisions (revert or replace as instructed).
     - Apply modifications to modified decisions at their named locations.
     - Delete `specs/<feature>/scratchpad/` and any temporary databases or scratch artifacts.
     - Ensure comprehensive test coverage is preserved and all long-term tests pass.
   - Launch design and implementation of the cleanup stage via `stage-runner`:
     - `stage-runner` invokes `stage-architect` to generate `specs/<feature>/stages/NN-cleanup.md` and `NN-cleanup.detail.md`.
     - In non-yolo mode, show & verify the cleanup stage plan with the user.
     - `implementer` makes the remediation changes, deletes `specs/<feature>/scratchpad/`, and runs tests.
     - `verifier` confirms scratchpad deletion, verifies remediation correctness, and runs the project test suite.
     - On verification `PASS`:
       - Write `NN-cleanup.report.md`.
       - Mark stage `done` in `STATE.md`.
       - Update `DECISIONS.md` statuses to `rejected → remediated in stage NN` and `modified → remediated in stage NN`.
       - Commit: `git commit -m "<feature>-stage-<num>: cleanup and decision remediation"`.
       - Stop.

---

### 5. `stage status`

1. Run context resolver script: `python3 .agents/plugins/staged-build/skills/staged-build/scripts/context_resolver.py`.
2. Display feature name, current VCS branch, `STATE.md` table, runtime session state (`SESSION_STATE.json`), decision summary (total, Tier 1, Tier 2, confirmed/unconfirmed/rejected/modified/deferred), scratchpad status, and the latest stage report summary.

---

### 6. `stage redo`

1. Identify active `in-progress` stage (or last `done` stage if specified).
2. Prompt user to confirm discarding uncommitted/stage work.
3. Reset stage changes (`git reset --hard <base_commit>`).
4. Set row status back to `pending` in `STATE.md` and delete `NN-slug.report.md`.
5. Trigger `stage next`.

---

### 7. `stage analyze_tokens [--feature <name>]` (Aliases: `stage tokens`, `stage telemetry`)

Parses subagent and orchestrator transcripts in `~/.gemini/antigravity/brain/` for the active feature to compute token accumulation, model thinking, tool usage, latency, and compliance.

```mermaid
flowchart TD
    Trigger([stage analyze_tokens]) --> Detect[Auto-detect feature from STATE.md or git branch]
    Detect --> ScanTranscripts[Scan ~/.gemini/antigravity/brain/*/ for feature transcripts]
    ScanTranscripts --> Classify[Role Classifier:\nstage-runner, implementer, verifier, stage-architect, etc.]
    Classify --> ModeCheck{All stages complete in STATE.md?}
    ModeCheck -- Yes --> PostReport[Post-Feature Mode:\nFull cross-stage benchmarks,\nYOLO vs Single-Stage analysis,\nInvariant compliance audit]
    ModeCheck -- No --> MidReport[Mid-Feature Diagnostic Mode:\nActive stage bottleneck alerts,\nRunaway turn & view_file warnings]
    PostReport --> WriteArtifacts[Write specs/<feature>/tokens_efficiency_report.md & .json]
    MidReport --> WriteArtifacts
    WriteArtifacts --> PrintSummary[Print compact terminal summary <= 250 tokens]
```

1. **Dual Operational Modes:**
   - **Post-Feature Mode:** Run after all stages complete or after `stage cleanup`. Generates the full benchmark report comparing multi-stage YOLO vs. single-stage runs, audit of the $\le 250$-token return invariant, and actionable optimization hypotheses.
   - **Mid-Feature Diagnostic Mode:** Run anytime during development (e.g. at Stage 5 of 20). Detects runaway turn counts (>30 turns), excessive file-reading overhead (`view_file` tax), high latency (>10 mins), or retry loops before the full feature finishes.
2. **Execution:**
   - Execute: `python3 .agents/plugins/staged-build/scripts/analyze_tokens.py [--feature <name>]` (or `skills/staged-build/scripts/analyze_tokens.py`).
   - Automatically resolves the active feature if `--feature` is omitted.
3. **Artifacts Produced:**
   - `specs/<feature>/tokens_efficiency_report.md`: Standardized human-readable report.
   - `specs/<feature>/tokens_efficiency_report.json`: Machine-readable structured telemetry dataset for cross-feature meta-analysis.
4. **Proactive Suggestion Invariants:**
   - **Feature Completion Trigger:** Whenever all stages in `STATE.md` are marked `done`, or after `stage cleanup`, the Root Orchestrator MUST conclude with:
     > *"Feature complete! To inspect token consumption, latency, and subagent efficiency, run: `stage analyze_tokens`."*
   - **Mid-Feature Watchdog Trigger:** If any single stage exceeds 15 minutes or 2 retry loops, the orchestrator MUST alert the user and recommend `stage analyze_tokens` mid-run.

