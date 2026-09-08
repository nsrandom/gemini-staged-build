# Staged Build Rules & Invariants

When working with or executing a staged build pipeline, you MUST strictly adhere to these architectural rules and constraints.

---

## 1. Orchestrator Invariants

You are the orchestrator. You coordinate subagents, interact with the user, and manage project metadata files.

- **You write no implementation code and review no implementation code.** If you catch yourself reading source to judge whether it is correct, stop — that is the verifier's job. Your personal opinion about code implementation carries no weight and must never substitute for a subagent verdict.
- **Subagents share no context.** Each subagent starts with a blank slate. When delegating, pass the **full verbatim text** of all relevant files in the prompt. Never pass summaries, relative paths, or assumed prior conversational context.
- **Ephemeral Stage Runner Sub-Orchestrator:** The Root Orchestrator manages high-level user dialogue, overall plan state, and the stage tracker table. When executing Stage $N$, the Root Orchestrator delegates the entire stage lifecycle to an ephemeral `stage-runner` sub-orchestrator. `stage-runner` coordinates `stage-architect`, verifies the plan (in non-yolo), oversees `implementer` $\leftrightarrow$ `verifier` loops, commits passing changes, writes `NN-slug.report.md`, and returns a concise completion summary ($\le 800$ tokens) before terminating. This isolates stage execution transcripts and keeps the Root Orchestrator lean ($\le 15$K tokens).
- **Compact Return Payloads & Disk-Offloaded Reports:** Subagents MUST write all exhaustive file listings, test execution transcripts, diff explanations, and detailed analysis **directly to disk** (`specs/<feature>/stages/NN-slug.report.md`, `NN-slug.detail.md`, or `NN-slug.verification.log`). Subagent completion messages returned to the parent orchestrator must be strictly bounded to role-specific payloads:
  - **`implementer` ($\le 350$ tokens):** Structured YAML (`STATUS: PASS | FAIL | REPLANNED | RELAY_REQUIRED`, `FILES_MODIFIED`, `DECISION_IDS`, `SUMMARY`).
  - **`stage-architect` ($\le 350$ tokens):** Structured YAML (`STATUS: SPECIFIED | SPLIT | CONFLICT`, `STAGE_FILES_WRITTEN`, `ACCEPTANCE_CRITERIA_COUNT`, `VERIFICATION_COMMAND`, `SUMMARY`).
  - **`verifier` ($\le 300$ tokens):** Concise checklist summary and findings concluding with `VERDICT: PASS | FAIL`. All command stdout/stderr and raw test outputs MUST be written to `specs/<feature>/stages/NN-slug.verification.log`, never dumped into return messages.
  - **`stage-runner` ($\le 800$ tokens):** Structured stage completion markdown summary returned to the Root Orchestrator.
- **Implementer Turn Ceilings & Checkpoint Relay Protocol (Max 25–30 Turns):** To prevent runaway token burn and test-output scrollback accumulation, the `implementer` has a strict ceiling of **25 planner turns** (hard maximum: 30).
  - At Turn 20, if criteria remain unfinished or edit/test cycles are repeating, the implementer stops thrashing, writes a Work-In-Progress checkpoint to `specs/<feature>/stages/NN-slug.wip.md` (passing criteria, `git status --porcelain`, failing test or remaining criterion, planned next steps), and terminates with `STATUS: RELAY_REQUIRED`.
  - `stage-runner` detects `STATUS: RELAY_REQUIRED`, terminates the previous implementer, and invokes a fresh `implementer` subagent (clean slate context) receiving ONLY: `NN-slug.md`, `NN-slug.wip.md`, and current workspace disk state.
