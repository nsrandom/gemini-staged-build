# Autonomy Policy & Decision Logging

In both supervised stage execution (`stage next`) and unattended execution (`stage yolo`), every judgement call is categorized as either **Major** (stops execution) or **Minor** (decided autonomously, placed into a single named place, and logged). Logging minor decisions in `stage next` allows the implementation flow to proceed smoothly without stopping on minor choices, while leaving a clear audit trail for deferred review and adjustment via `stage cleanup`.

---

## 1. Major Decisions (Halt & Ask)

The pipeline stops immediately. The orchestrator explains the exact blocker, presents the context, and prompts the user via `ask_question` or conversational dialogue.

- **Scope & Criteria Changes:** Altering what is built, changing acceptance criteria, modifying non-goals, or changing the stage execution order.
- **Non-Reversible Architectural Decisions:** Data model schemas, database migrations, on-disk or wire formats, public APIs, CLI flag signatures, introducing new dependencies, or deleting existing features.
- **Security, Auth & Compliance:** Authentication, permission models, credentials, tokens, secrets, encryption, billing, or user data (PII).
- **Destructive or Outward Actions:** Deleting files/data outside stage scope, force-pushing, deploying, or invoking external mutating services.
- **Project-Wide Conventions:** Introducing a style or convention that spans many files and is not already established.
- **Ambiguous Alternatives:** Two interpretations lead to materially different architectures and codebase evidence does not clarify intent.
- **Pipeline Failures:**
  - Implementer halted rather than guessed.
  - Stage-architect split the stage or flagged codebase conflicts.
  - Implementer returned `REPLANNED`.
  - Verification fails after 2 fix $\leftrightarrow$ verify cycles (`implementer` $\leftrightarrow$ `verifier`).
  - Stage marked `blocked`.

---

## 2. Minor Decisions (Decide, Log, & Continue)

Decided autonomously without interrupting the user during both `stage next` and `stage yolo`. Minor decisions are classified into two tiers to streamline subsequent review:

### Tier 1: Routine / Standard Conventions
Routine implementation choices that follow established idioms or localized convenience:
- **Local Naming:** Internal variables, helper function names, local types, test names, slugs.
- **Existing Patterns:** Placement within existing project directories and module structures, test file colocation.
- **Default Constants:** Setting local timeouts, retry limits, cache TTLs, or buffer sizes.
- **Messages & Logs:** Exact phrasing of error messages, log statements, alert strings, and comments.
- **CLI Option Flags:** Non-breaking flag aliases or formatting defaults.
- **Test Structures:** Unit test fixture setup, table-driven test definitions, test case ordering.
- **Internal Ordering:** Order of independent tasks within a single stage.

### Tier 2: Substantive Architecture & Behavior
Decisions that subtly shape behavior, contract boundaries, or validation semantics:
- **Type Validation:** Strict vs. loose type parsing (e.g. rejecting non-boolean JSON values vs. coercing truthy values).
- **Evaluation Ordering:** Query or filter evaluation ordering (e.g. short-circuiting conditions in WHERE clauses).
- **Public Contract Additions:** Supplementary non-breaking helper methods or optional parameters exposed on public contracts.
- **Fallback Behavior:** Fallback strategy when optional services or configurations are absent.

---

## 3. Single Named Place Rule

Every minor decision must land in the code as **one named place to change**:
- A named constant (e.g. `const MAX_RETRIES = 3`) instead of hardcoded magic numbers.
- A default parameter value instead of duplicated values across call sites.
- A single configuration key instead of branching logic scattered in code.

Do not over-engineer abstractions, plugin interfaces, or configuration frameworks just to house a minor decision.

---

## 4. Decision Log (`specs/<feature>/DECISIONS.md`)

The orchestrator is the sole writer of `DECISIONS.md`. Subagents output their decisions in an `Autonomous decisions` section, and the orchestrator transcribes them immediately upon receiving them in both `stage next` and `stage yolo`.

### Schema

```markdown
# Decisions — <feature>

Decisions taken without asking during development (`stage next` or `stage yolo`). Each is meant to be cheap to change; the "Change it here" line says where.

Status is `unconfirmed`, `confirmed`, `rejected`, `deferred`, or `modified: <details>`.

## D01 — <Short Title>

- **Stage:** NN-slug
- **Tier:** 1 | 2
- **Decided by:** implementer | stage-architect | orchestrator
- **The call:** <what was genuinely undecided / problem statement>
- **Decision:** <what was chosen>
- **Instead of:** <alternatives considered>
- **Tradeoffs & Implications:** <trade-offs made, alternatives passed over, and downstream consequences>
- **Because:** <rationale based on existing code or context>
- **Change it here:** `path/to/file.ext:line` — <named constant or default>
- **Status:** unconfirmed
```

---

## 5. Tiered Decision Walkthrough & Remediation Protocol (`stage cleanup`)

At feature completion or on demand via `stage cleanup`, the orchestrator guides the user through recorded decisions.

