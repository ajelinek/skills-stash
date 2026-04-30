#!/usr/bin/env bash
# Install skills for OpenCode.
# Usage: bash install.sh

set -euo pipefail

# ── Skill lists ───────────────────────────────────────────────────────────────

install_ajelinek() {
  echo ""
  echo "Installing ajelinek/skills-stash skills..."
  npx skills add ajelinek/skills-stash typescript-engineering --yes
  npx skills add ajelinek/skills-stash testing --yes
  npx skills add ajelinek/skills-stash react --yes
  npx skills add ajelinek/skills-stash solid.js --yes
  npx skills add ajelinek/skills-stash astro.js --yes
  npx skills add ajelinek/skills-stash ui-engineering --yes
  npx skills add ajelinek/skills-stash astro-seo --yes
  npx skills add ajelinek/skills-stash cmux-workspace-builder --yes
  npx skills add ajelinek/skills-stash firebase-dynamic-ports-setup --yes
}

install_recommended() {
  echo ""
  echo "Installing recommended public skills..."

  echo "  [TypeScript & backend]"
  npx skills add wshobson/agents typescript-advanced-types --yes
  npx skills add wshobson/agents nodejs-backend-patterns --yes
  npx skills add wshobson/agents api-design-principles --yes
  npx skills add wshobson/agents auth-implementation-patterns --yes

  echo "  [Database & data]"
  npx skills add wshobson/agents postgresql-table-design --yes

  echo "  [Testing]"
  npx skills add currents-dev/playwright-best-practices-skill playwright-best-practices --yes
  npx skills add wshobson/agents e2e-testing-patterns --yes

  echo "  [SEO & marketing]"
  npx skills add coreyhaines31/marketingskills seo-audit --yes
  npx skills add coreyhaines31/marketingskills ai-seo --yes
}

# ── Main ──────────────────────────────────────────────────────────────────────

echo ""
echo "OpenCode Skill Installer"
echo "========================"
echo ""
echo "Installing all skills (ajelinek/skills-stash + recommended public skills)..."

install_ajelinek
install_recommended

echo ""
echo "Done."
