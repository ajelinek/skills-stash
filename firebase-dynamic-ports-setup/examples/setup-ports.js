// scripts/setup-ports.js
// Generates ports-local.json, firebase.local.json, and .env for a given instance number.
// Run with: node scripts/setup-ports.js
// Requires Node 18+ and "type": "module" in package.json (or rename to setup-ports.mjs).

import fs from 'fs'
import readline from 'readline'

const PORTS_TEMPLATE = 'ports.json'
const PORTS_LOCAL = 'ports-local.json'

/**
 * Prompts user for instance number (1-9).
 */
async function promptInstanceNumber() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  })
  return new Promise(resolve => {
    rl.question('Enter instance number (1-9): ', answer => {
      rl.close()
      const num = parseInt(answer, 10)
      if (isNaN(num) || num < 1 || num > 9) {
        console.error('Invalid instance number. Must be 1-9.')
        process.exit(1)
      }
      resolve(num)
    })
  })
}

/**
 * Reads base port configuration from ports.json.
 */
function readBasePorts() {
  return JSON.parse(fs.readFileSync(PORTS_TEMPLATE, 'utf8'))
}

/**
 * Prefixes each port with the instance number.
 * Formula: parseInt(`${instance}${basePort}`)
 * Example: instance=2, basePort=8080 → 28080
 */
function updatePortsWithInstance(ports, instance) {
  const updated = { firebase: {}, web: {} }
  for (const [key, value] of Object.entries(ports.firebase)) {
    updated.firebase[key] = Number(`${instance}${value}`)
  }
  for (const [key, value] of Object.entries(ports.web)) {
    updated.web[key] = Number(`${instance}${value}`)
  }
  return updated
}

/**
 * Generates firebase.local.json with instance-specific emulator ports.
 * Reads the existing firebase.json as a base and replaces the emulators section.
 * Conditionally includes the functions emulator only when a functions/ directory exists.
 */
function generateFirebaseLocalJson(ports) {
  const firebaseJson = JSON.parse(fs.readFileSync('firebase.json', 'utf8'))
  const hasFunctions = fs.existsSync('functions')

  firebaseJson.emulators = {
    auth: { port: ports.firebase.auth },
    firestore: { port: ports.firebase.firestore },
    hosting: { port: ports.firebase.hosting },
    storage: { port: ports.firebase.storage },
    database: { port: ports.firebase.database },
    hub: { port: ports.firebase.hub },
    ui: { enabled: true, port: ports.firebase.ui },
    singleProjectMode: true,
  }

  if (hasFunctions) {
    firebaseJson.emulators.functions = { port: ports.firebase.functions }
  }

  fs.writeFileSync('firebase.local.json', JSON.stringify(firebaseJson, null, 2))
}

/**
 * Generates .env with Firebase emulator host environment variables.
 * Both PUBLIC_* (client SDK) and bare (Admin SDK / server-side) variants are written.
 * Functions env vars are only written when a functions/ directory exists.
 */
function generateEnv(ports) {
  const hasFunctions = fs.existsSync('functions')

  const functionsEnv = hasFunctions
    ? `PUBLIC_FIREBASE_FUNCTIONS_EMULATOR_HOST=localhost:${ports.firebase.functions}
FIREBASE_FUNCTIONS_EMULATOR_HOST=localhost:${ports.firebase.functions}
`
    : ''

  const envContent = `# Public Firebase SDK variables (for client-side)
PUBLIC_FIRESTORE_EMULATOR_HOST=localhost:${ports.firebase.firestore}
PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=localhost:${ports.firebase.auth}
PUBLIC_FIREBASE_STORAGE_EMULATOR_HOST=localhost:${ports.firebase.storage}
${functionsEnv}PUBLIC_DATABASE_EMULATOR_HOST=localhost:${ports.firebase.database}

# Server-side Firebase Admin variables
FIREBASE_AUTH_EMULATOR_HOST=localhost:${ports.firebase.auth}
FIRESTORE_EMULATOR_HOST=localhost:${ports.firebase.firestore}
FIREBASE_STORAGE_EMULATOR_HOST=localhost:${ports.firebase.storage}
DATABASE_EMULATOR_HOST=localhost:${ports.firebase.database}

# Web UI port (used by Astro dev server and Playwright)
UI_PORT=${ports.web.ui}
`
  fs.writeFileSync('.env', envContent)
}

async function main() {
  const ports = readBasePorts()
  const instance = await promptInstanceNumber()
  const updatedPorts = updatePortsWithInstance(ports, instance)

  fs.writeFileSync(PORTS_LOCAL, JSON.stringify(updatedPorts, null, 2))
  generateFirebaseLocalJson(updatedPorts)
  generateEnv(updatedPorts)

  console.log(`Instance ${instance} configured.`)
  console.log('Generated: ports-local.json, firebase.local.json, .env')
}

main()
