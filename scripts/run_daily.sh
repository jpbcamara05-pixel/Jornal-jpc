#!/usr/bin/env bash
# Executado pelo launchd (Mac) ou cron (VPS) às 06:30 America/Sao_Paulo, seg–sex.
set -euo pipefail
cd "$(dirname "$0")/.."
export TZ=America/Sao_Paulo
mkdir -p logs
source .venv/bin/activate
python -m briefing run >> "logs/$(date +%F).log" 2>&1
