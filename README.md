# Standalone Skills

> **Note:** These skills are actively being tested and are still evolving. Expect changes to structure, content, and coverage as they mature.

This directory contains opinionated, first-principles skills built for this project.
They cover the technology areas where custom guidance adds the most value.

For everything else, install from the public catalog at [skills.sh](https://skills.sh).

---

## Quick install

Run this one-liner to install everything automatically — no prompts, no interaction required:

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/ajelinek/skills-stash/main/install.sh)
```

This installs **all skills** from `ajelinek/skills-stash` plus the recommended public skills listed below. Nothing is selected or confirmed — it runs straight through.

---

## Manual install

To interactively pick and choose skills from a repo, run `npx skills add <repo>` — it will present a multi-select list of everything available. To install a specific skill directly without prompts, append the skill name and `--yes`.

---

### `ajelinek/skills-stash`

```sh
# Interactive — pick what you want
npx skills add ajelinek/skills-stash

# Or install specific skills directly
npx skills add ajelinek/skills-stash typescript-engineering --yes
npx skills add ajelinek/skills-stash testing --yes
npx skills add ajelinek/skills-stash react --yes
npx skills add ajelinek/skills-stash solid.js --yes
npx skills add ajelinek/skills-stash astro.js --yes
npx skills add ajelinek/skills-stash ui-engineering --yes
npx skills add ajelinek/skills-stash astro-seo --yes
npx skills add ajelinek/skills-stash cmux-workspace-builder --yes
npx skills add ajelinek/skills-stash firebase-dynamic-ports-setup --yes
```

| Skill                          | What it does                                                                                                                                          |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `typescript-engineering`       | Core TypeScript implementation practices: type modeling, error handling, naming conventions, module shape, and TSConfig guidance                      |
| `testing`                      | Full testing surface: philosophy, unit tests, integration tests, E2E with Playwright, page object model, TestContext system, and test data generation |
| `react`                        | React components, state management, SWR, Zustand, shared UI patterns, and foundational component examples                                             |
| `solid.js`                     | SolidJS components, signals, stores, context, async patterns, and testing with `@solidjs/testing-library`                                             |
| `astro.js`                     | Astro 5 project structure, component patterns, content collections, server rendering, middleware, and Astro Actions                                   |
| `ui-engineering`               | Cross-framework UI principles: component boundaries, accessibility, semantic HTML, styling tokens, and form UX                                        |
| `astro-seo`                    | Astro-specific SEO: structured data, IndexNow, performance SEO, and meta management                                                                   |
| `cmux-workspace-builder`       | Interview-driven builder for cmux.json workspace configs: pane layouts, split configuration, and dev environment automation                           |
| `firebase-dynamic-ports-setup` | Configure Firebase emulators for per-developer port isolation on shared hosts, eliminating port conflicts on team machines                            |

---

### `wshobson/agents`

A large public catalog (150+ skills). The ones recommended here complement the skills above.

```sh
# Interactive — pick what you want from the full catalog
npx skills add wshobson/agents

# Or install specific skills directly
npx skills add wshobson/agents typescript-advanced-types --yes
npx skills add wshobson/agents nodejs-backend-patterns --yes
npx skills add wshobson/agents api-design-principles --yes
npx skills add wshobson/agents auth-implementation-patterns --yes
npx skills add wshobson/agents postgresql-table-design --yes
npx skills add wshobson/agents e2e-testing-patterns --yes
npx skills add wshobson/agents sql-optimization-patterns --yes
npx skills add wshobson/agents database-migration --yes
```

| Skill                          | What it does                                                                       |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| `typescript-advanced-types`    | Advanced type patterns that extend `typescript-engineering` without duplicating it |
| `nodejs-backend-patterns`      | Express, NestJS, and Fastify service layer patterns                                |
| `api-design-principles`        | REST API design conventions, versioning, and error response shaping                |
| `auth-implementation-patterns` | Auth flows, JWT, session handling, and OAuth patterns                              |
| `postgresql-table-design`      | PostgreSQL-specific table and index design guidance                                |
| `e2e-testing-patterns`         | Additional E2E test organization and flakiness-reduction patterns                  |
| `sql-optimization-patterns`    | Query tuning, index strategy, and EXPLAIN analysis                                 |
| `database-migration`           | Schema migration workflows, versioning, and rollback patterns                      |

---

### `currents-dev/playwright-best-practices-skill`

```sh
# Interactive
npx skills add currents-dev/playwright-best-practices-skill

# Or install directly
npx skills add currents-dev/playwright-best-practices-skill playwright-best-practices --yes
```

| Skill                       | What it does                                                              |
| --------------------------- | ------------------------------------------------------------------------- |
| `playwright-best-practices` | Playwright-specific patterns that complement the `testing` skill          |

---

### `coreyhaines31/marketingskills`

```sh
# Interactive
npx skills add coreyhaines31/marketingskills

# Or install directly
npx skills add coreyhaines31/marketingskills seo-audit --yes
npx skills add coreyhaines31/marketingskills ai-seo --yes
```

| Skill       | What it does                                                           |
| ----------- | ---------------------------------------------------------------------- |
| `seo-audit` | Complements `astro-seo` with audit-oriented SEO analysis and reporting |
| `ai-seo`    | AI-assisted SEO content and programmatic SEO patterns                  |

---

### `firebase/agent-skills`

```sh
# Interactive — recommended, this catalog is large
npx skills add firebase/agent-skills

# Or install specific skills directly
npx skills add firebase/agent-skills firebase-basics --yes
npx skills add firebase/agent-skills firebase-auth-basics --yes
npx skills add firebase/agent-skills firebase-hosting-basics --yes
npx skills add firebase/agent-skills firebase-app-hosting-basics --yes
npx skills add firebase/agent-skills firebase-data-connect --yes
npx skills add firebase/agent-skills firebase-firestore-standard --yes
npx skills add firebase/agent-skills firebase-ai-logic --yes
npx skills add firebase/agent-skills firebase-local-env-setup --yes
npx skills add firebase/agent-skills firebase-firestore-basics --yes
npx skills add firebase/agent-skills firebase-security-rules-auditor --yes
npx skills add firebase/agent-skills firebase-ai-logic-basics --yes
```

| Skill                             | What it does                                                                                        |
| --------------------------------- | --------------------------------------------------------------------------------------------------- |
| `firebase-basics`                 | Firebase project setup, config, and CLI workflow                                                    |
| `firebase-auth-basics`            | Firebase Authentication flows: email, OAuth, and token handling                                     |
| `firebase-hosting-basics`         | Firebase Hosting setup, deployment, and CDN configuration                                           |
| `firebase-app-hosting-basics`     | Firebase App Hosting for server-rendered apps: build, deploy, and rollout patterns                  |
| `firebase-data-connect`           | PostgreSQL-backed GraphQL via Firebase SQL Connect — schema, queries, mutations, and type-safe SDKs |
| `firebase-firestore-standard`     | Firestore data modeling, queries, and security rules for standard projects                          |
| `firebase-ai-logic`               | Firebase AI Logic integration: Gemini API access, prompt management, and server-side AI workflows   |
| `firebase-local-env-setup`        | Local Firebase emulator suite setup and development workflow                                        |
| `firebase-firestore-basics`       | Firestore fundamentals: reads, writes, and real-time listeners                                      |
| `firebase-security-rules-auditor` | Audits Firebase Security Rules for gaps, misconfigurations, and overly permissive access            |
| `firebase-ai-logic-basics`        | Introductory Firebase AI Logic patterns for getting started with Gemini-powered features            |
