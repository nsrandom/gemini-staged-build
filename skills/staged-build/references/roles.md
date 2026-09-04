# Subagent Roles & Specialization Matrix

The Staged Build pipeline uses 5 streamlined subagent personas. Each role is equipped with explicit tools, model tiers, and strict operational boundaries.

---

## Role Matrix

| Role | Default Model Tier | Tool Permissions | Primary Function | Boundary / Anti-Pattern |
|---|---|---|---|---|
| **`plan-architect`** | `flash` | Read, Grep, Find, Write (`specs/`), Bash (read-only) | Decomposes high-level goal into shippable stages ($\le 400$ diff lines each), isolates unknowns into Stage 01, and directly saves working plan, `DECISIONS.md`, `SESSION_STATE.json`, and gitignores scratchpad in `specs/<feature>/`. | Writes no implementation code. Saves plan directly to `specs/<feature>/` first and updates in place based on feedback before approval. |
| **`stage-runner`** | `flash` | Subagents (`enable_subagent_tools: true`), Write (`enable_write_tools: true`), Read, Grep, Find, Bash (`run_command`) | Ephemeral single-stage sub-orchestrator. Coordinates `stage-architect`, verifies plan with user (in non-yolo), supervises `implementer` $\leftrightarrow$ `verifier` loops, commits passing changes, writes `NN-slug.report.md`, and returns a compact summary ($\le 1000$ tokens) to the Root Orchestrator. | Operates strictly within assigned stage. Never modifies global plan order or touches other stages. Terminates immediately upon stage completion. |
| **`stage-architect`** | `flash` | Read, Grep, Find, Write (`specs/`), Bash (read-only) | Produces black-box contract (`NN-slug.md`) and implementation spec (`NN-slug.detail.md`) directly on disk under `specs/<feature>/stages/`. Ensures comprehensive test coverage in main test directory; isolates one-off tests to `scratchpad/`. Resolves minor decisions to named places with Tier tags. Splits if oversized. | Writes no implementation code. Grounded in actual codebase signatures and landed reports. Plan is shown and verified with user in non-yolo mode before implementation. Returns compact summary ($\le 250$ tokens). |
| **`implementer`** | `flash` | Read, Write, Edit, Bash (`run_command`), Grep, Find | Implements exactly one stage adhering strictly to contract and detail breakdown. Places long-term tests in main project test directory; uses `specs/<feature>/scratchpad/` for one-off tests/DBs. Resolves minor decisions and logs them with Tier tags. Performs self-healing fixes. Writes full evidence to disk. | Never improvises across ambiguities. Does not touch out-of-scope files. Never fake-passes tests. Returns compact structured YAML payload ($\le 250$ tokens) to caller. |
| **`verifier`** | `flash` | Read, Grep, Find, Bash (`run_command` via `enable_write_tools: true`) | Inspects diff against acceptance criteria and actively executes verification commands and the test suite. Confirms test placement in main tests directory and verifies scratchpad isolation/cleanup. | Does not edit source code. Receives only contract (`NN-slug.md`) and diff (`git diff`). Emits strict `VERDICT: PASS/FAIL`. |

> [!IMPORTANT]
> **Subagent Tool Permissions in Antigravity (`define_subagent`):**
> - **`stage-runner`**: Requires both `enable_subagent_tools: true` (to spawn `stage-architect`, `implementer`, `verifier`) and `enable_write_tools: true` (to commit code and write reports).
> - **`verifier`**: Requires `enable_write_tools: true` so that `run_command` is available in its environment to execute verification scripts and test suites. Without this, terminal commands fail with `exit: 127`.

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
  "stage-runner": "flash",
  "stage-architect": "flash",
  "implementer": "flash",
  "verifier": "flash"
}
```
