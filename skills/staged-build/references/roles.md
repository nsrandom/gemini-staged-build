# Subagent Roles & Specialization Matrix

The Staged Build pipeline uses 7 specialized subagent personas. Each role is equipped with explicit tools, model tiers, and strict operational boundaries.

---

## Role Matrix

| Role | Default Model Tier | Tool Permissions | Primary Function | Boundary / Anti-Pattern |
|---|---|---|---|---|
| **`plan-architect`** | `pro` | Read, Grep, Find, Write (`specs/`), Bash (read-only) | Decomposes high-level goal into shippable stages ($\le 400$ diff lines each) and isolates unknowns into Stage 01. | Writes no implementation code. Proposal pass writes no files at all. |
| **`stage-architect`** | `pro` | Read, Grep, Find, Write (`specs/`), Bash (read-only) | Produces black-box contract (`NN-slug.md`) and implementation spec (`NN-slug.detail.md`). Splits if oversized. | Writes no implementation code. Grounded in actual codebase signatures. |
| **`plan-checker`** | `pro` | Read, Grep, Find, Bash (read-only) | Falsifies the stage plan and large step specs against live codebase before coding starts. | Read-only; cannot write or edit files. Does not redesign the plan. |
| **`implementer`** | `flash` | Read, Write, Edit, Bash, Grep, Find | Implements exactly one stage adhering strictly to the contract and detail breakdown. | Never improvises or guesses across ambiguities. Does not touch out-of-scope files. |
| **`reviewer`** | `pro` | Read, Grep, Find, Bash (read-only) | Conducts independent code review of diff against the contract. Classifies Critical/Warning/Suggestion. | Read-only; cannot write or edit files. Emits strict `VERDICT: PASS/FAIL`. |
| **`validator`** | `flash` | Read, Bash, Grep, Find | Executes black-box verification command and test suite. Observes and captures evidence. | Receives ONLY the contract. Never receives detail plans, diffs, or verdicts. Never fixes code. |
| **`debugger`** | `pro` | Read, Edit, Bash, Grep, Find | Reproduces failures, performs root cause analysis, applies minimal surgical fixes, or flags `REPLANNED`. | Does not patch symptoms without finding root cause. Only replans if spec was genuinely impossible. |

---

## Model Routing Configuration

Antigravity resolves model selection via `pipeline.json` (or workspace override in `.agents/pipeline.json`).

Supported Model Specifiers:
- `"pro"`: Gemini Pro reasoning tier (recommended for planning, checking, reviewing, debugging).
- `"flash"`: Gemini Flash tier (fast, cost-effective, high-throughput execution for implementation and test running).
- `"flash_lite"`: Lightweight tier for quick lookups.
- `"inherit"`: Inherits parent session model.

Example `pipeline.json`:
```json
{
  "plan-architect": "pro",
  "stage-architect": "pro",
  "plan-checker": "pro",
  "implementer": "flash",
  "reviewer": "pro",
  "validator": "flash",
  "debugger": "pro"
}
```
