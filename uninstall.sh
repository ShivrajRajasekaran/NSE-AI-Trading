#!/bin/bash
# NSE-AI-Trading — Uninstall Script
set -e
echo "Removing NSE-AI-Trading skills..."
SKILLS_DIR="$HOME/.claude/skills"
rm -rf "$SKILLS_DIR/trade" "$SKILLS_DIR/trade-analyze" "$SKILLS_DIR/trade-intraday" "$SKILLS_DIR/trade-options" "$SKILLS_DIR/trade-swing" "$SKILLS_DIR/trade-crypto" "$SKILLS_DIR/trade-quick" "$SKILLS_DIR/trade-sector" "$SKILLS_DIR/trade-risk" "$SKILLS_DIR/trade-screen" "$SKILLS_DIR/trade-compare" "$SKILLS_DIR/trade-thesis" "$SKILLS_DIR/trade-macro" "$SKILLS_DIR/trade-expiry"
echo "Done. Skills removed. You may want to manually remove the entry from ~/.claude/CLAUDE.md"
