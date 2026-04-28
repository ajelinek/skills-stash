# Standalone Skills Migration Plan

## Purpose

This plan covers the migration work that was intentionally left out of the current
SpecFlow migration.

These items should be recreated as standalone installable skills under `skill/`.
They are not part of the SpecFlow product surface and should not be placed under
`SpecFlow/skills/`.

---

## Relationship To SpecFlow

The current `old-vibes/MIGRATION-PLAN.md` is a SpecFlow-specific migration plan.
It explicitly excludes several content classes from the SpecFlow bundle:

- standards skills such as TypeScript, React, testing, data, and error handling
- deep pattern libraries
- some removed or deferred agents whose behavior may still be valuable as
  standalone skills
- old `rules/` and `fragments/` content that should not be mechanically ported
  into SpecFlow workflows

This document is the follow-on plan for that excluded material.

Some shared support capabilities may live inside the SpecFlow bundle without being
numbered SpecFlow workflow skills. Those support skills are not tracked in this
standalone migration plan.

The goal here is not to preserve the old `vibing` file structure. The goal is to
extract the durable guidance, package it as standalone skills, and make each skill
useful on its own outside SpecFlow.

---

## Target Structure

Each standalone skill lives in its own directory under `skill/`.

The catalog should prefer larger, technology-based skills instead of many narrow
micro-skills.

```text
skill/
├── MIGRATION-PLAN.md
├── MIGRATION-STATUS.md
├── README.md
│
├── typescript-engineering/
│   └── SKILL.md
├── firebase/
│   └── SKILL.md
├── postgres-database-design/
│   └── SKILL.md
├── apollo/
│   └── SKILL.md
├── react/
│   └── SKILL.md
├── solid.js/
│   └── SKILL.md
├── astro.js/
│   └── SKILL.md
├── testing/
│   ├── SKILL.md
│   ├── references/
│   └── examples/
├── ui-engineering/
│   └── SKILL.md
├── firebase-dynamic-ports-setup/
│   ├── SKILL.md
│   ├── references/
│   └── examples/
│
├── seo/
│   └── SKILL.md
```

The exact final set may change during authoring, but new skills should generally be:

- technology-based
- broad enough to be worth installing
- small enough that their trigger conditions remain clear

---

## Migration Principles

- Build standalone skills from first principles using old `vibing` content only as
  source material.
- Do not copy old `rules/`, `fragments/`, or agent prompts verbatim into new
  `SKILL.md` files.
- One old file does not automatically equal one new skill. Merge or split based on
  user-facing utility.
- Prefer skills that are reusable across projects instead of skills that encode one
  product's exact defaults.
- Keep SpecFlow-specific workflow behavior out of these skills.
- If a piece of guidance is really a pattern library, decide whether it belongs in a
  standalone skill or should remain documented elsewhere.
- Use supporting `references/`, `examples/`, and `scripts/` folders only when they
  materially improve usability.
- Pattern-heavy skills with substantial real code examples are valid standalone
  skills when the pattern is reusable and the examples materially help the user.

---

## Scope

This migration plan covers three buckets.

### 1. Standards skills

These are the old `vibing/rules/` files that were excluded from SpecFlow because
they are general engineering guidance rather than SpecFlow workflow content.

### 2. Pattern-derived skills

These come from `old-vibes/vibing/patterns/` when the content is actionable enough
to become an installable skill rather than a passive reference document.

### 3. Deferred or removed agent behavior worth preserving

If an old agent represented a reusable capability that is still broadly useful, it
should be recast as a standalone skill rather than recreated as a persona agent.

---

## Source Inventory

### Standards rules

Foundation:

- `old-vibes/vibing/rules/common/foundation/general-rules.md`
- `old-vibes/vibing/rules/common/foundation/typescript-guidelines.md`
- `old-vibes/vibing/rules/common/foundation/error-handling-guidelines.md`

Apollo:

- `old-vibes/vibing/rules/apollo/apollo-client-guidelines.md`
- `old-vibes/vibing/rules/apollo/apollo-server-guidelines.md`
- `old-vibes/vibing/rules/apollo/apollo-store-architecture.md`
- `old-vibes/vibing/rules/apollo/apollo-react-state-integration.md`
- `old-vibes/vibing/rules/apollo/apollo-api-change-rules.md`

React:

- `old-vibes/vibing/rules/react/react-component-guidelines.md`
- `old-vibes/vibing/rules/react/react-state-management.md`
- `old-vibes/vibing/rules/react/react-state-with-swr.md`
- `old-vibes/vibing/rules/react/react-testing-guidelines.md`
- `old-vibes/vibing/rules/react/react-zustand-patterns.md`

Solid:

