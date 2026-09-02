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
| `stage plan "<goal>"` | Interactive 2-pass planning conversation with `plan-architect`. Writes `SPEC.md` and `STATE.md`. | Stops after writing plan. Never implements. |
| `stage next [--new-branch]` | Executes exactly **one** pending stage through the streamlined pipeline: specify $\to$ implement $\leftrightarrow$ verify. | Stops after verifying stage and producing report. Never auto-advances. |
| `stage yolo ["<goal>"]` | Runs the entire plan end-to-end unattended with context pruning between stages. Resolves minor decisions, logs to `DECISIONS.md`, and commits each stage. | Stops only on major architectural decisions, unrecoverable failures, or when all stages finish. |
| `stage status` | Displays active plan state, current git/jj branch, and most recent stage report. | Read-only. |
| `stage redo` | Discards current stage work with confirmation, resets stage to `pending`, and re-runs `next`. | Stops after user confirmation. |

---

## Architectural Principles & Invariants

1. **Orchestrator Separation:** The orchestrator coordinates subagents, manages disk files, and interacts with the user. **The orchestrator writes no implementation code and reviews no code.**
2. **Context Isolation & Inter-Stage Bridging:** Subagents start blank and share no conversational context. All file dependencies and prior findings must be passed verbatim in the delegation prompt. When invoking `stage-architect` for Stage $N$ ($N > 1$), pass `SPEC.md`, `STATE.md`, and the **Summary & Changes sections** of all previous `stages/*.report.md` files (stripping raw execution logs) to ground specifications in landed code without token bloat.
3. **Verifier Independence & Scope:** The `verifier` receives **ONLY the stage acceptance contract (`NN-slug.md`)** and the stage diff (`git diff <base_commit>`). Never pass implementation specs (`.detail.md`), implementer thoughts, or decision logs.
4. **Single Branch per Feature:** One Git branch `staged-build/<feature>` for all stages of a feature. Recorded on the `Branch:` line of `specs/<feature>/STATE.md`.

---

## Directory & File Layout

```text
specs/<feature>/
  SPEC.md                    # High-level architecture, approach, stages, non-goals
  STATE.md                   # Stage tracker table and branch binding
  DECISIONS.md               # Log of minor decisions taken in yolo mode
  stages/
    NN-slug.md               # Black-box acceptance contract & verification command
    NN-slug.detail.md        # Deep implementation plan & large step breakdowns
    NN-slug.report.md        # Stage completion report with verification evidence
```

---

## Subagent Setup & Model Routing

When delegating, resolve model tiers from `pipeline.json` (or `.agents/pipeline.json` override):

```json
{
  "plan-architect": "flash",
  "stage-architect": "flash",
  "implementer": "flash",
  "verifier": "flash"
}
```

### Spawning Subagents in Antigravity

Subagents are invoked using `invoke_subagent` (or defined via `define_subagent`):
- `TypeName`: The role name (`plan-architect`, `stage-architect`, `implementer`, `verifier`).
- `Role`: Descriptive role title (e.g. `Staged Build Verifier`).
- `Model`: Resolved model tier (`"flash"`, `"pro"`, `"flash_lite"`, `"inherit"`).
- `Workspace`: `"inherit"`.
- `Prompt`: Subagent persona instructions concatenated with the verbatim task payload.

> [!IMPORTANT]
> **Subagent Tool Permissions for Verifier:** When defining or spawning `verifier` via `define_subagent`, `enable_write_tools: true` MUST be set so that `run_command` is available in its environment (otherwise terminal commands fail with `exit: 127`).

---

## Workflows

### 1. `stage plan "<goal>"`

Planning is an interactive conversation to settle the scope and sequence before writing files.

```mermaid
flowchart TD
    Start([User provides Goal]) --> ProposalPass[Delegate to plan-architect\nProposal Pass: Write NO files]
    ProposalPass --> UserReview{Present Proposal\n& Inquire via ask_question}
    UserReview -- "User requests edits" --> RevisionPass[Delegate revision to\nplan-architect with feedback]
    RevisionPass --> UserReview
    UserReview -- "User Approves" --> WritePass[Delegate to plan-architect\nWrite Pass]
    WritePass --> WriteFiles[Write SPEC.md & STATE.md\nunder specs/<feature>/]
    WriteFiles --> Stop([Show stage summary & STOP])
```

1. **Proposal Pass:** Invoke `plan-architect` on model `flash` with the goal and instruction: `"PROPOSAL PASS: Write no files to disk. Read codebase, assess feasibility, isolate unknowns into Stage 01, and propose numbered stages and specific questions."`
2. **User Alignment:** Present the proposal to the user.
   - Use `ask_question` for discrete choices, highlighting defaults.
   - Solicit additions, removals, renames, or reordering of stages.
3. **Iterate:** If the user requests changes, pass their feedback back to `plan-architect` for a revised proposal.
4. **Write Pass:** Upon explicit user approval, invoke `plan-architect` with `"WRITE PASS: Follow user approvals. Create specs/<feature>/SPEC.md and specs/<feature>/STATE.md."`
5. **Stop:** Present the final stage table and halt.