### Walkthrough Sequence:
1. **Context Reset:** Clear conversational history to drop prompt size from ~160K tokens to ~10K tokens. Reload ONLY:
   - `specs/<feature>/SESSION_STATE.json`
   - `specs/<feature>/SPEC.md`, `STATE.md`, `DECISIONS.md`
   - Directory listing of `specs/<feature>/scratchpad/`
2. **Tier 1 Consolidated Batch Review:** Present all Tier 1 decisions as a single consolidated review modal/table:
   > *"N routine decisions followed standard codebase conventions (see table). [Confirm All N (Recommended)] or [Select specific decision to inspect]."*
   - If the user selects **Confirm All N**, mark all Tier 1 decisions as `confirmed` in `DECISIONS.md`.
   - If the user flags specific decisions for closer review, queue those flagged decisions for the individual walkthrough.
3. **Tier 2 (and Flagged) Individual Walkthrough Loop:** Walk through Tier 2 decisions and user-flagged Tier 1 decisions **one at a time**. For each decision, present:
   - **The Problem:** What was unresolved or what challenge was encountered.
   - **What Decision Was Taken:** The choice made and its exact location in code (`Change it here: path/to/file:line`).
   - **Tradeoffs, Alternatives & Implications:** Alternatives considered, what was traded off, and downstream consequences.
4. **User Actions:**
   - **Confirm:** Mark `confirmed` in `DECISIONS.md`.
   - **Reject the decision:** Mark `rejected` in `DECISIONS.md`. Record user's reason and replacement direction.
   - **Defer:** Add to the deferred queue to be re-evaluated after the initial loop finishes.
   - **Ask a follow-up question:** Provide answers, explain nuances, and re-prompt user with the options.
   - **Suggest a modification to the decision:** Mark `modified: <details>` in `DECISIONS.md`. Record specific adjustments.
5. **Deferred Resolution:** Once the initial loop finishes, process any deferred decisions until all are resolved.
6. **Cleanup Stage Creation & Execution:**
   - If any decisions were rejected or modified, **or** if `specs/<feature>/scratchpad/` exists:
     - Add a new stage to `specs/<feature>/STATE.md`: `Stage NN: Cleanup and decision remediation`.
     - In the stage spec, detail:
       - Remediation for rejected decisions.
       - Code changes for modified decisions at their named single places.
       - Deletion of `specs/<feature>/scratchpad/` and temporary data/databases.
       - Verification that all long-term tests continue to pass.
     - Immediately launch design and implementation of the cleanup stage via `stage-runner` (`stage-architect` $\to$ verify plan $\to$ `implementer` $\leftrightarrow$ `verifier` $\to$ commit).
7. **Unified Feature `architecture.md` Synthesis:**
   - At the conclusion of `stage cleanup` (after Tier 1 batch review, Tier 2 walkthroughs, any remediation stages, and scratchpad deletion), synthesize a single, permanent system reference: `specs/<feature>/architecture.md`.
   - **Token-Efficient Single-Pass Generation:** Synthesize directly from disk metadata already verified (`DECISIONS.md`, `Summary & Changes` of all `stages/*.report.md`, `SESSION_STATE.json`) without re-reading source code.
   - **Standardized Cheat-Sheet Schema ($\le 1,000\text{--}1,500$ tokens):**
     1. Executive Summary & Entrypoints
     2. Module & Directory Map
     3. Public API, CLI Contracts & JSON Schemas
     4. Key Invariants & Data Flow
     5. Configuration Keys & Defaults
     6. Verification & Test Suite Command
   - **Downstream Consumption:** Future features integrating with this feature (or future maintenance tasks) should read `specs/<feature>/architecture.md` as the authoritative, compact source of truth instead of re-reading dozens of historical stage files or running brute-force code searches.

---

## 6. Subagent Minor Decisions Addendum

Append this block to the prompts for `stage-architect` and `implementer` in both `stage next` and `stage yolo` modes:

```markdown
---

## Minor decisions — how to handle a judgement call

**Stop and report when the call is major:** scope/criteria changes; non-reversible choices (data model, schema, wire format, public API, new dependency, behavior deletion); auth/credentials/secrets/billing/PII; destructive actions outside scope; cross-file conventions; or unresolved ambiguities. Stopping on these is expected and correct.

**Decide it yourself when the call is minor:** naming, placement in existing patterns, default values/constants, messages/logs, test structure, or internal step order.
- **Tier 1:** Routine conventions (naming, constants, log messages, test layout).
- **Tier 2:** Substantive behavior (type validation, filter/eval ordering, public helper additions).

**Every minor decision must land as one named place to change** (a named constant, default parameter, or single config key).

End your response with this exact section:

```
## Autonomous decisions

- **The call:** <what was genuinely undecided>
  **Tier:** 1 | 2
  **Decision:** <what you chose>
  **Instead of:** <the alternatives>
  **Tradeoffs & Implications:** <trade-offs and consequences>
  **Because:** <one line rationale>
  **Change it here:** <file:line — the constant, default, or key>
```

If none were made, write the heading followed by `none`.
```

> [!IMPORTANT]
> Never send this addendum or the decision log to `verifier`. The verifier acts as an independent judge.