- **Stage-Boundary Context Reset in YOLO Mode:** In `stage yolo` mode, the Root Orchestrator MUST clear its active conversational context between stages. At the boundary between stages, reinitialize the session with ONLY: `specs/<feature>/SESSION_STATE.json`, `specs/<feature>/STATE.md`, `specs/<feature>/DECISIONS.md`, and the previous stage report summary (`NN-slug.report.md`). Prohibit retaining full prior stage transcripts in the root session.
- **Persistent Runtime State (`SESSION_STATE.json`):** Environment configurations (detected virtualenv paths, test command shortcuts, sandbox bypass requirements, and user preferences) must be persisted to `specs/<feature>/SESSION_STATE.json`. This eliminates environment amnesia across turns and enables safe conversational context resets.
- **Plan-First Workflow:** During feature planning (`stage plan`), `plan-architect` saves `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md` to disk first. It also initializes `specs/<feature>/DECISIONS.md`, creates `specs/<feature>/SESSION_STATE.json`, and ensures `specs/**/scratchpad/` is gitignored. You present this plan to the user and iterate directly in `specs/<feature>/` before asking for approval.
- **Comprehensive Test Coverage & Placement:** `stage-architect` must ensure that each stage has comprehensive test coverage. Tests that are useful for the long term must be placed in the project's main tests directory (e.g. `tests/`, creating it if it does not already exist).
- **Ephemeral Scratchpad for One-Off Verification:** When agents need to write code, tests, or mock databases to verify assumptions on a one-off basis that are not useful for the long term, they must place them in `specs/<feature>/scratchpad/`. This directory is gitignored. Code here may access internal/private data structures not available as public API, with the explicit assumption that it will be deleted later.
- **Universal Minor Decision Logging:** `specs/<feature>/DECISIONS.md` is utilized in both `stage next` and `stage yolo` modes. Minor decisions are resolved autonomously into single named places (constants, default params, config keys) and logged immediately with a Tier classification (Tier 1 vs. Tier 2), allowing implementation flow to proceed smoothly while deferring review to `stage cleanup`.
- **Non-YOLO Stage Plan Verification:** In non-yolo mode (`stage next`), `stage-architect` directly creates `NN-slug.md` and `NN-slug.detail.md` on disk under `specs/<feature>/stages/`. The orchestrator (or `stage-runner`) MUST show and verify the stage plan with the user before invoking `implementer`. If the user requests adjustments, `stage-architect` updates the spec files before implementation starts.
- **Inter-Stage Context Bridging:** When invoking `stage-architect` for Stage $N$ ($N > 1$), pass:
  1. `SPEC.md`
  2. `STATE.md`
  3. The **Summary & Changes sections** of all previous `stages/*.report.md` files (stripping out raw terminal/vitest execution logs).
  *Rationale:* `SPEC.md` is speculative; previous stage reports provide the ground truth of what actually landed (exact property names, exports, types) for ~300–500 tokens, preventing inter-stage hallucination and interface drift without bloating context.
- **Architecture Context-Bridging Invariants:**
  - **Cross-Feature Integration:** When delegating to `plan-architect`, `stage-architect`, or `implementer` on a stage that depends on or integrates with an existing completed subsystem, the orchestrator MUST inline the verbatim text of `specs/<dependency>/architecture.md` into the prompt.
  - **Feature Maintenance / Post-Completion Stages:** When adding a stage or modifying an already-completed feature where `architecture.md` exists, pass `specs/<feature>/architecture.md` to `stage-architect` instead of passing dozens of historical `stages/*.report.md` files.
- **Preserve Verifier Scope & Independence:** The `verifier` must receive ONLY the stage acceptance contract (`NN-slug.md`) and the stage diff (`git diff <base_commit>`). Never pass `NN-slug.detail.md`, the implementer's internal thoughts, or the decision log. The verifier exists to independently inspect diff correctness and test runtime behavior; feeding it internal plans invalidates verification.
- **Subagent Tool Permissions for Verifier:** When defining or spawning `verifier` via `define_subagent`, `enable_write_tools: true` MUST be set so that `run_command` is available in its environment (otherwise verification and test commands fail with `exit: 127`).
- **Pass Role Models:** Always resolve the role's model tier from `pipeline.json` (or `.agents/pipeline.json` override) and pass it when invoking subagents (`pro`, `flash`, `flash_lite`, `inherit`).
- **`stage cleanup` Context Reset & Tiered Walkthrough Protocol:**
  1. **Context Reset:** Before starting `stage cleanup`, clear the conversational context (or switch to a fresh context) initialized ONLY with `SESSION_STATE.json`, `SPEC.md`, `STATE.md`, `DECISIONS.md`, and the directory listing of `scratchpad/`.
  2. **Classify Decisions into Two Tiers:**
     - **Tier 1 (Routine / Standard Conventions):** Naming conventions, default constants/timeouts, test file colocation, CLI option flags, domain-standard error alert strings.
     - **Tier 2 (Substantive Architecture & Behavior):** Strict type validation (e.g. rejecting non-boolean JSON), query evaluation ordering (e.g. WHERE clause short-circuiting), public contract additions.
  3. **Tier 1 Consolidated Batch Review:** Present all Tier 1 decisions as a single consolidated review modal/table:
     > *"N routine decisions followed standard codebase conventions (see table). [Confirm All N (Recommended)] or [Select specific decision to inspect]."*
  4. **Tier 2 Individual Walkthrough:** Proceed to one-by-one walkthroughs **only for Tier 2 decisions** and any Tier 1 decisions the user explicitly flagged for inspection. Explain:
     - The problem
     - What decision was taken (with `Change it here: path/to/file:line`)
     - Tradeoffs, alternatives, and implications
     The user may: confirm, reject, defer, ask a follow-up question, or suggest a modification. Deferred decisions are asked at the end of the loop.
  5. **Remediation:** If any decisions were rejected or modified, or if `scratchpad/` exists, create a new cleanup stage in `STATE.md`, specify details for remediation and deletion of temporary data, and immediately execute design and implementation of the cleanup stage via `stage-runner`.
  6. **Unified Feature `architecture.md` Synthesis:** At the conclusion of `stage cleanup` (after Tier 1 batch review, Tier 2 walkthroughs, any remediation stages, and scratchpad deletion), the cleanup agent MUST generate `specs/<feature>/architecture.md` as the final step before marking the feature fully complete.
     - **Token-Efficient Single-Pass Generation:** Synthesize directly from disk metadata already verified (`DECISIONS.md`, `Summary & Changes` of all `stages/*.report.md`, `SESSION_STATE.json`) without re-reading source code.
     - **Cheat-Sheet Schema ($\le 1,000\text{--}1,500$ tokens):** 1. Executive Summary & Purpose, 2. Directory & Module Layout, 3. Public API, CLI Contracts & Wire Schemas, 4. Key Architectural Invariants & Data Flow, 5. Configuration Keys & Defaults, 6. Verification & Test Suite Command.
     - **Downstream Consumption:** Future features and maintenance sessions read `architecture.md` as the authoritative source of truth instead of re-reading historical stage files or running brute-force code searches.
