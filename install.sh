#!/bin/bash
# NSE-AI-Trading — Full Install Script
# Installs all 13 trading skills + KARTHIK persona
# Usage: bash install.sh

set -e

echo "=== NSE-AI-Trading Installer ==="
echo "=== KARTHIK — Indian Master Trading Analyst ==="
echo ""

# 1. Install Python dependencies (for PDF generation)
echo "[1/3] Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install reportlab 2>/dev/null || echo "    reportlab install skipped (optional — for PDF reports)"
else
    echo "    Python/pip3 not found — PDF generation won't work (optional)"
fi

# 2. Copy skills to Claude Code
echo "[2/3] Installing slash commands..."
SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$SKILLS_DIR"

# Main orchestrator
mkdir -p "$SKILLS_DIR/trade"
cp "trade/SKILL.md" "$SKILLS_DIR/trade/SKILL.md"

# Sub-skills
for skill in trade-analyze trade-intraday trade-options trade-swing trade-crypto trade-quick trade-sector trade-risk trade-screen trade-compare trade-thesis trade-macro trade-expiry; do
    mkdir -p "$SKILLS_DIR/$skill"
    cp "skills/$skill/SKILL.md" "$SKILLS_DIR/$skill/SKILL.md"
done

echo "    Installed 14 skills (1 orchestrator + 13 sub-skills)"

# 3. Add to CLAUDE.md
echo "[3/3] Registering in CLAUDE.md..."
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

if [ ! -f "$CLAUDE_MD" ]; then
    touch "$CLAUDE_MD"
fi

if ! grep -q "NSE-AI-Trading" "$CLAUDE_MD" 2>/dev/null; then
    cat >> "$CLAUDE_MD" << 'BLOCK'

# trade (NSE-AI-Trading — KARTHIK)
- **trade** (`~/.claude/skills/trade/SKILL.md`) - Indian Master Trading Analyst orchestrator. Trigger: `/trade`
- **trade-analyze** (`~/.claude/skills/trade-analyze/SKILL.md`) - Full multi-dimensional analysis. Trigger: `/trade analyze`
- **trade-intraday** (`~/.claude/skills/trade-intraday/SKILL.md`) - Intraday analysis. Trigger: `/trade intraday`
- **trade-options** (`~/.claude/skills/trade-options/SKILL.md`) - Options strategy. Trigger: `/trade options`
- **trade-swing** (`~/.claude/skills/trade-swing/SKILL.md`) - Swing trading. Trigger: `/trade swing`
- **trade-crypto** (`~/.claude/skills/trade-crypto/SKILL.md`) - Crypto analysis. Trigger: `/trade crypto`
- **trade-quick** (`~/.claude/skills/trade-quick/SKILL.md`) - 60-sec snapshot. Trigger: `/trade quick`
- **trade-sector** (`~/.claude/skills/trade-sector/SKILL.md`) - Sector rotation. Trigger: `/trade sector`
- **trade-risk** (`~/.claude/skills/trade-risk/SKILL.md`) - Risk assessment. Trigger: `/trade risk`
- **trade-screen** (`~/.claude/skills/trade-screen/SKILL.md`) - Stock screener. Trigger: `/trade screen`
- **trade-compare** (`~/.claude/skills/trade-compare/SKILL.md`) - Stock comparison. Trigger: `/trade compare`
- **trade-thesis** (`~/.claude/skills/trade-thesis/SKILL.md`) - Investment thesis. Trigger: `/trade thesis`
- **trade-macro** (`~/.claude/skills/trade-macro/SKILL.md`) - Macro overview. Trigger: `/trade macro`
- **trade-expiry** (`~/.claude/skills/trade-expiry/SKILL.md`) - Weekly expiry strategy. Trigger: `/trade expiry`
When the user types any `/trade` command, invoke the Skill tool with the matching skill name before doing anything else.
BLOCK
    echo "    Added to CLAUDE.md"
else
    echo "    CLAUDE.md already has NSE-AI-Trading (skipped)"
fi

echo ""
echo "=== INSTALLATION COMPLETE ==="
echo ""
echo "Available commands:"
echo "  /trade analyze <ticker>     Full 5-dimension analysis"
echo "  /trade intraday <ticker>    Intraday setups & levels"
echo "  /trade options <ticker>     Options strategy (Greeks, IV, OI)"
echo "  /trade swing <ticker>       Swing trade plan (5-30 days)"
echo "  /trade crypto <coin>        Crypto analysis"
echo "  /trade quick <ticker>       60-second snapshot"
echo "  /trade sector <sector>      Sector rotation"
echo "  /trade risk <ticker>        Risk assessment"
echo "  /trade screen <criteria>    Stock screener"
echo "  /trade compare <t1> <t2>    Head-to-head comparison"
echo "  /trade thesis <ticker>      Investment thesis"
echo "  /trade macro                Market macro view"
echo "  /trade expiry               Weekly expiry strategy"
echo ""
echo "Open Claude Code and type: /trade analyze RELIANCE"
echo ""
echo "— KARTHIK is ready."