---

### 2. `stage next [--new-branch]`

Executes exactly **one** pending stage.

```mermaid
flowchart TD
    A[Read STATE.md & pick first non-done stage] --> B[Verify clean git status & checkout feature branch]
    B --> C[Mark stage in-progress in STATE.md]
    C --> D[Delegate to stage-architect\nWrites NN-slug.md & NN-slug.detail.md\nGrounded by prior stage reports]
    D --> E[Record Stage Base Commit\nDelegate to implementer]
    E --> F[Delegate to verifier\nInspects diff & executes commands]
    F -- FAIL (max 2) --> G[Implementer Self-Healing\nFix root cause & re-verify] --> F
    F -- PASS --> H[Write NN-slug.report.md\nMark done in STATE.md\nSuggest commit & STOP]
```

1. **Select Stage:** First non-`done` row in `STATE.md`. If `blocked`, halt and explain why.
2. **VCS Setup:**
   - Verify `git status --porcelain -- ':!specs'` is clean. If uncommitted code exists, halt.
   - Ensure checkout of `staged-build/<feature>` (or create on Stage 01).
3. **Specify Stage:**
   - Invoke `stage-architect` (model `flash`) with `SPEC.md` and the stage's row.
   - For Stage $N > 1$, also pass the **Summary & Changes sections** of all previous `stages/*.report.md` files (strip raw terminal/test execution logs).
   - `stage-architect` creates `NN-slug.md` (contract) and `NN-slug.detail.md` (implementation spec).
   - If it splits the stage or reports a conflict, stop and report.
4. **Implement:**
   - Record base commit hash: `git rev-parse HEAD`.
   - Invoke `implementer` (model `flash`) with full text of `NN-slug.md` and `NN-slug.detail.md`.
5. **Verify & Self-Heal:**
   - Obtain stage diff: `git diff <base_commit>` plus untracked files.
   - Invoke `verifier` (model `flash`, `enable_write_tools: true`) with `NN-slug.md` and the diff.
   - `verifier` inspects the diff against criteria and executes the verification command and project test suite using `run_command`.
   - **On FAIL:** Route findings directly back to `implementer` to self-heal (max 2 cycles). Implementer reproduces the issue, applies surgical fixes, and verifies locally.
   - **If Implementer outputs `REPLANNED`:** Mark stage `blocked` in `STATE.md` and stop immediately.
6. **Complete:**
   - Write `specs/<feature>/stages/NN-slug.report.md`.
   - Mark stage `done` in `STATE.md`.
   - Suggest `git commit` message. **Stop.**

---

### 3. `stage yolo ["<goal>"]`

Unattended execution of all stages from start to finish with inter-stage context pruning.

1. **Setup:**
   - If goal provided and no plan exists, run the interactive planning flow first.
   - Initialize `specs/<feature>/DECISIONS.md`.
   - Ensure clean branch setup.
2. **Execution Loop:**
   - Pick next pending stage.
   - Apply the **Unattended Addendum** (from `references/autonomy_policy.md`) to `stage-architect` and `implementer`.
   - Transcribe all `Autonomous decisions` into `DECISIONS.md` immediately.
   - Delegate verification to `verifier` with `NN-slug.md` and the stage diff.
   - On verification PASS: Commit automatically: `git add -A && git commit -m "stage NN: <title>"`.
   - **Context Pruning:** Upon completing and committing a stage, the orchestrator MUST NOT retain or re-paste old stage implementation details (`.detail.md`), raw diffs, or verbose verification/test logs into subsequent prompts. Only `SPEC.md`, updated `STATE.md`, and concise `report.md` summaries (~300–500 tokens) are carried over into subsequent stage prompts.
   - Immediately proceed to the next stage.
3. **Major Stop Conditions:**
   - Implementer stalls, stage-architect splits stage, implementer returns `REPLANNED`, or verification retry budget (2 cycles) is exhausted.
   - Halt, output the blocker in subagent's verbatim words, and leave repository intact for user inspection.
4. **Decision Review (Final Stage):**
   - When all implementation stages are `done`, append a final stage to `STATE.md`: `Confirm autonomous decisions`.
   - Present all unconfirmed decisions from `DECISIONS.md`.
   - Use `ask_question` (multi-select) to ask the user which decisions to modify.
   - If edits requested, invoke `plan-architect` write pass to append new remediation stages and loop back.
   - If confirmed, mark `confirmed` in `DECISIONS.md` and commit.

---

### 4. `stage status`

1. Run context resolver script: `python3 .agents/plugins/staged-build/skills/staged-build/scripts/context_resolver.py`.
2. Display feature name, current VCS branch, `STATE.md` table, and the latest stage report summary.

---

### 5. `stage redo`

1. Identify active `in-progress` stage (or last `done` stage if specified).
2. Prompt user to confirm discarding uncommitted/stage work.
3. Reset stage changes (`git reset --hard <base_commit>`).
4. Set row status back to `pending` in `STATE.md` and delete `NN-slug.report.md`.
5. Trigger `stage next`.
