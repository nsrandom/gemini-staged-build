# Changelog

All notable changes to the `staged-build` plugin will be documented in this file.

## [1.5.0] - 2026-09-06

### Token Efficiency & Telemetry Analytics (`stage analyze_tokens`)
- **New `stage analyze_tokens` Command:** Added `stage analyze_tokens` (with aliases `stage tokens` and `stage telemetry`) to extract, parse, and analyze subagent execution transcripts directly from `~/.gemini/antigravity/brain/`.
- **Dual Operational Modes:**
  - **Post-Feature Comprehensive Mode:** Evaluates full end-to-end token consumption, wall-clock latency, tool call distributions, subagent handoff compliance, and compares multi-stage YOLO mode against single-stage execution.
  - **Mid-Feature Diagnostic Mode:** Enables users to inspect pipeline performance halfway through active feature development (e.g. while on Stage 5 of 20) to detect runaway turn counts (>30 turns), excessive file-reading overhead (`view_file` tax), and retry loops.
- **Standardized Reporting Artifacts:** Generates `specs/<feature>/tokens_efficiency_report.md` (human-readable benchmark report) and `tokens_efficiency_report.json` (machine-readable structured telemetry for cross-feature meta-analysis).
- **Zero-Dependency CLI Script (`scripts/analyze_tokens.py`):** Standalone Python standard-library script providing robust subagent role classification, cumulative context growth calculation, and bounded terminal summaries ($\le 250$ tokens).
- **Proactive Orchestrator Suggestion Triggers:**
  - **Feature Completion Trigger:** The Root Orchestrator automatically suggests running `stage analyze_tokens` upon completion of all planned stages or `stage cleanup`.
  - **Mid-Feature Watchdog Trigger:** The orchestrator proactively alerts and recommends `stage analyze_tokens` if any stage exceeds 15 minutes or 2 retry loops.

## [1.4.0] - 2026-09-04

### Tiered & Batched Decision Walkthrough (`stage cleanup`)
- **Two-Tier Decision Classification:** Minor decisions in `DECISIONS.md` are now classified into:
  - **Tier 1 (Routine / Standard Conventions):** Naming conventions, default constants/timeouts, test file colocation, CLI option flags, domain-standard error alert strings.
  - **Tier 2 (Substantive Architecture & Behavior):** Strict type validation (e.g. rejecting non-boolean JSON), query evaluation ordering (e.g. WHERE short-circuiting), public contract additions.
- **Consolidated Batch Review Modal:** `stage cleanup` presents Tier 1 decisions as a single consolidated batch review modal/table (*"Confirm All N (Recommended)"* or flag specific decisions for inspection), reducing late-session turns from 35+ to 3–4 and saving ~12M prompt tokens.
- **Targeted Walkthroughs:** One-by-one walkthroughs are conducted only for Tier 2 decisions and user-flagged Tier 1 decisions.

### Compact Subagent Return Payloads & Disk-Offloaded Reports
- **Direct-to-Disk Evidence Offloading:** Mandated that subagents (`implementer`, `stage-architect`) write all exhaustive file listings, test output transcripts, code diff explanations, and detailed analysis directly to disk (`NN-slug.report.md` or `NN-slug.detail.md`).
- **Compact Structured Payloads ($\le 500$ tokens):** Subagents return strictly bounded structured YAML payloads containing status, modified files, logged decisions (with Tier tags), and a 1–2 sentence summary.
- **Prohibited Raw Terminal Transcripts:** Raw terminal logs, vitest/jest/unittest outputs, and verbatim diffs are prohibited in conversational return messages, eliminating quadratic $O(N^2)$ re-transmission bloat across stages.

### Persistent Runtime State (`SESSION_STATE.json`) & Context Reset at Cleanup
- **`specs/<feature>/SESSION_STATE.json` Persistence:** Discovered environment parameters (virtualenv paths, sandbox bypass requirements, test command shortcuts, and user preferences) are persisted to disk.
- **Safe Context Reset at Cleanup:** The orchestrator explicitly clears its conversational context prior to `stage cleanup`, reloading only `SESSION_STATE.json`, `SPEC.md`, `STATE.md`, `DECISIONS.md`, and the `scratchpad/` file listing. This drops prompt context from ~160K tokens to ~10K tokens without environment amnesia.

