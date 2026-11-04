# Jornal · Briefing diário de notícias financeiras no WhatsApp

Todo dia útil, antes das 7h, no seu WhatsApp: **um PDF visual com as principais notícias e o que ler**, **3 notas de voz** (Mercado & Empresas · Economia · Política) e **um PDF com o Termômetro DCM** (sinais de nova emissão, refinanciamento e consent/waiver). Fontes: Valor Econômico e Brazil Journal (local, prioridade), Financial Times, New York Times e Wall Street Journal (internacional).

## Documentação

| Doc | O que tem |
|---|---|
| [01 · Visão geral](docs/01-visao-geral.md) | problema, entregáveis, fluxo em 5 linhas, princípios |
| [02 · Conteúdo](docs/02-conteudo.md) | **o contrato do produto**: página a página do PDF, roteiro dos áudios, Termômetro, regras editoriais, critérios de ranking |
| [03 · Arquitetura](docs/03-arquitetura.md) | pipeline, stack por componente, decisão de entrega (WhatsApp), custos, segurança, estrutura de pastas |
| [04 · Fontes](docs/04-fontes.md) | feeds/APIs/newsletters por veículo, acesso com assinatura, limites |
| [05 · Termômetro DCM](docs/05-termometro-dcm.md) | fontes estruturadas (CVM, B3, ANBIMA, fiduciários), taxonomia de sinais, fórmula da temperatura |
| [06 · Referências](docs/06-referencias.md) | projetos no GitHub e links que embasaram as decisões |
| [07 · Roadmap](docs/07-roadmap.md) | fases de implementação |

## Exemplo do resultado

`scripts/preview_pdf.py` renderiza os dois PDFs a partir de dados fictícios (`tests/fixtures/`) para validar o layout: `output/preview/briefing_exemplo.pdf` e `output/preview/termometro_dcm_exemplo.pdf`.

## Como rodar (fase 1)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
brew install ffmpeg            # conversão para nota de voz (OGG/Opus)
cp .env.example .env           # já feito: preencher ANTHROPIC_API_KEY, WHATSAPP_TO, provedor de entrega

python -m briefing run --until curate  # só coleta + curadoria (sem LLM, sem custo): olhe output/<dia>/stories.json
python -m briefing login valor         # 1x: abre o navegador, você loga no Globo, cookies ficam em browser_profile/
python -m briefing run --dry-run       # coleta → curadoria → síntese → PDFs/áudios em output/<dia>/ (sem enviar)
python -m briefing test-delivery       # "ping" no WhatsApp/Telegram
python -m briefing test-delivery --sample   # texto + 2 PDFs + 3 áudios de exemplo: prova o canal sem gastar LLM
python -m briefing run                 # pipeline completo
python -m briefing run --from render   # retoma de uma etapa sem recoletar/pagar LLM
```

Estado em 4/11/2026: ambiente instalado, coleta real e curadoria validadas, render (PDF + áudio) validado com dados fictícios em `output/preview/exemplo/`. Falta só o que depende de credenciais suas: chave da Anthropic, login no Valor e canal de entrega (ver checklist em `docs/07-roadmap.md`).

Agendamento no Mac: `scripts/com.jornal.briefing.plist` (launchd, seg–sex 06:30). Em VPS: cron chamando `scripts/run_daily.sh`.

### Como provar a entrega no WhatsApp antes de pagar qualquer API

1. `python scripts/preview_pdf.py --audio` gera em `output/preview/exemplo/` o conjunto fictício completo (2 PDFs + 3 notas de voz, TTS grátis).
2. `DELIVERY_PROVIDER=console python -m briefing test-delivery --sample` mostra no terminal a sequência exata que seria enviada.
3. Canal real, uma das duas rotas:
   - **WhatsApp via WAHA** (padrão): Docker na máquina (neste Mac: Colima, `brew services start colima` sobe ao logar; em outro, Docker Desktop/OrbStack), `WAHA_API_KEY` (qualquer string longa) e `WHATSAPP_TO` (seu número, DDI+DDD+número) no `.env`, `scripts/waha_up.sh` sobe o container (imagem `:arm` no Apple Silicon), `scripts/waha_qr.sh` abre o QR para ler com o **chip reserva** (WhatsApp → Dispositivos conectados). Painel em `http://localhost:3000/dashboard`, usuário `admin`, senha = `WAHA_API_KEY`. Depois `python -m briefing test-delivery --sample`. Os arquivos chegam no seu número principal como mensagens do chip reserva.
   - **Telegram** (zero risco, 10 min): criar bot no @BotFather, mandar "oi" para ele, pegar o `chat_id` em `https://api.telegram.org/bot<TOKEN>/getUpdates`, `DELIVERY_PROVIDER=telegram` no `.env`, `python -m briefing test-delivery --sample`.
4. Com o canal provado, a chave da Anthropic é o último elo: `python -m briefing run --dry-run` gera o briefing real e `python -m briefing run` envia.

## Estrutura

```
config/      settings.yaml (perfil do leitor, pesos, modelo) · sources.yaml (feeds) · dcm_signals.yaml (taxonomia)
briefing/    ingest/ → curate/ → summarize/ (Claude, prompts/*.md) → render/ (WeasyPrint, TTS) → deliver/ (WAHA | Cloud API | Telegram)
scripts/     run_daily.sh · launchd plist · preview_pdf.py
tests/       testes e fixtures de exemplo
output/      artefatos por dia (ignorado pelo git)
```

## Decisões que valem saber antes de começar

- **Entrega**: a API oficial do WhatsApp não envia áudio fora de uma janela de 24 h que só você abre; por isso o padrão é o **WAHA** (self-hosted, grátis) com um **chip reserva**, e o Telegram fica como rota de escape sem risco. Detalhe em [03 · Arquitetura](docs/03-arquitetura.md).
- **LLM**: Claude Opus 5.5 para a síntese, Haiku 5.5 para triagem em massa; saída estruturada (pydantic). Custo estimado ~US$ 0,50/dia.
- **Assinatura**: o login do Valor é feito uma vez no navegador; o pipeline reaproveita os cookies. Uso pessoal: o PDF traz resumo + link, não o texto integral.