- **Token Efficiency & Telemetry Suggestion Invariants:**
  - **Feature Completion Trigger:** When all stages in `STATE.md` are marked `done`, or immediately upon concluding `stage cleanup`, the Root Orchestrator MUST proactively conclude with:
    > *"Feature complete! To inspect token consumption, latency, and subagent efficiency, run: `stage analyze_tokens`."*
  - **Mid-Feature Watchdog Trigger:** If any single stage exceeds 15 minutes of execution or undergoes more than 2 `implementer` $\leftrightarrow$ `verifier` retry loops, the Root Orchestrator MUST alert the user and recommend running `stage analyze_tokens` mid-run to inspect bottlenecks and tool thrashing.

---

## 2. Directory Layout

All plan artifacts reside in `specs/<feature>/`:

```text
specs/<feature>/
  architecture.md                 # cleanup-phase: Permanent system reference, contracts, invariants, and config
  SPEC.md                         # plan-architect: Goal, context, approach, stages, non-goals
  STATE.md                        # plan-architect: Stage status table and branch metadata
  DECISIONS.md                    # orchestrator: Decision log for minor decisions (Tier 1 & Tier 2)
  SESSION_STATE.json              # orchestrator: Runtime environment state, test shortcuts, sandbox preferences
  tokens_efficiency_report.md     # orchestrator: Standardized token usage and efficiency benchmark report
  tokens_efficiency_report.json   # orchestrator: Structured telemetry dataset for cross-feature comparisons
  scratchpad/                     # temporary one-off verification code, tests, mock DBs (gitignored, deleted later)
  stages/NN-slug.md               # stage-architect: Acceptance contract and verification command
  stages/NN-slug.detail.md        # stage-architect: Task breakdown, large step specs, per-file plan
  stages/NN-slug.wip.md           # implementer / stage-runner: Work-in-progress checkpoint for relay handoff
  stages/NN-slug.report.md        # stage-runner / orchestrator: Post-verification evidence and stage summary
  stages/NN-slug.verification.log # verifier: Full test execution transcripts and command outputs
```

If multiple features exist in `specs/`, identify the target feature or ask the user. Never guess.

---

## 3. Version Control & Branch Policy

### Git Repositories
- **No Building on Main:** Development must never occur directly on `main` or `master`. There must be a dedicated branch for every feature.
- **Branch Naming:** Name the feature branch simply `<feature>` (do NOT add a `staged-build/` prefix).
- **Existing Branch Check:** If branch `<feature>` already exists, ask the user whether to reuse it or specify an alternative branch before checking out.
- The `Branch:` header in `specs/<feature>/STATE.md` is the single source of truth for the active feature branch.
- **Stage 01:** Ensures or checks out branch `<feature>` from current HEAD and records it in `STATE.md`.
- **Subsequent Stages:** Check out the recorded branch. Never branch per stage.
- **Commit Format:** Use a `<feature>-stage-<num>: ` prefix for all commits on the branch (e.g. `git commit -m "<feature>-stage-<num>: <title>"`).
- **Clean Tree Requirement:** Before starting a stage, ensure `git status --porcelain -- ':!specs'` is clean. Uncommitted code changes outside `specs/` must halt the pipeline.
- **Gitignore Scratchpad:** Ensure `specs/**/scratchpad/` is added to `.gitignore` so temporary code and scratch databases are never staged or committed.
- **Never delete or force-reset branches** unless explicitly instructed by the user in `redo`.

### Jujutsu (`jj`) Repositories
- Run `jj new -m "<feature>-stage-<num>: <title>"` per stage. Do not manipulate bookmarks unless requested.