### Ephemeral "Stage Runner" Sub-Orchestrator Pattern
- **New `stage-runner` Persona:** Added a 5th pipeline persona (`stage-runner`, model `flash`, `enable_subagent_tools: true`, `enable_write_tools: true`).
- **Isolated Stage Lifecycles:** The Root Orchestrator delegates single-stage execution to an ephemeral `stage-runner` container that coordinates `stage-architect`, verifies the plan (in non-yolo mode), manages `implementer` $\leftrightarrow$ `verifier` loops, commits passing changes, and writes `NN-slug.report.md`.
- **Bounded Handoff:** `stage-runner` terminates and returns a concise completion summary ($\le 1000$ tokens) to the Root Orchestrator. Root context never accumulates intermediate implementation or verification transcripts, keeping total orchestrator prompt size under ~15K tokens across the entire session.

### Configuration & Tool Updates
- **Pipeline Model Routing:** Updated `pipeline.json` to include `"stage-runner": "flash"`.
- **Context Resolver Enhancements:** Updated `context_resolver.py` to parse `SESSION_STATE.json` and report Tier 1 vs Tier 2 decision counts.


## [1.3.0] - 2026-09-03

### Comprehensive Test Coverage & Project Test Placement
- **Main Project Tests Standard:** `stage-architect` must ensure that each stage has comprehensive test coverage. Tests that are useful for the long term must be placed in the project's main tests directory (e.g. `tests/`, creating it if needed).
- **Test Validation by Verifier:** `verifier` checks test placement in the main project tests directory and executes project test runners.

### Ephemeral Gitignored Scratchpad
- **`specs/<feature>/scratchpad/` Isolation:** Added an isolated scratchpad directory for one-off verification code, experimental tests, and temporary test databases.
- **Internal Access Allowed:** Code in `scratchpad/` may access internal data structures not available as public API, with the explicit assumption that it will be deleted during cleanup.
- **Gitignore Enforcement:** Enforced `specs/**/scratchpad/` in `.gitignore` during `stage plan` and branch setup via `branch_helper.sh ensure-gitignore`.

### Universal Minor Decision Logging
- **`DECISIONS.md` in `stage next` & `stage yolo`:** Minor decisions are decided autonomously into single named places (constants, defaults, config keys) and recorded in `specs/<feature>/DECISIONS.md` across both `stage next` and `stage yolo` modes. This prevents minor choices from interrupting implementation flow while preserving a clear audit trail for subsequent review.
- **Enhanced Decision Schema:** Added `Tradeoffs & Implications` and updated status tracking (`unconfirmed`, `confirmed`, `rejected`, `deferred`, `modified`).

### Interactive `stage cleanup` Command & Decision Remediation
- **Interactive Decision Walkthrough:** `stage cleanup` walks through decisions one by one, explaining the problem, the decision taken, and tradeoffs/alternatives/implications.
- **5 User Action Paths:** The user may `confirm`, `reject the decision`, `defer`, `ask a follow up question`, or `suggest a modification`.
- **Deferred Resolution Queue:** Deferred decisions are systematically revisited at the end of the walkthrough loop.
- **Automated Cleanup Stage Design & Execution:** If any decisions were rejected or modified, or if `specs/<feature>/scratchpad/` exists, the orchestrator automatically creates a cleanup stage in `STATE.md` and immediately starts its design and implementation (`stage-architect` $\to$ `implementer` $\leftrightarrow$ `verifier` $\to$ commit) to apply remediations, delete scratchpads, and ensure all tests pass.

## [1.2.0] - 2026-09-02

### Plan-First Architecture & In-Place Iteration
- **Direct On-Disk Plan Creation:** `plan-architect` now directly writes `specs/<feature>/SPEC.md` and `specs/<feature>/STATE.md` to disk upon initial goal analysis rather than using a fileless proposal pass.
- **Pre-Approval Plan Review:** The orchestrator displays the saved plan to the user for review. User feedback and answers to open questions are updated in place in `specs/<feature>/` before approval.

