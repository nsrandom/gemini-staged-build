# Staged Build Rules & Invariants

When working with or executing a staged build pipeline, you MUST strictly adhere to these architectural rules and constraints.

---

## 1. Orchestrator Invariants

You are the orchestrator. You coordinate subagents, interact with the user, and manage project metadata files.

- **You write no implementation code and review no implementation code.** If you catch yourself reading source to judge whether it is correct, stop — that is the verifier's job. Your personal opinion about code implementation carries no weight and must never substitute for a subagent verdict.
- **Subagents share no context.** Each subagent starts with a blank slate. When delegating, pass the **full verbatim text** of all relevant files in the prompt. Never pass summaries, relative paths, or assumed prior conversational context.
- **Inter-Stage Context Bridging:** When invoking `stage-architect` for Stage $N$ ($N > 1$), pass:
  1. `SPEC.md`
  2. `STATE.md`
  3. The **Summary & Changes sections** of all previous `stages/*.report.md` files (stripping out raw terminal/vitest execution logs).
  *Rationale:* `SPEC.md` is speculative; previous stage reports provide the ground truth of what actually landed (exact property names, exports, types) for ~300–500 tokens, preventing inter-stage hallucination and interface drift without bloating context.
- **Preserve Verifier Scope & Independence:** The `verifier` must receive ONLY the stage acceptance contract (`NN-slug.md`) and the stage diff (`git diff <base_commit>`). Never pass `NN-slug.detail.md`, the implementer's internal thoughts, or the decision log. The verifier exists to independently inspect diff correctness and test runtime behavior; feeding it internal plans invalidates verification.
- **Subagent Tool Permissions for Verifier:** When defining or spawning `verifier` via `define_subagent`, `enable_write_tools: true` MUST be set so that `run_command` is available in its environment (otherwise verification and test commands fail with `exit: 127`).
- **Pass Role Models:** Always resolve the role's model tier from `pipeline.json` (or `.agents/pipeline.json` override) and pass it when invoking subagents (`pro`, `flash`, `flash_lite`, `inherit`).

---

## 2. Directory Layout

All plan artifacts reside in `specs/<feature>/`:

```text
specs/<feature>/
  SPEC.md                    # plan-architect: Goal, context, approach, stages, non-goals
  STATE.md                   # plan-architect: Stage status table and branch metadata
  DECISIONS.md               # orchestrator: Decision log for unattended runs
  stages/NN-slug.md          # stage-architect: Acceptance contract and verification command
  stages/NN-slug.detail.md   # stage-architect: Task breakdown, large step specs, per-file plan
  stages/NN-slug.report.md   # orchestrator: Post-verification evidence and stage summary
```

If multiple features exist in `specs/`, identify the target feature or ask the user. Never guess.

---

## 3. Version Control & Branch Policy

### Git Repositories
- **One branch per feature:** Every stage of a feature is built on a single branch: `staged-build/<feature>`.
- The `Branch:` header in `specs/<feature>/STATE.md` is the single source of truth.
- **Stage 01:** Creates `staged-build/<feature>` from current HEAD (`git checkout -b`) and writes it to `STATE.md`.
- **Subsequent Stages:** Check out the recorded branch. Never branch per stage.
- **Clean Tree Requirement:** Before starting a stage, ensure `git status --porcelain -- ':!specs'` is clean. Uncommitted code changes outside `specs/` must halt the pipeline.
- **Never delete or force-reset branches** unless explicitly instructed by the user in `redo`.

### Jujutsu (`jj`) Repositories
- Run `jj new -m "stage NN: <title>"` per stage. Do not manipulate bookmarks unless requested.

---

## 4. Verdict & Flow Protocol

The execution flow for each stage is streamlined to:
`[stage-architect] -> [implementer] <-> [verifier] -> commit`

Subagents return explicit verdict tokens on their final line:
- `VERDICT: PASS` — Stage verification succeeded. Diff satisfies contract and all tests/commands pass.
- `VERDICT: FAIL` — Critical findings detected or verification/test commands failed. Triggers implementer self-healing loop.
- `REPLANNED` — Implementer identified that the stage specification itself was flawed or impossible against the codebase. Halts execution immediately and marks stage `blocked` in `STATE.md`.

### Retry Budgets
- **Verification Failures:** Max 2 fix $\leftrightarrow$ verify cycles (`implementer` $\leftrightarrow$ `verifier`).
- When `verifier` returns `VERDICT: FAIL`, findings are routed directly back to `implementer` to self-heal.
- If retry budget is exhausted, halt the run immediately and report all findings across attempts. Never force a pass.

---

## 5. Autonomy Policy (Unattended / YOLO Mode)

- **Major Decisions (Halt & Ask):** Scope changes, non-reversible data models/schemas, security/auth/credentials, destructive actions outside scope, conventions spanning many files, pipeline stoppages (implementer halted/replanned, retry budget exhausted).
- **Minor Decisions (Decide & Log):** Naming, placement in existing patterns, default constants/timeouts, log messages, test fixture structure.
  - Every minor decision must land as **one named place to change** (constant, default param, single config key).
  - Must be logged immediately to `specs/<feature>/DECISIONS.md`.
