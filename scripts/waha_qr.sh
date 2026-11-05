#!/usr/bin/env bash
# Abre no navegador uma página com o QR AO VIVO do WAHA (renova a cada 4 s) e mantém a sessão
# "default" em espera de leitura, reiniciando-a sempre que o WhatsApp a derruba (a sessão desiste
# depois de ~2m40s sem leitura). Termina sozinho quando a sessão fica WORKING ou após 30 min.
# Leia com o CHIP RESERVA / número Business: WhatsApp → Dispositivos conectados → Conectar dispositivo.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
URL="${WAHA_URL:-http://localhost:3000}"; KEY="${WAHA_API_KEY:?defina WAHA_API_KEY no .env}"; H="X-Api-Key: $KEY"

status() { curl -sf -H "$H" "$URL/api/sessions/default" 2>/dev/null | sed -E 's/.*"status":"([A-Z_]+)".*/\1/' || echo NONE; }

s=$(status)
if [ "$s" = "WORKING" ]; then echo "sessão já conectada (WORKING) — nada a ler"; exit 0; fi
[ "$s" = "NONE" ] && curl -sf -X POST -H "$H" -H "Content-Type: application/json" "$URL/api/sessions" -d '{"name":"default","start":true}' >/dev/null

mkdir -p output
cat > output/waha_qr.html <<HTML
<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>QR do WAHA</title>
<style>body{margin:0;background:#111;color:#eee;font:18px -apple-system,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;gap:16px}
img{width:min(80vh,80vw);background:#fff;padding:16px;border-radius:12px}#st{font-size:22px}</style></head>
<body><div id="st">carregando…</div><img id="qr" alt="QR"><div>Leia com o WhatsApp do chip reserva → Dispositivos conectados → Conectar dispositivo. O código se renova sozinho.</div>
<script>
const U="$URL", H={"X-Api-Key":"$KEY"};
async function tick(){
  try{
    const s=await (await fetch(U+"/api/sessions/default",{headers:H})).json();
    document.getElementById("st").textContent="status: "+s.status;
    if(s.status==="WORKING"){document.getElementById("qr").style.display="none";document.getElementById("st").textContent="✅ conectado: "+(s.me?s.me.id:"");return;}
    if(s.status==="SCAN_QR_CODE"){const r=await fetch(U+"/api/default/auth/qr?format=image",{headers:H});
      if(r.ok){document.getElementById("qr").src=URL.createObjectURL(await r.blob());}}
  }catch(e){document.getElementById("st").textContent="erro: "+e;}
  setTimeout(tick,4000);
}
tick();
</script></body></html>
HTML
open output/waha_qr.html 2>/dev/null || echo "abra output/waha_qr.html no navegador"

echo "aguardando leitura (Ctrl+C para sair)…"
for _ in $(seq 1 360); do
  s=$(status)
  case "$s" in
    WORKING) echo "✅ conectado"; curl -sf -H "$H" "$URL/api/sessions/default" | sed -E 's/.*"me":\{"id":"([^"]+)".*/número: \1/'; exit 0 ;;
    FAILED|STOPPED) curl -sf -X POST -H "$H" "$URL/api/sessions/default/restart" >/dev/null || true ;;
  esac
  sleep 5
done
echo "tempo esgotado sem leitura"; exit 1