### Non-YOLO Stage Plan Verification
- **Direct On-Disk Stage Spec Creation:** `stage-architect` directly creates `NN-slug.md` and `NN-slug.detail.md` on disk under `specs/<feature>/stages/` first.
- **User Review Before Implementation:** In non-yolo mode (`stage next`), the orchestrator shows and verifies the stage plan with the user prior to invoking `implementer`. Any user refinements update the stage specs in place before code is written.

### Feature Branch & Commit Conventions
- **No Building on Main:** Enforced policy preventing development directly on `main` or `master`.
- **Simplified Branch Naming:** Feature branches are now named simply `<feature>` (dropping the `staged-build/` prefix).
- **Existing Branch Confirmation:** When preparing the branch, the orchestrator detects if `<feature>` already exists and asks the user whether to reuse it before proceeding.
- **Standardized Commit Format:** All commits on the feature branch use the `<feature>-stage-<num>: ` prefix (e.g., `<feature>-stage-<num>: <title>`).
- **Updated `branch_helper.sh`:** Added `branch-exists`, `commit-stage`, and branch reuse checking flag (`--reuse`) with guards against `main`/`master`.

### Documentation & Maintenance
- **Reinstallation & Update Guide:** Added comprehensive instructions to `README.md` on how to pull updates or perform clean reinstalls for both workspace-level submodules and global installations, including post-update session reload guidance.
- **Version Bump:** Bumped plugin version to `1.2.0` in `plugin.json`.

## [1.1.0] - 2026-09-02

### Architecture & Pipeline Streamlining
- **Dropped `plan-checker` Role:** Removed the extra pre-implementation plan-checking subagent pass. `stage-architect` now outputs the stage contract (`NN-slug.md`) and task breakdown (`.detail.md`) directly to `implementer`, eliminating unnecessary round-trip latency.
- **Unified `verifier` Role:** Merged `reviewer` and `validator` into a single, comprehensive `verifier` persona. The `verifier` receives the acceptance contract and stage diff, performs static diff inspection against acceptance criteria, and actively executes verification commands and the project test suite via `run_command`.
- **Eliminated `debugger` Role in Favor of Self-Healing `implementer`:** When `verifier` detects issues or fails verification commands, findings are routed directly back to `implementer` to reproduce, diagnose root cause, and apply surgical fixes (max 2 retry cycles).
- **Streamlined 3-Role Execution Flow:** The active build loop is now `[stage-architect] -> [implementer] <-> [verifier] -> commit`.

### Subagent Tooling & Permissions
- **Fixed `verifier` Tool Permissions:** Explicitly configured and documented `enable_write_tools: true` for `verifier` subagent definitions in Antigravity. This ensures `run_command` is available in its environment, resolving runtime tool missing errors (`exit: 127`).

### Context Optimization & Token Efficiency
- **Inter-Stage Report Bridging:** When invoking `stage-architect` for Stage $N$ ($N > 1$), the orchestrator now provides `SPEC.md`, `STATE.md`, and the **Summary & Changes sections** of all previous `stages/*.report.md` files (stripping raw execution logs). This grounds stage specifications in exact landed types and interfaces (~300–500 tokens) without token bloat or hallucinated signatures.
- **Context Pruning in YOLO Mode:** The orchestrator prunes old stage implementation plans (`.detail.md`), raw diffs, and verbose test logs upon stage completion and commit. Only `SPEC.md`, the updated `STATE.md`, and concise `report.md` summaries persist across stage boundaries.

### Configuration & Manifest
- **Updated `pipeline.json`:** Streamlined to 4 roles (`plan-architect`, `stage-architect`, `implementer`, `verifier`), all defaulted to `"flash"` for fast, cost-effective execution.
- **Bumped Plugin Version:** Updated `plugin.json` from `1.0.0` to `1.1.0` with updated description.