- `old-vibes/vibing/rules/solid.js/solidjs-component-guidelines.md`
- `old-vibes/vibing/rules/solid.js/solid-state-management.md`
- `old-vibes/vibing/rules/solid.js/solid-testing-guidelines.md`

Astro:

- `old-vibes/vibing/rules/astro.js/astro-component-guidelines.md`
- `old-vibes/vibing/rules/astro.js/astro-project-structure.md`

UI and accessibility:

- `old-vibes/vibing/rules/common/ui/ui-component-guidelines.md`
- `old-vibes/vibing/rules/common/ui/ui-foundational-component-principles.md`
- `old-vibes/vibing/rules/common/ui/ui-project-structure.md`
- `old-vibes/vibing/rules/common/ui/ui-styling-guidelines.md`
- `old-vibes/vibing/rules/common/ui/ui-theme.md`
- `old-vibes/vibing/rules/common/ui/ui-form-management.md`
- `old-vibes/vibing/rules/common/ui/ui-data-store-architecture.md`
- `old-vibes/vibing/rules/common/ui/ui-accessibility-guidelines.md`

Backend and data:

- `old-vibes/vibing/rules/common/backend/firebase-integration.md`
- `old-vibes/vibing/rules/common/data/data-attribute-naming-conventions.md`
- `old-vibes/vibing/rules/common/data/data-object-store-persistent.md`
- `old-vibes/vibing/rules/common/data/data-relational-persistent.md`

Testing:

- `old-vibes/vibing/rules/common/testing/test-general.md`
- `old-vibes/vibing/rules/common/testing/test-context.md`
- `old-vibes/vibing/rules/common/testing/test-e2e.md`
- `old-vibes/vibing/rules/common/testing/test-e2e-page-object.md`
- `old-vibes/vibing/rules/common/testing/test-e2e-tags.md`
- `old-vibes/vibing/rules/common/testing/test-gherkin-definition.md`
- `old-vibes/vibing/rules/common/testing/test-setup-examples.md`

Fragments to absorb:

- `old-vibes/vibing/fragments/engineer-guardrails.md`
- `old-vibes/vibing/fragments/engineer-principles.md`

### Patterns

- `old-vibes/vibing/patterns/firebase-dynamic-ports-setup.md`
- `old-vibes/vibing/patterns/test-context-and-data-generation-pattern.md`
- `old-vibes/vibing/patterns/foundational-ui-components.md`
- `old-vibes/vibing/patterns/astro-seo.md`

The `old-vibes/vibing/modifiers/` directory is not part of this standalone-skills
migration flow.

SpecFlow-owned exception:

- `old-vibes/vibing/modifiers/agent-context-manager.md`

### Deferred or removed agents to reassess

- `old-vibes/vibing/agents/research-agent.md`
- `old-vibes/vibing/agents/seo-specialist.md`
- `old-vibes/vibing/agents/domain-expert.md`

These should only become standalone skills if their behavior is still useful after
removing persona framing and project-specific assumptions.

SpecFlow-owned exception:

- Research behavior derived from `research-agent.md` is packaged as
  `SpecFlow/skills/deep-research/`, not as a standalone `skill/` package.

---

## Proposed Skill Mapping

This is the current recommended grouping. It deliberately merges many narrower
source documents into a smaller set of broader skills.

| Proposed skill | Primary source material | Notes |
| --- | --- | --- |
| `typescript-engineering` | `general-rules.md`, `typescript-guidelines.md`, `error-handling-guidelines.md`, `data-attribute-naming-conventions.md`, `engineer-guardrails.md`, `engineer-principles.md`, selected generally useful guidance from `backend-engineer.md` | Broad TypeScript engineering skill covering shared implementation, quality, and TypeScript-first practices across frontend and backend work |
| `firebase` | `firebase-integration.md`, `data-object-store-persistent.md` | Firebase-specific application, Firestore, and document-store guidance kept separate from the general TypeScript skill |
| `postgres-database-design` | `data-relational-persistent.md`, a PostgreSQL-adapted version of `data-attribute-naming-conventions.md` | PostgreSQL-focused relational schema, persistence design, and database-specific naming guidance |
| `apollo` | `apollo-client-guidelines.md`, `apollo-server-guidelines.md`, `apollo-store-architecture.md`, `apollo-react-state-integration.md`, `apollo-api-change-rules.md` | One larger GraphQL and Apollo skill |
| `react` | `react-component-guidelines.md`, `react-state-management.md`, `react-state-with-swr.md`, `react-zustand-patterns.md`, plus React-specific portions of `foundational-ui-components.md` and relevant common UI rules | One broad React skill covering components, state, SWR, Zustand, shared UI practices, and React-based foundational component examples; React testing guidance belongs in `testing` |
| `solid.js` | `solidjs-component-guidelines.md`, `solid-state-management.md`, `solid-testing-guidelines.md`, plus relevant common UI rules and rebuilt Solid-based foundational component examples | One broad Solid skill with shared UI practices and Solid-specific foundational component examples |
| `astro.js` | `astro-component-guidelines.md`, `astro-project-structure.md`, plus relevant common UI rules where applicable | One broad Astro skill with shared UI practices where they truly apply |
| `testing` | `test-general.md`, `test-context.md`, `test-setup-examples.md`, `test-e2e.md`, `test-e2e-page-object.md`, `test-e2e-tags.md`, `test-context-and-data-generation-pattern.md` | Merged skill covering testing philosophy, unit/integration/E2E patterns, Playwright, page object model, TestContext system, and test data generation; uses `references/` and `examples/` |
| `ui-engineering` | `ui-component-guidelines.md`, `ui-foundational-component-principles.md`, `ui-accessibility-guidelines.md`, `ui-form-management.md` | Standalone cross-framework UI engineering skill for shared component principles, accessibility, semantic HTML, and form UX guidance |
| `firebase-dynamic-ports-setup` | `firebase-dynamic-ports-setup.md` | Example-heavy standalone setup skill with real scripts and config examples |
| `seo` | `seo-specialist.md`, `astro-seo.md` | Keep as a standalone skill rather than folding into `astro.js` |

