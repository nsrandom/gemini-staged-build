# Changelog

All notable changes to the `staged-build` plugin will be documented in this file.

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
