# Standalone Skills Migration Status

## Reference

Use `skill/MIGRATION-PLAN.md` as the source of truth for scope, mapping, and
authoring rules.

This tracker covers the standalone `skill/` migration only.

It does not cover:

- `SpecFlow/skills/`
- `old-vibes/vibing/modifiers/`

SpecFlow-owned exception:

- `old-vibes/vibing/modifiers/agent-context-manager.md`

---

## Progress Summary

| Status | Count |
| --- | --- |
| Planned | 9 |
| In progress | 0 |
| Complete | 2 |
| Decision pending | 0 |

---

## Planned Skills

| # | Skill | Primary source material | Status | Notes |
| --- | --- | --- | --- | --- |
| 1 | `typescript-engineering` | `rules/common/foundation/*`, `fragments/engineer-*`, `rules/common/data/data-attribute-naming-conventions.md`, selected generally useful guidance from `agents/backend-engineer.md` | Complete | Created as a standalone TypeScript engineering skill with focused references for type modeling, code shape, and TSConfig or module choices, plus concrete examples for discriminated unions, predicates, type-only imports, and project references |
| 2 | `testing` | `test-general.md`, `test-context.md`, `test-setup-examples.md`, `test-e2e.md`, `test-e2e-page-object.md`, `test-e2e-tags.md`, `patterns/test-context-and-data-generation-pattern.md` | Complete | Unified testing skill merging original `testing`, `playwright`, and `test-context-and-data-generation` plans; rich layout with `references/` and `examples/` including full TestContext implementation guide |
| 3 | `firebase` | `rules/common/backend/firebase-integration.md`, `rules/common/data/data-object-store-persistent.md` | Planned | Firebase-specific application, Firestore, and document-store guidance |
| 4 | `postgres-database-design` | `rules/common/data/data-relational-persistent.md`, PostgreSQL-adapted guidance derived from `rules/common/data/data-attribute-naming-conventions.md` | Planned | PostgreSQL-focused relational schema, persistence design, and database-specific naming guidance |
| 5 | `apollo` | `rules/apollo/*` | Planned | One larger Apollo and GraphQL skill |
| 6 | `react` | `rules/react/*`, relevant common UI rules, React-specific portions of `patterns/foundational-ui-components.md` | Planned | Broad React skill with React-based foundational component examples |
| 7 | `solid.js` | `rules/solid.js/*`, relevant common UI rules, rebuilt Solid-based foundational component examples | Planned | Broad Solid skill with Solid-specific foundational component examples |
| 8 | `astro.js` | `rules/astro.js/*`, relevant common UI rules | Planned | Broad Astro skill with shared UI guidance where applicable |
| 9 | `ui-engineering` | `rules/common/ui/ui-component-guidelines.md`, `rules/common/ui/ui-foundational-component-principles.md`, `rules/common/ui/ui-accessibility-guidelines.md`, `rules/common/ui/ui-form-management.md` | Planned | Cross-framework UI engineering skill for shared component principles, accessibility, semantic HTML, and form UX guidance |
| 10 | `firebase-dynamic-ports-setup` | `patterns/firebase-dynamic-ports-setup.md` | Planned | Example-heavy operational setup skill |
| 11 | `seo` | `agents/seo-specialist.md`, `patterns/astro-seo.md` | Planned | Standalone SEO skill |

---

## Suggested Order

### Wave 1

1. `typescript-engineering` ✓
2. `testing` ✓

### Wave 2

1. `react`
2. `solid.js`
3. `astro.js`
4. `ui-engineering`

### Wave 3

1. `firebase`
2. `postgres-database-design`
3. `apollo`
4. `firebase-dynamic-ports-setup`

### Wave 4

1. `seo`

---

## Moved To SpecFlow

The `deep-research` package is no longer part of the standalone `skill/` catalog.

It now lives at `SpecFlow/skills/deep-research/` as a SpecFlow-bundled support
skill, similar in role to other unnumbered support capabilities.

---

## Skill Package Expectations

All migrated skills must satisfy these checks before being marked complete:

- `skill/<name>/SKILL.md` exists
- valid frontmatter
- `name` matches directory
- `description` starts with `Use this skill when...`
- no `@vibing/` paths remain
- no migration-history language remains in the finished artifact
- guidance is action-oriented, not a direct prose dump from the source
- supporting `references/` and `examples/` are included when they materially help

Additional expectation for example-heavy skills:

- `testing`
- `firebase-dynamic-ports-setup`

These should preserve practical code examples as supporting files rather than forcing
all content into `SKILL.md`.
