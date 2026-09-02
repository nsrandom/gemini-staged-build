# Subagent Roles & Specialization Matrix

The Staged Build pipeline uses 4 streamlined subagent personas. Each role is equipped with explicit tools, model tiers, and strict operational boundaries.

---

## Role Matrix

| Role | Default Model Tier | Tool Permissions | Primary Function | Boundary / Anti-Pattern |
|---|---|---|---|---|
| **`plan-architect`** | `flash` | Read, Grep, Find, Write (`specs/`), Bash (read-only) | Decomposes high-level goal into shippable stages ($\le 400$ diff lines each), isolates unknowns into Stage 01, and directly saves working plan to `specs/<feature>/`. | Writes no implementation code. Saves plan directly to `specs/<feature>/` first and updates in place based on feedback before approval. |
| **`stage-architect`** | `flash` | Read, Grep, Find, Write (`specs/`), Bash (read-only) | Produces black-box contract (`NN-slug.md`) and implementation spec (`NN-slug.detail.md`) directly on disk under `specs/<feature>/stages/`, grounded in prior stage report summaries. Splits if oversized. | Writes no implementation code. Grounded in actual codebase signatures and landed reports. Plan is shown and verified with user in non-yolo mode before implementation. |
| **`implementer`** | `flash` | Read, Write, Edit, Bash (`run_command`), Grep, Find | Implements exactly one stage adhering strictly to the contract and detail breakdown. Performs self-healing fix passes if verification fails. | Never improvises across ambiguities. Does not touch out-of-scope files. Never fake-passes tests. |
| **`verifier`** | `flash` | Read, Grep, Find, Bash (`run_command` via `enable_write_tools: true`) | Inspects diff against acceptance criteria and actively executes verification commands and the test suite. | Does not edit source code. Receives only contract (`NN-slug.md`) and diff (`git diff`). Emits strict `VERDICT: PASS/FAIL`. |

> [!IMPORTANT]
> **Subagent Tool Permissions for `verifier`**: In Antigravity's `define_subagent`, `run_command` requires `enable_write_tools: true`. When defining or invoking `verifier`, you MUST set `enable_write_tools: true` so that `run_command` is available in its environment to execute verification scripts and test suites. Without this, terminal commands fail with `exit: 127`.

---

## Model Routing Configuration

Antigravity resolves model selection via `pipeline.json` (or workspace override in `.agents/pipeline.json`).

Supported Model Specifiers:
- `"flash"`: Gemini Flash tier (fast, cost-effective, high-throughput execution for all pipeline roles).
- `"pro"`: Gemini Pro reasoning tier (available for higher complexity planning or heavy debugging overrides).
- `"flash_lite"`: Lightweight tier for quick lookups.
- `"inherit"`: Inherits parent session model.

Current `pipeline.json`:
```json
{
  "plan-architect": "flash",
  "stage-architect": "flash",
  "implementer": "flash",
  "verifier": "flash"
}
```
