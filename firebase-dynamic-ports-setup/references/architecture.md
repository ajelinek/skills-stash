# Firebase Dynamic Ports — Architecture Reference

## Port Calculation

Each developer picks an instance number from 1–9. That number is prepended
to each base port as a digit, producing a unique port for every service.

```
instance port = parseInt(`${instance}${basePort}`)
```

| Instance | Base (Firestore 8080) | Calculated Port |
| -------- | --------------------- | --------------- |
| 1        | 8080                  | 18080           |
| 2        | 8080                  | 28080           |
| 5        | 8080                  | 58080           |
| 9        | 8080                  | 98080           |

The Hub (default port 4400) must also be instance-keyed to avoid collisions on shared
machines. Instance 2 hub → `24400`, instance 3 → `34400`, etc. The setup script
handles this automatically via `ports.json`.

## Generated File Structure

```text
project-root/
├── ports.json                    ← committed, base port template
├── ports-local.json              ← gitignored, instance-specific map
├── firebase.json                 ← committed, base Firebase config
├── firebase.local.json           ← gitignored, generated emulator config
├── .env                          ← gitignored, generated env vars
└── scripts/
    ├── setup-ports.js            ← committed
    └── kill-firebase-ports.js    ← committed
```

## Environment Variable Reference

All variables are written to `.env` by `setup-ports.js`. Both public and
server-side variants are generated so the same file works for client SDKs
and Firebase Admin.

| Variable                                  | Used By                       | Example (Instance 2) |
| ----------------------------------------- | ----------------------------- | -------------------- |
| `PUBLIC_FIRESTORE_EMULATOR_HOST`          | Frontend Firestore SDK        | `localhost:28080`    |
| `PUBLIC_FIREBASE_AUTH_EMULATOR_HOST`      | Frontend Auth SDK             | `localhost:29099`    |
| `PUBLIC_FIREBASE_STORAGE_EMULATOR_HOST`   | Frontend Storage SDK          | `localhost:29199`    |
| `PUBLIC_FIREBASE_FUNCTIONS_EMULATOR_HOST` | Frontend Functions SDK        | `localhost:25001`    |
| `PUBLIC_DATABASE_EMULATOR_HOST`           | Frontend Database SDK         | `localhost:29000`    |
| `FIRESTORE_EMULATOR_HOST`                 | Backend Firestore Admin       | `localhost:28080`    |
| `FIREBASE_AUTH_EMULATOR_HOST`             | Backend Auth Admin            | `localhost:29099`    |
| `FIREBASE_STORAGE_EMULATOR_HOST`          | Backend Storage Admin         | `localhost:29199`    |
| `FIREBASE_FUNCTIONS_EMULATOR_HOST`        | Backend Functions Admin       | `localhost:25001`    |
| `DATABASE_EMULATOR_HOST`                  | Backend Database Admin        | `localhost:29000`    |
| `UI_PORT`                                 | Astro dev server + Playwright | `23333`              |

> **Note:** `FIREBASE_AUTH_EMULATOR_HOST` and `FIRESTORE_EMULATOR_HOST` must be in
> `host:port` format with **no `http://` prefix**. The `http://` prefix is required
> only for the `connectAuthEmulator()` JS SDK call — not for Admin SDK env vars.

## Shared Environment Config

Centralize environment variable access so neither frontend nor backend code
scatters `process.env` reads:

```typescript
// src/shared/config/env.ts
export const ENV = {
  FIREBASE_PROJECT_ID: process.env.FIREBASE_PROJECT_ID || 'my-project',
  FIRESTORE_EMULATOR_HOST: process.env.PUBLIC_FIRESTORE_EMULATOR_HOST || 'localhost:8080',
  FUNCTIONS_EMULATOR_HOST: process.env.PUBLIC_FIREBASE_FUNCTIONS_EMULATOR_HOST || 'localhost:5001',
  AUTH_EMULATOR_HOST: process.env.PUBLIC_FIREBASE_AUTH_EMULATOR_HOST || 'localhost:9099',
  STORAGE_EMULATOR_HOST: process.env.PUBLIC_FIREBASE_STORAGE_EMULATOR_HOST || 'localhost:9199',
  DATABASE_EMULATOR_HOST: process.env.PUBLIC_DATABASE_EMULATOR_HOST || 'localhost:9000',
}
```

