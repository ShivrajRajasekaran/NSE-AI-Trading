# NSE-AI-Trading — Full Install Script (Windows PowerShell)
# Installs all 13 trading skills + KARTHIK persona
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "=== NSE-AI-Trading Installer ===" -ForegroundColor Cyan
Write-Host "=== KARTHIK - Indian Master Trading Analyst ===" -ForegroundColor Cyan
Write-Host ""

# 1. Python dependencies (optional)
Write-Host "[1/3] Checking Python dependencies..." -ForegroundColor Yellow
try { pip install reportlab 2>$null } catch { Write-Host "    reportlab skipped (optional - for PDF)" -ForegroundColor Gray }

# 2. Copy skills
Write-Host "[2/3] Installing slash commands..." -ForegroundColor Yellow
$skillsDir = Join-Path $env:USERPROFILE ".claude\skills"

# Main orchestrator
$destDir = Join-Path $skillsDir "trade"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
Copy-Item "trade\SKILL.md" -Destination "$destDir\SKILL.md" -Force

# Sub-skills
$skills = @("trade-analyze", "trade-intraday", "trade-options", "trade-swing", "trade-crypto", "trade-quick", "trade-sector", "trade-risk", "trade-screen", "trade-compare", "trade-thesis", "trade-macro", "trade-expiry")

foreach ($skill in $skills) {
    $destDir = Join-Path $skillsDir $skill
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Copy-Item "skills\$skill\SKILL.md" -Destination "$destDir\SKILL.md" -Force
}

Write-Host "    Installed 14 skills (1 orchestrator + 13 sub-skills)" -ForegroundColor Green

# 3. Add to CLAUDE.md
Write-Host "[3/3] Registering in CLAUDE.md..." -ForegroundColor Yellow
$claudeMd = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"

if (-not (Test-Path $claudeMd)) { New-Item -ItemType File -Force -Path $claudeMd | Out-Null }

$content = Get-Content $claudeMd -Raw -ErrorAction SilentlyContinue
if ($content -notmatch "NSE-AI-Trading") {
    $block = @"

# trade (NSE-AI-Trading - KARTHIK)
- **trade** (``~/.claude/skills/trade/SKILL.md``) - Indian Master Trading Analyst orchestrator. Trigger: ``/trade``
- **trade-analyze** (``~/.claude/skills/trade-analyze/SKILL.md``) - Full multi-dimensional analysis. Trigger: ``/trade analyze``
- **trade-intraday** (``~/.claude/skills/trade-intraday/SKILL.md``) - Intraday analysis. Trigger: ``/trade intraday``
- **trade-options** (``~/.claude/skills/trade-options/SKILL.md``) - Options strategy. Trigger: ``/trade options``
- **trade-swing** (``~/.claude/skills/trade-swing/SKILL.md``) - Swing trading. Trigger: ``/trade swing``
- **trade-crypto** (``~/.claude/skills/trade-crypto/SKILL.md``) - Crypto analysis. Trigger: ``/trade crypto``
- **trade-quick** (``~/.claude/skills/trade-quick/SKILL.md``) - 60-sec snapshot. Trigger: ``/trade quick``
- **trade-sector** (``~/.claude/skills/trade-sector/SKILL.md``) - Sector rotation. Trigger: ``/trade sector``
- **trade-risk** (``~/.claude/skills/trade-risk/SKILL.md``) - Risk assessment. Trigger: ``/trade risk``
- **trade-screen** (``~/.claude/skills/trade-screen/SKILL.md``) - Stock screener. Trigger: ``/trade screen``
- **trade-compare** (``~/.claude/skills/trade-compare/SKILL.md``) - Stock comparison. Trigger: ``/trade compare``
- **trade-thesis** (``~/.claude/skills/trade-thesis/SKILL.md``) - Investment thesis. Trigger: ``/trade thesis``
- **trade-macro** (``~/.claude/skills/trade-macro/SKILL.md``) - Macro overview. Trigger: ``/trade macro``
- **trade-expiry** (``~/.claude/skills/trade-expiry/SKILL.md``) - Weekly expiry strategy. Trigger: ``/trade expiry``
When the user types any ``/trade`` command, invoke the Skill tool with the matching skill name before doing anything else.
"@
    Add-Content -Path $claudeMd -Value $block
    Write-Host "    Added to CLAUDE.md" -ForegroundColor Green
} else {
    Write-Host "    CLAUDE.md already has NSE-AI-Trading (skipped)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== INSTALLATION COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available commands:" -ForegroundColor White
Write-Host "  /trade analyze <ticker>     Full 5-dimension analysis"
Write-Host "  /trade intraday <ticker>    Intraday setups & levels"
Write-Host "  /trade options <ticker>     Options strategy (Greeks, IV, OI)"
Write-Host "  /trade swing <ticker>       Swing trade plan (5-30 days)"
Write-Host "  /trade crypto <coin>        Crypto analysis"
Write-Host "  /trade quick <ticker>       60-second snapshot"
Write-Host "  /trade sector <sector>      Sector rotation"
Write-Host "  /trade risk <ticker>        Risk assessment"
Write-Host "  /trade screen <criteria>    Stock screener"
Write-Host "  /trade compare <t1> <t2>    Head-to-head comparison"
Write-Host "  /trade thesis <ticker>      Investment thesis"
Write-Host "  /trade macro                Market macro view"
Write-Host "  /trade expiry               Weekly expiry strategy"
Write-Host ""
Write-Host "Open Claude Code and type: /trade analyze RELIANCE" -ForegroundColor Green
Write-Host ""
Write-Host "- KARTHIK is ready." -ForegroundColor Cyan