Candidates likely not worth migrating as standalone skills unless a clearer use case
emerges:

- `domain-expert` — likely superseded by project-specific domain context generation
- `agent-list` and other roster-only files — not install-worthy skills

### TypeScript Recommendation

Recommendation: merge the currently planned generic engineering and thin backend
implementation guidance into a single `typescript-engineering` skill, while keeping
Firebase and PostgreSQL data design as separate skills.

Reasoning:

- The current core rules are overwhelmingly TypeScript-oriented across both frontend
  and backend usage.
- The old `backend-engineer.md` source is mostly role framing plus general service
  implementation guidance, not a deep runtime-specific Node body of knowledge.
- `data-object-store-persistent.md` aligns much more closely with Firestore and should
  live with `firebase`.
- `data-relational-persistent.md` is distinct from the rest of the set and is really
  PostgreSQL relational database design guidance.
- `data-attribute-naming-conventions.md` should remain canonical in
  `typescript-engineering`, but `postgres-database-design` should intentionally carry a
  modified PostgreSQL-specific version of the naming guidance.
- In OpenCode and Claude Code's hybrid skill model, a broader TypeScript core plus
  focused platform/data skills should produce cleaner triggering than a thin separate
  backend skill.

This gives you a cleaner split:

- `typescript-engineering` for shared TypeScript implementation practices
- `firebase` for Firebase and Firestore-specific application/data guidance
- `postgres-database-design` for relational schema, persistence design, and adapted
  database naming conventions

### Testing Recommendation

Recommendation: merge `testing`, `playwright`, and `test-context-and-data-generation`
into a single unified `testing` skill with supporting `references/` and `examples/`.

Reasoning:

- All three planned skills share the same domain — writing, organizing, and managing
  tests — and would frequently be installed together.
- A unified skill produces cleaner triggering: one skill fires whenever the user writes
  any test, whether unit, integration, or E2E.
- The Playwright and TestContext material is substantial but structured; it belongs in
  `references/` and `examples/` under the unified skill rather than as separate top-level
  skills.
- `test-gherkin-definition.md` does not need to become a standalone `skill/` package;
  Gherkin authoring is already covered by `SpecFlow/skills/202-spec-design`.
- Keeping three narrow testing skills would create ambiguous trigger overlap and require
  users to install multiple skills to get complete testing guidance.

This gives you one cohesive install-worthy testing skill:

- `testing` for the full testing surface: philosophy, unit tests, integration tests,
  E2E with Playwright, page object model, TestContext system, and test data generation

The `testing` skill should use the rich layout:

- `SKILL.md` as the navigation hub (≤500 lines)
- `references/` for deep domain content (philosophy, unit, integration, e2e, POM,
  TestContext, anti-patterns)
- `examples/` for copyable TypeScript code and implementation guides

### UI Recommendation

Recommendation: keep a standalone `ui-engineering` skill for cross-framework UI
guidance, and move foundational component implementation examples into the
framework skills that own them.

Reasoning:

- The reusable UI material is substantial enough to stand alone as a shared skill,
  especially around accessibility, semantic HTML, component boundaries, and form UX.
- The heaviest concrete implementation material in `foundational-ui-components.md`
  is React-shaped, so it should not remain the canonical example source for all UI
  frameworks.
- OpenCode and Claude Code are designed around hybrid skill models, so a shared
  `ui-engineering` skill can work alongside framework-specific skills without forcing
  full duplication.
