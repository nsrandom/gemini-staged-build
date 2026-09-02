# Changelog

All notable changes to the `staged-build` plugin will be documented in this file.

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
