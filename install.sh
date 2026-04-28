#!/usr/bin/env bash
# Install skills for OpenCode.
# Usage: bash install.sh

set -euo pipefail

# ── Skill lists ───────────────────────────────────────────────────────────────

install_ajelinek() {
  echo ""
  echo "Installing ajelinek/skills-stash skills..."
  npx skills add ajelinek/skills-stash typescript-engineering
  npx skills add ajelinek/skills-stash testing
  npx skills add ajelinek/skills-stash react
  npx skills add ajelinek/skills-stash solid.js
  npx skills add ajelinek/skills-stash astro.js
  npx skills add ajelinek/skills-stash ui-engineering
  npx skills add ajelinek/skills-stash astro-seo
  npx skills add ajelinek/skills-stash cmux-workspace-builder
  npx skills add ajelinek/skills-stash firebase-dynamic-ports-setup
}

install_recommended() {
  echo ""
  echo "Installing recommended public skills..."

  echo "  [TypeScript & backend]"
  npx skills add wshobson/agents typescript-advanced-types
  npx skills add wshobson/agents nodejs-backend-patterns
  npx skills add wshobson/agents api-design-principles
  npx skills add wshobson/agents auth-implementation-patterns

  echo "  [Database & data]"
  npx skills add neondatabase/agent-skills neon-postgres
  npx skills add wshobson/agents postgresql-table-design

  echo "  [Testing]"
  npx skills add currents-dev/playwright-best-practices-skill playwright-best-practices
  npx skills add wshobson/agents e2e-testing-patterns

  echo "  [SEO & marketing]"
  npx skills add coreyhaines31/marketingskills seo-audit
  npx skills add coreyhaines31/marketingskills ai-seo
}

# ── Menu ──────────────────────────────────────────────────────────────────────

echo ""
echo "OpenCode Skill Installer"
echo "========================"
echo ""
  echo "  1) ajelinek/skills-stash only"
  echo "  2) Recommended public skills only"
  echo "  3) All (ajelinek/skills-stash + recommended public skills)"
echo ""
read -rp "Choose an option [1-3]: " choice

case "$choice" in
  1)
    install_ajelinek
    ;;
  2)
    install_recommended
    ;;
  3)
    install_ajelinek
    install_recommended
    ;;
  *)
    echo "Invalid option: $choice" >&2
    exit 1
    ;;
esac

echo ""
echo "Done."