- Rebuilding foundational component examples inside `react` and `solid.js` should
  improve framework accuracy while keeping cross-framework principles single-sourced.

This gives you one shared UI skill plus framework-local examples:

- `ui-engineering` for shared UI principles and standards
- `react` for React-specific implementation patterns and foundational component examples
- `solid.js` for Solid-specific implementation patterns and foundational component examples
- `astro.js` for Astro-specific UI guidance where applicable

### Example-Heavy Pattern Skills

The following skills are intentional exceptions to the "larger technology-based
skills" default because they contain substantial reusable code examples and should be
packaged with supporting files:

- `testing`
- `firebase-dynamic-ports-setup`

For these skills:

- keep `SKILL.md` focused on when to use the skill and how to apply it
- move long code walkthroughs into `references/`
- place copyable concrete implementations into `examples/`
- preserve enough real code to make the skill genuinely useful

---

## Authoring Rules For Standalone Skills

Each new standalone skill should follow these rules.

1. Create `skill/<name>/SKILL.md`.
2. Use frontmatter with `name` matching the directory and a `description` that starts
   with `Use this skill when...`.
3. Default to normal model invocation for migrated standalone skills; only keep a skill
   user-invoked if there is a clear reason it should not auto-trigger.
4. Remove persona language and old agent-role framing.
5. Remove all `@vibing/` paths and references to migration history.
6. Convert static rule prose into action-oriented skill instructions.
7. Keep the skill narrowly scoped enough that a user can tell when to use it.
8. Move long examples or reference tables into `examples/` or `references/` only when
   they improve usability.
9. For example-heavy skills, keep `SKILL.md` lean and put substantial real code in
   `examples/` and deep explanation in `references/`.
10. If a source document is too project-specific, generalize it or drop it.

---

## Per-Skill Migration Procedure

1. Identify the exact source files for the target skill.
2. Read the old source material and classify its content:
   - durable guidance
   - project-specific defaults
   - obsolete tool or path references
   - examples worth preserving
3. Decide whether the material should become:
   - a standalone skill
   - supporting examples or references under another skill
   - or be dropped as obsolete
4. Research current best practices if the topic depends on a live ecosystem.
5. Draft the new `SKILL.md` from first principles.
6. Add `examples/`, `references/`, or `scripts/` only when justified.
7. Validate that the skill is install-worthy on its own.
8. Update `skill/MIGRATION-STATUS.md`.

---

## Done Criteria

A standalone skill is complete when all of the following are true:

- `skill/<name>/SKILL.md` exists
- frontmatter is valid
- `name` matches the directory
- `description` clearly states when to use the skill
- no `@vibing/` paths remain
- no migration-history language remains in the finished artifact
- the skill is action-oriented, not just copied reference prose
- supporting files are included only when they improve the package
- the skill is useful outside SpecFlow
- migration status has been updated

---

## Suggested Migration Order

Start with the broad, high-value standards skills first, then the specialized and
more project-shaped items.

### Wave 1: Core cross-stack skills

1. `typescript-engineering`
2. `testing`

### Wave 2: Frontend technology skills

1. `react`
2. `solid.js`
3. `astro.js`
4. `ui-engineering`

### Wave 3: Backend and API skills

1. `firebase`
2. `postgres-database-design`
3. `apollo`
4. `firebase-dynamic-ports-setup`

### Wave 4: Reassessed standalone capabilities

1. `seo`

---

## Explicit Non-Goals

These items are not part of this standalone skill migration unless a later decision
changes scope:

- Recreating the old `vibing` agent roster as agents
- Recreating `@vibing/` path conventions
- Copying old rule files verbatim into new skills
- Pulling SpecFlow workflow content back out of `SpecFlow/skills/`
- Reviving `109-data-access-patterns` as a standalone skill without a new rationale
- Using any files from `old-vibes/vibing/modifiers/` in this standalone-skill flow

---

## Open Questions

These decisions should be made before large-scale authoring begins.

1. Confirm the top-level catalog names: `typescript-engineering`, `firebase`,
   `postgres-database-design`, `apollo`, `react`, `solid.js`, `astro.js`,
   `ui-engineering`, `testing`, and `firebase-dynamic-ports-setup`.
2. Confirm the target depth for rebuilt foundational component examples in `react`
   and `solid.js`.
3. Confirm how much non-Firebase backend implementation guidance, if any, still
   deserves explicit `references/` inside `typescript-engineering`.
4. Confirm how Firebase application guidance in `firebase` should relate to the
   standalone `firebase-dynamic-ports-setup` operational skill.

---

## Immediate Next Steps

1. Create `skill/MIGRATION-STATUS.md` with the larger skill inventory from this plan.
2. Start Wave 1 with `typescript-engineering`.
