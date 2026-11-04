#!/usr/bin/env bash
# Garante que a sessão "default" do WAHA está iniciada e abre o QR atual no Preview.
# O QR muda a cada ~30 s: se expirar antes de ler, rode de novo. Leia com o CHIP RESERVA
# (WhatsApp → Dispositivos conectados → Conectar dispositivo).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
URL="${WAHA_URL:-http://localhost:3000}"; H="X-Api-Key: ${WAHA_API_KEY:?defina WAHA_API_KEY no .env}"

status=$(curl -sf -H "$H" "$URL/api/sessions/default" | sed -E 's/.*"status":"([A-Z_]+)".*/\1/' || echo "NONE")
case "$status" in
  WORKING) echo "sessão já conectada (WORKING) — nada a ler"; exit 0 ;;
  NONE)    curl -sf -X POST -H "$H" -H "Content-Type: application/json" "$URL/api/sessions" -d '{"name":"default","start":true}' >/dev/null ;;
  STOPPED|FAILED) curl -sf -X POST -H "$H" "$URL/api/sessions/default/start" >/dev/null ;;
esac
for _ in 1 2 3 4 5 6 7 8 9 10; do
  s=$(curl -sf -H "$H" "$URL/api/sessions/default" | sed -E 's/.*"status":"([A-Z_]+)".*/\1/')
  [ "$s" = "SCAN_QR_CODE" ] && break
  sleep 2
done
mkdir -p output && curl -sf -H "$H" "$URL/api/default/auth/qr?format=image" -o output/waha_qr.png
echo "QR salvo em output/waha_qr.png (status: $s)"; open output/waha_qr.png 2>/dev/null || true
