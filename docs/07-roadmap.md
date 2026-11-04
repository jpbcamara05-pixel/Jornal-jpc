# 07 · Roadmap

Ordem pensada para ter algo útil no WhatsApp o mais cedo possível e só depois sofisticar.

## Fase 0 · Fundação (feita)
- [x] Especificação de conteúdo, modelos de dados, prompts, templates de PDF validados com dados de exemplo.
- [x] Esqueleto do pipeline com retomada por etapa; provedores de entrega (WAHA, Cloud API, Evolution, Telegram).
- [x] Pesquisa de referências (entrega, fontes, geração, DCM).

## Fase 1 · Primeiro briefing de ponta a ponta (1–2 dias de trabalho)
- [x] `pip install -e ".[dev]"` + `playwright install chromium` + `brew install ffmpeg` (feito em 4/11/2026; Python 3.14, ffmpeg 9).
- [x] Coleta real validada (`python -m briefing run --until curate`, 4/11/2026): Valor 333 (110 do impresso), Brazil Journal 10, FT 79, WSJ 138, CVM 139, Vórtx 40 → 136 histórias para o LLM, ~54k tokens de prompt.
- [x] Render validado com fixtures (`output/preview/exemplo/`): 2 PDFs + 3 notas de voz OGG/Opus via edge-tts + ffmpeg em 28 s.
- [ ] **Você:** `ANTHROPIC_API_KEY` no `.env`; depois `python -m briefing run --until summarize` e ler `output/<dia>/briefing.json`; ajustar `reader_profile` e prompts.
- [ ] **Você:** `python -m briefing login valor` (1x) → texto integral dos ~60 itens mais proeminentes (hoje só 49/136 histórias têm texto, as abertas no RSS).
- [ ] **Você:** `NYT_API_KEY` (grátis) e, se quiser, IMAP das newsletters.
- [ ] Entrega: Telegram primeiro (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`, `DELIVERY_PROVIDER=telegram`, `python -m briefing test-delivery`); depois WAHA com chip reserva.
- [ ] launchd às 06:30 seg–sex (`scripts/com.jornal.briefing.plist`) — só depois que o `run --dry-run` completo passar.

## Fase 2 · Qualidade editorial (1–2 semanas de uso)
- Newsletters por IMAP (Valor, Brazil Journal, FirstFT, The Morning, 10-Point) como sinal de proeminência.
- Raspagem da capa / edição impressa do Valor para `prominence` real.
- Embeddings multilíngues no cluster (mesma história em PT e EN).
- Painel de contexto (Ibovespa, dólar, DI, NTN-B, Treasury) e agenda do dia no PDF.
- Voz premium (OpenAI/ElevenLabs) se o edge-tts não agradar.
- Loop de feedback: responder "👍/👎 + id" no WhatsApp alimenta o ranking.

## Fase 3 · Termômetro DCM de verdade
- Já implementados na fase 0: CVM IPE (AGDEB, avisos aos debenturistas, fatos relevantes de dívida), ofertas RCVM 160, página de ofertas da B3, eventos ativos da Vórtx; score determinístico em `dcm_score.py`.
- Adicionar: RAD `ListarDocumentos` de hora em hora (quase tempo real), XLSX de autorizações da B3, Fundos.NET (FIDC/CRI/CRA), Valor RI e Oliveira Trust via headless, PDF do Diário Comercial, SND/ANBIMA Data para o muro de vencimentos.
- Radar com status (novo / acompanhando / concluído) editável por mensagem no WhatsApp.
- Cruzar sinais com base de emissões em circulação (SND/ANBIMA) para "vencimentos próximos" automáticos.
- Histórico semanal: termômetro como série temporal.

## Fase 4 · Conforto
- Comando no WhatsApp: "resumo de X" devolve o card e o link; "áudio de novo" reenvia.
- Edição de fim de semana (sábado: leitura longa; domingo: agenda da semana).
- Migrar para VPS pequeno com Docker (WAHA + pipeline) para não depender do Mac ligado.
