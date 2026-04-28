# Standalone Skills

This directory contains opinionated, first-principles skills built for this project.
They cover the technology areas where custom guidance adds the most value.

For everything else, install from the public catalog at [skills.sh](https://skills.sh).

---

## Skills in this directory

| Skill                    | What it does                                                                                                                                          |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `typescript-engineering` | Core TypeScript implementation practices: type modeling, error handling, naming conventions, module shape, and TSConfig guidance                      |
| `testing`                | Full testing surface: philosophy, unit tests, integration tests, E2E with Playwright, page object model, TestContext system, and test data generation |
| `react`                  | React components, state management, SWR, Zustand, shared UI patterns, and foundational component examples                                             |
| `solid.js`               | SolidJS components, signals, stores, context, async patterns, and testing with `@solidjs/testing-library`                                             |
| `astro.js`               | Astro 5 project structure, component patterns, content collections, server rendering, middleware, and Astro Actions                                   |
| `ui-engineering`         | Cross-framework UI principles: component boundaries, accessibility, semantic HTML, styling tokens, and form UX                                        |
| `astro-seo`              | Astro-specific SEO: structured data, IndexNow, performance SEO, and meta management                                                                   |

---

## Recommended public skills

Install these from [skills.sh](https://skills.sh) to complement the skills above.

### TypeScript and backend

```sh
npx skills add wshobson/agents typescript-advanced-types
npx skills add wshobson/agents nodejs-backend-patterns
npx skills add wshobson/agents api-design-principles
npx skills add wshobson/agents auth-implementation-patterns
```

| Skill                          | Why                                                                                |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| `typescript-advanced-types`    | Advanced type patterns that extend `typescript-engineering` without duplicating it |
| `nodejs-backend-patterns`      | Express, NestJS, and Fastify service layer patterns                                |
| `api-design-principles`        | REST API design conventions, versioning, and error response shaping                |
| `auth-implementation-patterns` | Auth flows, JWT, session handling, and OAuth patterns                              |

### Database and data

```sh
npx skills add neondatabase/agent-skills neon-postgres
npx skills add wshobson/agents postgresql-table-design
```

| Skill                     | Why                                                     |
| ------------------------- | ------------------------------------------------------- |
| `neon-postgres`           | Neon serverless PostgreSQL setup and branching workflow |
| `postgresql-table-design` | PostgreSQL-specific table and index design guidance     |

### Testing

```sh
npx skills add currents-dev/playwright-best-practices-skill playwright-best-practices
npx skills add wshobson/agents e2e-testing-patterns
```

| Skill                       | Why                                                               |
| --------------------------- | ----------------------------------------------------------------- |
| `playwright-best-practices` | Playwright-specific patterns that complement the `testing` skill  |
| `e2e-testing-patterns`      | Additional E2E test organization and flakiness-reduction patterns |

### SEO and marketing

```sh
npx skills add coreyhaines31/marketingskills seo-audit
npx skills add coreyhaines31/marketingskills ai-seo
```

| Skill       | Why                                                                    |
| ----------- | ---------------------------------------------------------------------- |
| `seo-audit` | Complements `astro-seo` with audit-oriented SEO analysis and reporting |
| `ai-seo`    | AI-assisted SEO content and programmatic SEO patterns                  |

---

## What is not covered here

Firebase, PostgreSQL operational patterns, and Apollo/GraphQL are intentionally out of scope
for this skill library. Use public skills from Firebase or Neon if your project needs them.

### Firebase

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

| Skill                                      | Why                                                                                                    |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `firebase-basics`                          | Firebase project setup, config, and CLI workflow                                                       |
| `firebase-auth-basics`                     | Firebase Authentication flows: email, OAuth, and token handling                                       |
| `firebase-hosting-basics`                  | Firebase Hosting setup, deployment, and CDN configuration                                              |
| `firebase-app-hosting-basics`              | Firebase App Hosting for server-rendered apps: build, deploy, and rollout patterns                    |
| `firebase-data-connect`                    | PostgreSQL-backed GraphQL via Firebase SQL Connect — schema, queries, mutations, and type-safe SDKs   |
| `firebase-firestore-standard`              | Firestore data modeling, queries, and security rules for standard projects                             |
| `firebase-ai-logic`                        | Firebase AI Logic integration: Gemini API access, prompt management, and server-side AI workflows      |
| `firebase-local-env-setup`                 | Local Firebase emulator suite setup and development workflow                                           |
| `firebase-firestore-basics`                | Firestore fundamentals: reads, writes, and real-time listeners                                         |
| `firebase-security-rules-auditor`          | Audits Firebase Security Rules for gaps, misconfigurations, and overly permissive access               |
| `firebase-ai-logic-basics`                 | Introductory Firebase AI Logic patterns for getting started with Gemini-powered features               |

### Apollo / GraphQL

No dedicated Apollo or GraphQL skill currently exists on skills.sh. `firebase-data-connect`
above covers a GraphQL schema-first workflow if you are using Firebase SQL Connect.
For standalone Apollo Server or Apollo Client work, no public catalog option is available —
consider a local standalone skill in this directory.

### PostgreSQL (additional patterns)

The `neon-postgres` and `postgresql-table-design` skills above cover schema design.
For operational and migration patterns:

```sh
npx skills add wshobson/agents sql-optimization-patterns
npx skills add wshobson/agents database-migration
```

| Skill                    | Why                                                              |
| ------------------------ | ---------------------------------------------------------------- |
| `sql-optimization-patterns` | Query tuning, index strategy, and EXPLAIN analysis           |
| `database-migration`     | Schema migration workflows, versioning, and rollback patterns   |

### GCP App Engine

No GCP App Engine skill exists on skills.sh as of April 2026. No public catalog option
is available — consider a local standalone skill in this directory if App Engine deployment
patterns are needed for this project.