Fallback defaults point to base ports so the app stays runnable with a
default-port emulator when no `.env` is present.

## Astro Config Integration

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'
import 'dotenv/config'

const uiPortRaw = process.env.UI_PORT
const uiPort = uiPortRaw && !isNaN(Number(uiPortRaw)) ? Number(uiPortRaw) : null

if (!uiPort) {
  throw new Error('UI_PORT must be set in .env and must be a valid number')
}

export default defineConfig({
  server: { port: uiPort },
})
```

Fail fast at startup if `UI_PORT` is missing. Do not silently fall back to a
default that may conflict with another instance.

## Playwright Config Integration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'
import * as dotenv from 'dotenv'
dotenv.config()

const uiPort = process.env.UI_PORT || '4000'
const baseUrl = `http://localhost:${uiPort}`

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: baseUrl,
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'pnpm run dev',
    url: baseUrl,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
```

## Vitest Config Integration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import * as dotenv from 'dotenv'
dotenv.config()

export default defineConfig({
  test: {
    environment: 'node',
    include: ['data/**/*.test.ts', 'functions/src/__tests__/**/*.test.ts'],
    globals: true,
    testTimeout: 10000,
  },
})
```

Vitest picks up the emulator host env vars from `.env` automatically once
`dotenv.config()` runs at module load time.

## Starting Emulators with the Generated Config

Always pass `--project` so the emulator's project ID matches your app's `initializeApp` config:

```bash
firebase emulators:start --config firebase.local.json --project my-project
```

Using a `demo-` prefix project ID is recommended, especially in CI. Firebase emulators
with a `demo-*` project ID refuse to connect to real Firebase services, preventing
accidental production data access:

```bash
firebase emulators:start --config firebase.local.json --project demo-myapp
```

Set the same project ID everywhere: `firebase.local.json`, your `initializeApp` call,
and any test setup.

## Data Export and Import (Seed Data)

Persist emulator data between restarts and share test fixtures across the team using
the `--import` and `--export-on-exit` flags.

**Export on shutdown:**

```bash
firebase emulators:start --config firebase.local.json --project demo-myapp \
  --import=./seed-data --export-on-exit
```

On shutdown, all Auth, Firestore, Realtime Database, and Cloud Storage emulator data
is written to `./seed-data/`. Commit this directory to share fixtures with the team.

**Import only (no auto-export):**

```bash
firebase emulators:start --config firebase.local.json --project demo-myapp \
  --import=./seed-data
```

**Standalone export from a running instance:**

```bash
firebase emulators:export ./seed-data --project demo-myapp
```

Add `seed-data/` to `package.json` scripts for convenience:

```json
{
  "scripts": {
    "emulators": "firebase emulators:start --config firebase.local.json --project demo-myapp --import=./seed-data --export-on-exit"
  }
}
```

## Functions Emulator Handling

The setup script checks whether a `functions/` directory exists before
including the Functions emulator in `firebase.local.json`. If no functions
directory is present, the functions entry is omitted entirely. This prevents
Firebase from failing to start because a configured emulator has no code.

Projects that add functions later simply need to re-run `pnpm run setup:ports`.

## Troubleshooting

**Port already in use when starting emulators**

```bash
pnpm run kill:ports
firebase emulators:start --config firebase.local.json
```

**Missing configuration files**

Re-run setup. The script is idempotent and safe to re-run at any time.

```bash
pnpm run setup:ports
```

**Environment variables not loading**

1. Verify `.env` exists at the project root.
2. Confirm the test runner or dev server calls `dotenv.config()` before reading env vars.
3. Restart the dev server to pick up changes.

**Wrong instance number / collision with another developer**

```bash
pnpm run kill:ports
pnpm run setup:ports   # choose a different instance number
```

Coordinate instance assignments with the team to avoid collisions.
