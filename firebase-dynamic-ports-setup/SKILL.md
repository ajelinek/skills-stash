---
name: firebase-dynamic-ports-setup
description: >
  Use this skill when setting up Firebase emulators to support multiple
  developers on the same host machine without port conflicts. Trigger on
  requests to configure Firebase emulator ports dynamically, assign per-developer
  instance numbers, set up emulator port isolation, generate firebase.local.json
  or a .env file from a port template, or add kill-ports scripts to a Firebase
  project. Also trigger when a team reports emulator port conflicts or asks how
  to run Firebase emulators in parallel on shared infrastructure.
---

# Firebase Dynamic Ports Setup

Use this skill to configure Firebase emulators so that multiple developers can
run isolated emulator instances on the same host machine without port conflicts.

The core mechanism: each developer picks an instance number (1–9). That number
is prepended to every base port to produce a unique, non-overlapping port set.
All emulator config and environment variables are generated from a single script
so the setup stays consistent and repeatable.

## When to Use This Skill

- Adding emulator port isolation to a Firebase project for the first time
- Onboarding a new developer who needs their own emulator instance
- Troubleshooting emulator port conflicts on a shared dev machine or CI host
- Wiring the generated `.env` into Playwright, Vitest, Astro, or another tool
- Explaining or reviewing any part of the dynamic ports pattern

## When Not to Use This Skill

- Solo or single-machine projects where default emulator ports are sufficient
- CI environments where each run gets an isolated VM or container (no shared ports)
- Projects not using Firebase emulators

## Port Calculation Formula

```
instance port = instance_number prepended to base port
```

Instance 2, base Firestore port 8080 → `28080`  
Instance 3, base Firestore port 9099 → `39099`

Instances must be 1–9. Instance numbers across the team should be unique and
coordinated out of band (a simple shared doc or team convention is enough).

## Setup Workflow

### 1. Create `ports.json` (committed)

Defines base port numbers for all services. Commit this file.

See `./examples/ports.json` for the standard template.

### 2. Add `scripts/setup-ports.js` (committed)

Prompts for an instance number, then generates three files:

- `ports-local.json` — instance-specific port map (gitignored)
- `firebase.local.json` — Firebase emulator config at instance ports (gitignored)
- `.env` — environment variables for all emulator hosts (gitignored)

The script conditionally includes the Functions emulator only when a `functions/`
directory exists, preventing Firebase startup errors on projects without functions.

See `./examples/setup-ports.js` for the complete script.

### 3. Add `scripts/kill-firebase-ports.js` (committed)

Reads `ports-local.json` and kills all processes on the stored ports. Falls back
to default base ports if the config file is missing.

See `./examples/kill-firebase-ports.js` for the complete script.

### 4. Wire up `package.json` scripts

```json
{
  "type": "module",
  "scripts": {
    "setup:ports": "node scripts/setup-ports.js",
    "kill:ports": "node scripts/kill-firebase-ports.js"
  },
  "devDependencies": {
    "kill-port": "^2.0.1"
  }
}
```

`"type": "module"` is required because the scripts use ES module `import` syntax.
Run `pnpm add -D kill-port` (or `npm install -D kill-port`) after adding the dependency.

### 5. Update `.gitignore`

```
ports-local.json
firebase.local.json
.env
.env.local
```

### 6. Start emulators using the generated config

```bash
firebase emulators:start --config firebase.local.json --project demo-myapp
```

Pass `--project` so the emulator's project ID matches your app's `initializeApp` config.
Using a `demo-` prefix is strongly recommended: Firebase emulators with a `demo-*`
project ID refuse to connect to real Firebase services, preventing accidental
production data access. Use the same project ID in your app init and test setup.

## Connecting Firebase SDKs to Instance Ports

All SDKs read ports from the generated `.env` at runtime.

**Frontend (Firebase JS SDK):** connect emulators in non-production mode by
reading `PUBLIC_*` env vars.

**Backend (Firebase Admin SDK):** set `FIRESTORE_EMULATOR_HOST` and
`DATABASE_EMULATOR_HOST` from env before initializing.

**Shared env config:** centralize access in a typed `ENV` object with sane
fallbacks to avoid scattered `process.env` reads.

See `./examples/firebase-sdk-connection.ts` for frontend and backend
connection patterns.

**Test runners (Vitest, Playwright):** load `.env` at the top of each config
file via `dotenv.config()` so tests connect to the same instance ports.

See `./references/architecture.md` for Playwright and Vitest config examples
and the full environment variable reference table.

## File Reference

| File                             | Committed | Purpose                          |
| -------------------------------- | --------- | -------------------------------- |
| `ports.json`                     | Yes       | Base port template               |
| `scripts/setup-ports.js`         | Yes       | Generates all instance files     |
| `scripts/kill-firebase-ports.js` | Yes       | Kills processes on instance ports |
| `ports-local.json`               | No        | Instance-specific port map       |
| `firebase.local.json`            | No        | Firebase emulator config         |
| `.env`                           | No        | Emulator host environment vars   |

## Developer Workflow

```bash
# First-time setup or switching instances
pnpm run setup:ports
# → Enter instance number (1–9) when prompted

# Start emulators (with seed data import/export)
firebase emulators:start --config firebase.local.json --project demo-myapp \
  --import=./seed-data --export-on-exit

# Kill all instance ports before stopping or restarting
pnpm run kill:ports
```

## Supporting Files

| File | Purpose |
| --- | --- |
| `./references/architecture.md` | Port calculation details, full env var table, Playwright and Vitest config examples, troubleshooting guide |
| `./examples/ports.json` | Base port template to commit |
| `./examples/setup-ports.js` | Complete setup script |
| `./examples/kill-firebase-ports.js` | Complete port-killing script |
| `./examples/firebase-sdk-connection.ts` | Frontend and backend SDK connection patterns |
