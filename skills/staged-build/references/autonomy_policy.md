# Autonomy Policy & Decision Logging

In unattended execution (`/staged-build:yolo`), the orchestrator drives all stages end-to-end without pausing between stages. Every judgement call is categorized as either **Major** (stops execution) or **Minor** (decided autonomously and logged).

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
  - Debugger returned `REPLANNED`.
  - Plan check fails after 2 revision cycles.
  - Review fails after 2 debug cycles.
  - Validation fails after 2 debug cycles.
  - Stage marked `blocked`.

---

## 2. Minor Decisions (Decide, Log, & Continue)

Decided autonomously without interrupting the user.

- **Local Naming:** Internal variables, helper function names, local types, test names, slugs.
- **Existing Patterns:** Placement within existing project directories and module structures.
- **Default Constants:** Setting local timeouts, retry limits, cache TTLs, or buffer sizes.
- **Messages & Logs:** Exact phrasing of error messages, log statements, and comments.
- **Test Structures:** Unit test fixture setup, table-driven test definitions, test case ordering.
- **Internal Ordering:** Order of independent tasks within a single stage.

---

## 3. Single Named Place Rule

Every minor decision must land in the code as **one named place to change**:
- A named constant (e.g. `const MAX_RETRIES = 3`) instead of hardcoded magic numbers.
- A default parameter value instead of duplicated values across call sites.
- A single configuration key instead of branching logic scattered in code.

Do not over-engineer abstractions, plugin interfaces, or configuration frameworks just to house a minor decision.

---

## 4. Decision Log (`specs/<feature>/DECISIONS.md`)

The orchestrator is the sole writer of `DECISIONS.md`. Subagents output their decisions in an `Autonomous decisions` section, and the orchestrator transcribes them immediately upon receiving them.

### Schema

```markdown
# Decisions — <feature>

Decisions taken without asking during `/staged-build:yolo`. Each is meant to be cheap to change; the "Change it here" line says where.

Status is `unconfirmed`, `confirmed`, or `changed → stage NN`.

## D01 — <Short Title>

- **Stage:** NN-slug
- **Decided by:** implementer | stage-architect | debugger | orchestrator
- **The call:** <what was genuinely undecided>
- **Decision:** <what was chosen>
- **Instead of:** <alternatives considered>
- **Because:** <rationale based on existing code or context>
- **Change it here:** `path/to/file.ext:line` — <named constant or default>
- **Status:** unconfirmed
```

---

## 5. Subagent Unattended Addendum

When running under `yolo`, append this exact block to the prompts for `stage-architect`, `implementer`, and `debugger`:

```markdown
---

## Unattended run — how to handle a judgement call

This is running unattended. Nobody will answer you mid-task, so a question you raise costs the whole run a stop.

**Stop and report when the call is major:** scope/criteria changes; non-reversible choices (data model, schema, wire format, public API, new dependency, behavior deletion); auth/credentials/secrets/billing/PII; destructive actions outside scope; cross-file conventions; or unresolved ambiguities. Stopping on these is expected and correct.

**Decide it yourself when the call is minor:** naming, placement in existing patterns, default values/constants, messages/logs, test structure, or internal step order.

**Every minor decision must land as one named place to change** (a named constant, default parameter, or single config key).

End your response with this exact section:

```
## Autonomous decisions

- **The call:** <what was genuinely undecided>
  **Decision:** <what you chose>
  **Instead of:** <the alternatives>
  **Because:** <one line rationale>
  **Change it here:** <file:line — the constant, default, or key>
```

If none were made, write the heading followed by `none`.
```

> [!IMPORTANT]
> Never send this addendum or the decision log to `plan-checker`, `reviewer`, or `validator`. Those roles act as independent judges.
