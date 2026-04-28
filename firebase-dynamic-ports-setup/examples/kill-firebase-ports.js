// scripts/kill-firebase-ports.js
// Kills all processes on the ports stored in ports-local.json.
// Falls back to default Firebase base ports if the config file is missing.
// Run with: node scripts/kill-firebase-ports.js

import fs from 'fs'
import { spawn } from 'child_process'

/**
 * Kills the process on a single port using npx kill-port.
 * Errors are swallowed — if the port is not in use, that is fine.
 */
function killPort(port) {
  return new Promise(resolve => {
    const proc = spawn('npx', ['kill-port', String(port)], { stdio: 'inherit' })
    proc.on('close', () => resolve())
  })
}

async function main() {
  try {
    const portInfo = JSON.parse(fs.readFileSync('ports-local.json', 'utf8'))

    const raw = []

    if (portInfo.firebase && typeof portInfo.firebase === 'object') {
      raw.push(...Object.values(portInfo.firebase))
    }

    if (portInfo.web && typeof portInfo.web === 'object') {
      raw.push(...Object.values(portInfo.web))
    }

    // Deduplicate and filter for valid numbers.
    const ports = [...new Set(raw.filter(p => typeof p === 'number' && !isNaN(p)))]

    if (ports.length === 0) {
      console.log('No valid ports found in ports-local.json.')
      return
    }

    console.log(`Killing processes on ports: ${ports.join(', ')}`)
    // Kill individually to avoid argument-parsing issues with space-separated strings.
    await Promise.all(ports.map(killPort))
    console.log('Done.')
  } catch (error) {
    console.error('Could not read ports-local.json:', error.message)
    console.log('Falling back to default Firebase emulator ports...')
    const defaultPorts = [8080, 9099, 4000, 9199, 5001, 5000]
    await Promise.all(defaultPorts.map(killPort))
    console.log('Done (fallback).')
  }
}

main()
