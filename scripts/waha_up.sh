#!/usr/bin/env bash
# Sobe o WAHA (WhatsApp HTTP API, self-hosted) em Docker com as variáveis do .env.
# Pré-requisito: Docker rodando. Neste Mac: Colima (`brew services start colima` já deixa no ar ao logar).
# Depois de subir: abra http://localhost:3000, inicie a sessão "default" e leia o QR com o CHIP RESERVA.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
: "${WAHA_API_KEY:?defina WAHA_API_KEY no .env (qualquer string longa; é a senha da API local)}"

# Apple Silicon usa a imagem :arm (a :latest só tem build amd64)
IMAGE=devlikeapro/waha
[ "$(uname -m)" = "arm64" ] && IMAGE=devlikeapro/waha:arm

docker rm -f waha >/dev/null 2>&1 || true
docker run -d --name waha --restart unless-stopped \
  -p 3000:3000 \
  -v waha_sessions:/app/.sessions \
  -e WHATSAPP_DEFAULT_ENGINE=NOWEB \
  -e WAHA_API_KEY="$WAHA_API_KEY" \
  -e WAHA_DASHBOARD_USERNAME=admin -e WAHA_DASHBOARD_PASSWORD="$WAHA_API_KEY" \
  -e WHATSAPP_SWAGGER_USERNAME=admin -e WHATSAPP_SWAGGER_PASSWORD="$WAHA_API_KEY" \
  -e WHATSAPP_RESTART_ALL_SESSIONS=True \
  "$IMAGE"

echo "WAHA no ar. Painel: http://localhost:3000/dashboard  (usuário admin · senha = WAHA_API_KEY do .env)"
echo "QR para o chip reserva: scripts/waha_qr.sh  (ou no painel, sessão 'default')"
echo "Teste: python -m briefing test-delivery   →   python -m briefing test-delivery --sample"