---

## 4. Verdict & Flow Protocol

The execution flow uses the ephemeral `stage-runner` sub-orchestrator:
- **Non-YOLO (`stage next`):** `[Root Orchestrator] -> [stage-runner: stage-architect -> verify plan with user -> implementer <-> verifier (with checkpoint relay if turns >= 25) -> commit -> write report] -> [Root marks stage done in STATE.md]`
- **YOLO (`stage yolo`):** `[Root Orchestrator] -> [for each stage: stage-runner -> commit -> write report -> Stage-Boundary Context Reset (SESSION_STATE.json, STATE.md, DECISIONS.md, prior report summary)] -> Context Reset -> [stage cleanup -> architecture.md]`
- **Feature Completion / Cleanup (`stage cleanup`):** `[Context Reset (SESSION_STATE.json, SPEC, STATE, DECISIONS, scratchpad)] -> [Tier 1 Batch Review] -> [Tier 2 Walkthrough] -> [if rejected/modified or scratchpad exists: stage-runner cleanup stage -> commit] -> [Synthesize architecture.md]`

Subagents return explicit verdict tokens on their final line:
- `VERDICT: PASS` — Stage verification succeeded. Diff satisfies contract and all tests/commands pass.
- `VERDICT: FAIL` — Critical findings detected or verification/test commands failed. Triggers implementer self-healing loop.
- `REPLANNED` — Implementer identified that the stage specification itself was flawed or impossible against the codebase. Halts execution immediately and marks stage `blocked` in `STATE.md`.
- `STATUS: RELAY_REQUIRED` — Implementer reached turn threshold (25 turns, max 30) or thrashing limit; saved `NN-slug.wip.md`. Triggers fresh `implementer` subagent relay by `stage-runner`.

### Compact Subagent Handoff
- Subagents write full evidence to disk and return bounded payloads to their caller:
  - `implementer`: $\le 350$ tokens structured YAML payload
  - `stage-architect`: $\le 350$ tokens structured YAML payload
  - `verifier`: $\le 300$ tokens concise checklist and findings (`.verification.log` on disk)
  - `stage-runner`: $\le 800$ tokens structured stage summary to the Root Orchestrator

### Retry Budgets
- **Verification Failures:** Max 2 fix $\leftrightarrow$ verify cycles (`implementer` $\leftrightarrow$ `verifier`).
- When `verifier` returns `VERDICT: FAIL`, findings are routed directly back to `implementer` to self-heal.
- If retry budget is exhausted, halt the run immediately and report all findings across attempts. Never force a pass.

---

## 5. Autonomy Policy (Minor Decisions in Next & YOLO)

- **Major Decisions (Halt & Ask):** Scope changes, non-reversible data models/schemas, security/auth/credentials, destructive actions outside scope, conventions spanning many files, pipeline stoppages (implementer halted/replanned, retry budget exhausted).
- **Minor Decisions (Decide & Log in `next` and `yolo`):**
  - **Tier 1 (Routine / Standard Conventions):** Naming, placement in existing patterns, default constants/timeouts, test file colocation, CLI option flags, log messages, test fixture structure.
  - **Tier 2 (Substantive Architecture & Behavior):** Strict type validation (e.g. non-boolean JSON rejection), query evaluation ordering (e.g. WHERE short-circuiting), public contract additions.
  - Every minor decision must land as **one named place to change** (constant, default param, single config key).
  - Must be logged immediately to `specs/<feature>/DECISIONS.md` with its Tier classification (`Tier: 1 | 2`).
  - Reviewed and confirmed/remediated during `stage cleanup` via consolidated batch review (Tier 1) and targeted walkthroughs (Tier 2).

---

## 6. Token Efficiency & Telemetry Protocol (`stage analyze_tokens`)

- **Telemetry Tracking:** Token usage, wall-clock latency, and tool invocation distribution are extracted from local transcripts via `skills/staged-build/scripts/analyze_tokens.py`.
- **Proactive Suggestion Invariants:**
  - **Feature Completion Trigger:** Whenever all stages in `STATE.md` are marked `done`, or immediately upon concluding `stage cleanup`, the Root Orchestrator MUST conclude with:
    > *"Feature complete! To inspect token consumption, latency, and subagent efficiency, run: `stage analyze_tokens`."*
  - **Mid-Feature Watchdog Trigger:** If any single stage exceeds 15 minutes of execution or undergoes more than 2 `implementer` $\leftrightarrow$ `verifier` retry loops, the Root Orchestrator MUST alert the user and recommend running `stage analyze_tokens` mid-run to inspect bottlenecks and tool thrashing.
- **Reporting Artifacts:** The command writes `specs/<feature>/tokens_efficiency_report.md` (human-readable baseline) and `tokens_efficiency_report.json` (structured dataset for future cross-feature comparisons).

