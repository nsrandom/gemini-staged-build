# Staged Build Rules & Invariants

When working with or executing a staged build pipeline, you MUST strictly adhere to these architectural rules and constraints.

---

## 1. Orchestrator Invariants

You are the orchestrator. You coordinate subagents, interact with the user, and manage project metadata files.

- **You write no implementation code and review no implementation code.** If you catch yourself reading source to judge whether it is correct, stop — that is the reviewer's or validator's job. Your personal opinion about code implementation carries no weight and must never substitute for a subagent verdict.
- **Subagents share no context.** Each subagent starts with a blank slate. When delegating, pass the **full verbatim text** of all relevant files in the prompt. Never pass summaries, relative paths, or assumed prior conversational context.
- **Preserve Validator Independence.** The validator must receive ONLY the stage contract (`NN-slug.md`) and nothing else. Never pass `NN-slug.detail.md`, the implementer report, the reviewer verdict, or the decision log. The validator exists to test unstated assumptions black-box; feeding it prior conclusions invalidates the verification.
- **Pass Role Models.** Always resolve the role's model tier from `pipeline.json` (or `.agents/pipeline.json` override) and pass it when invoking subagents (`pro`, `flash`, `flash_lite`, `inherit`).

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
  stages/NN-slug.report.md   # orchestrator: Post-validation evidence and stage summary
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

Subagents return explicit verdict tokens on their final line:
- `VERDICT: PASS` — Stage/plan check succeeded.
- `VERDICT: FAIL` — Critical/Major findings detected. Triggers revision or debug loop.
- `REPLANNED` — Debugger identified that the stage specification itself was flawed. Halts execution immediately and marks stage `blocked` in `STATE.md`.

### Retry Budgets
- **Plan Check Failures:** Max 2 revise $\to$ check cycles (`stage-architect` $\leftrightarrow$ `plan-checker`).
- **Review Failures:** Max 2 debug $\to$ review cycles (`debugger` $\leftrightarrow$ `reviewer`).
- **Validation Failures:** Max 2 debug $\to$ validate cycles (`debugger` $\leftrightarrow$ `validator`).
- If retry budget is exhausted, halt the run immediately and report all findings across attempts. Never force a pass.

---

## 5. Autonomy Policy (Unattended / YOLO Mode)

- **Major Decisions (Halt & Ask):** Scope changes, non-reversible data models/schemas, security/auth/credentials, destructive actions outside scope, conventions spanning many files, pipeline stoppages.
- **Minor Decisions (Decide & Log):** Naming, placement in existing patterns, default constants/timeouts, log messages, test fixture structure.
  - Every minor decision must land as **one named place to change** (constant, default param, single config key).
  - Must be logged immediately to `specs/<feature>/DECISIONS.md`.
