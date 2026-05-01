# Standalone Skills

> **Note:** These skills are actively being tested and are still evolving. Expect changes to structure, content, and coverage as they mature.

This directory contains opinionated, first-principles skills built for this project.
They cover the technology areas where custom guidance adds the most value.

For everything else, install from the public catalog at [skills.sh](https://skills.sh).

---

## Install

To interactively pick and choose skills from a repo, run `npx skills add <repo>` — it will present a multi-select list of everything available. To install a single specific skill, append the skill name.

---

### `ajelinek/skills-stash`

Interactive - pick what you want:

```sh
npx skills add ajelinek/skills-stash
```

Install specific skills directly:

```sh
npx skills add ajelinek/skills-stash typescript-engineering
npx skills add ajelinek/skills-stash testing
npx skills add ajelinek/skills-stash react
npx skills add ajelinek/skills-stash solid.js
npx skills add ajelinek/skills-stash astro.js
npx skills add ajelinek/skills-stash ui-engineering
npx skills add ajelinek/skills-stash astro-seo
npx skills add ajelinek/skills-stash cmux-workspace-builder
npx skills add ajelinek/skills-stash firebase-dynamic-ports-setup
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

Interactive - pick what you want from the full catalog:

```sh
npx skills add wshobson/agents
```

Install specific skills directly:

```sh
npx skills add wshobson/agents nodejs-backend-patterns
npx skills add wshobson/agents auth-implementation-patterns
npx skills add wshobson/agents postgresql-table-design
npx skills add wshobson/agents sql-optimization-patterns
npx skills add wshobson/agents database-migration
```

| Skill                          | What it does                                                        |
| ------------------------------ | ------------------------------------------------------------------- |
| `nodejs-backend-patterns`      | Express, NestJS, and Fastify service layer patterns                 |
| `auth-implementation-patterns` | Auth flows, JWT, session handling, and OAuth patterns               |
| `postgresql-table-design`      | PostgreSQL-specific table and index design guidance                 |
| `sql-optimization-patterns`    | Query tuning, index strategy, and EXPLAIN analysis                  |
| `database-migration`           | Schema migration workflows, versioning, and rollback patterns       |

---

### `coreyhaines31/marketingskills`

Interactive:

```sh
npx skills add coreyhaines31/marketingskills
```

Install directly:

```sh
npx skills add coreyhaines31/marketingskills seo-audit
npx skills add coreyhaines31/marketingskills ai-seo
```

| Skill       | What it does                                                           |
| ----------- | ---------------------------------------------------------------------- |
| `seo-audit` | Complements `astro-seo` with audit-oriented SEO analysis and reporting |
| `ai-seo`    | AI-assisted SEO content and programmatic SEO patterns                  |

---

### `firebase/agent-skills`

Interactive - recommended, this catalog is large:

```sh
npx skills add firebase/agent-skills
```

Install specific skills directly:

```sh
npx skills add firebase/agent-skills firebase-basics
npx skills add firebase/agent-skills firebase-auth-basics
npx skills add firebase/agent-skills firebase-hosting-basics
npx skills add firebase/agent-skills firebase-app-hosting-basics
npx skills add firebase/agent-skills firebase-data-connect
npx skills add firebase/agent-skills firebase-firestore-standard
npx skills add firebase/agent-skills firebase-ai-logic
npx skills add firebase/agent-skills firebase-local-env-setup
npx skills add firebase/agent-skills firebase-firestore-basics
npx skills add firebase/agent-skills firebase-security-rules-auditor
npx skills add firebase/agent-skills firebase-ai-logic-basics
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

---

## Not really coding, but nice to have

### `anthropics/skills`

Skills from Anthropic for document creation, file formats, and agent tooling.

Interactive:

```sh
npx skills add anthropics/skills
```

Install specific skills directly:

```sh
npx skills add anthropics/skills skill-creator
npx skills add anthropics/skills pdf
npx skills add anthropics/skills pptx
npx skills add anthropics/skills xlsx
npx skills add anthropics/skills docx
npx skills add anthropics/skills mcp-builder
npx skills add anthropics/skills doc-coauthoring
```

| Skill             | What it does                                                                                    |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| `skill-creator`   | Create, test, and iteratively improve agent skills with structured evaluation and benchmarking  |
| `pdf`             | Read, extract, merge, split, rotate, watermark, fill, encrypt, and OCR PDF files               |
| `pptx`            | Create, read, edit, and manipulate PowerPoint presentations                                     |
| `xlsx`            | Open, read, edit, create, and convert spreadsheet files                                         |
| `docx`            | Create, read, edit, and manipulate Word documents                                               |
| `mcp-builder`     | Build high-quality MCP servers connecting LLMs to external services, with evals                 |
| `doc-coauthoring` | Structured three-stage workflow for collaboratively authoring docs, specs, and proposals        |
