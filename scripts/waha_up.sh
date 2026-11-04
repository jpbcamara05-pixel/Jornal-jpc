#!/usr/bin/env bash
# Sobe o WAHA (WhatsApp HTTP API, self-hosted) em Docker com as variáveis do .env.
# Pré-requisito: Docker rodando (Docker Desktop, OrbStack ou `brew install colima docker && colima start`).
# Depois de subir: abra http://localhost:3000, inicie a sessão "default" e leia o QR com o CHIP RESERVA.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
: "${WAHA_API_KEY:?defina WAHA_API_KEY no .env (qualquer string longa; é a senha da API local)}"

docker rm -f waha >/dev/null 2>&1 || true
docker run -d --name waha --restart unless-stopped \
  -p 3000:3000 \
  -v waha_sessions:/app/.sessions \
  -e WHATSAPP_DEFAULT_ENGINE=NOWEB \
  -e WAHA_API_KEY="$WAHA_API_KEY" \
  -e WHATSAPP_RESTART_ALL_SESSIONS=True \
  devlikeapro/waha

echo "WAHA no ar: http://localhost:3000  (Swagger: /  · QR da sessão: POST /api/sessions/default/start e GET /api/default/auth/qr)"
echo "Teste: python -m briefing test-delivery   →   python -m briefing test-delivery --sample"
