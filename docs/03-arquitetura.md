# 03 · Arquitetura e stack

## Fluxo

```
            ┌──────────────── 1. COLETA (ingest/) ──────────────────┐
 Valor RSS ─┤  feedparser  →  Article                                │
 BJ RSS ────┤  NYT API / FT RSS / WSJ RSS                            │  ~300 artigos
 Newsletters┤  IMAP (Gmail): Valor, BJ, FirstFT, The Morning, 10-Pt  │  SQLite (dedup histórico)
 Valor login┤  Playwright perfil persistente → texto integral top-N  │
 DCM ───────┤  Valor Legais · CVM · B3 · agentes fiduciários          │
            └───────────────────────────┬───────────────────────────┘
                                        ▼
            ┌──────────────── 2. CURADORIA (curate/) ────────────────┐
            │ dedup URL/título → cluster entre veículos (rapidfuzz)   │  ~40 histórias
            │ score = proeminência · cobertura · relevância (Haiku) · │
            │         recência  ·  penaliza já-enviado                │
            └───────────────────────────┬───────────────────────────┘
                                        ▼
            ┌──────────────── 3. SÍNTESE (summarize/) ───────────────┐
            │ Claude Opus 5.5 · messages.parse → pydantic            │
            │   Briefing JSON  →  3 AudioScript  →  DCMReport         │
            │ (prompts estáveis cacheados; Haiku para triagem em lote)│
            └───────────────────────────┬───────────────────────────┘
                                        ▼
            ┌──────────────── 4. RENDER (render/) ───────────────────┐
            │ Jinja2 + CSS → WeasyPrint → PDF (A4, cards)             │
            │ TTS (edge-tts | OpenAI | ElevenLabs) → ffmpeg → OGG/Opus│
            └───────────────────────────┬───────────────────────────┘
                                        ▼
            ┌──────────────── 5. ENTREGA (deliver/) ─────────────────┐
            │ texto → PDF → 3 notas de voz → PDF DCM                  │
            │ WAHA (padrão) | Meta Cloud API | Evolution | Telegram   │
            └────────────────────────────────────────────────────────┘
```

Cada etapa grava seu resultado em `output/AAAA-MM-DD/` (`articles.json`, `stories.json`, `briefing.json`, `audio_scripts.json`, `dcm.json`, PDFs, OGGs, `run.json`). `python -m briefing run --from render` retoma sem recoletar nem pagar LLM de novo.

## Stack por componente

| Componente | Escolha | Por quê | Alternativa |
|---|---|---|---|
| Linguagem | **Python 3.11+** | melhor ecossistema para scraping, LLM, PDF e TTS | Node (se preferir Baileys nativo) |
| Feeds | **feedparser** | RSS/Atom padrão, robusto a feeds malformados | — |
| Texto integral | **trafilatura** (+ **Playwright** perfil persistente para paywall) | trafilatura é o extrator com melhor precisão em páginas de jornal; Playwright reaproveita o login feito uma vez | newspaper4k, readability-lxml |
| Newsletters | **imaplib** (Gmail, senha de app) | a newsletter é a curadoria do editor, chega sem anti-bot | Gmail API |
| Dedup/cluster | **rapidfuzz** (fase 1) → embeddings multilíngues (fase 2) | título similar pega 90% dos casos; embeddings pegam PT×EN | — |
| LLM | **Claude Opus 5.5** (síntese) + **Claude Haiku 5.5** (triagem em lote) | saída estruturada validada por pydantic; cache do system prompt; fallback de recusa | Sonnet 5.5 na síntese se custo apertar |
| PDF | **WeasyPrint** (HTML/CSS → PDF), página em **formato de celular** (420×760 pt, corpo 14 pt) | layout de cards com CSS normal, `break-inside: avoid`, sem navegador; o WhatsApp abre o PDF ajustado à largura da tela, A4 fica ilegível; validado em `scripts/preview_pdf.py` | Playwright `page.pdf()`, Typst; variante A4 por configuração |
| TTS | **edge-tts** no desenvolvimento (grátis, sem conta) → **Google Cloud Chirp 3 HD** em produção (30 vozes pt-BR, **1M chars/mês sempre grátis**, OGG/Opus nativo) | nosso volume (~120k chars/mês) cabe no free tier; edge-tts usa endpoint não oficial e pode quebrar | Azure (500k grátis/mês), OpenAI gpt-4o-mini-tts (~US$ 2/mês), ElevenLabs (US$ 22/mês, melhor prosódia) |
| Áudio | **ffmpeg** → OGG/Opus mono, ~24 kbps VBR, `application voip`, loudnorm | formato de nota de voz (PTT) no WhatsApp; 4 min ≈ 600 KB | — |
| Entrega | **WAHA** (Docker) · ver seção abaixo | único caminho gratuito que envia PDF **e** áudio proativamente | Meta Cloud API · Telegram |
| Estado | **SQLite** | zero infra; histórico para dedup entre dias e radar DCM | Postgres se virar multiusuário |
| Agendamento | **launchd** (Mac, com `pmset repeat wakeorpoweron` para o Mac estar acordado) ou **systemd timer** (Raspberry/VPS) | precisa de IP residencial e perfil de navegador em disco; IPs do GitHub Actions são bloqueados por Cloudflare/DataDome | GitHub Actions só para RSS/API (ou com exit node Tailscale em casa); Modal/Cloud Run para a parte sem login |

## Entrega no WhatsApp: a decisão

Pesquisa de novembro/2026 (fontes em [06-referencias.md](06-referencias.md)):

| Opção | Custo/mês | Envia PDF | Envia nota de voz | Proativo às 06:45? | Risco de ban | Fricção |
|---|---|---|---|---|---|---|
| **WAHA** (self-hosted, grátis desde 2026.6) | R$ 0 | sim | sim (`sendVoice`) | **sim** | não-zero (sessão não oficial) | baixa: 1 container + QR |
| Meta Cloud API, número de teste | R$ 0 | sim (template) | só dentro da janela de 24 h | PDF sim; **áudio não** | nenhum | média: app Meta, token, template, webhook |
| Meta Cloud API, 2º número registrado | ≈ R$ 1 | sim | idem | idem | nenhum | média-alta |
| Evolution API | R$ 0 (+ ativação de licença desde v2.4) | sim | sim | sim | não-zero | média: Postgres/Redis |
| Twilio sandbox | ~US$ 1 | sim | só na janela | não (rejoin a cada 3 dias; Brasil pode ser restrito) | nenhum | baixa |
| Z-API | R$ 99,99 | sim | sim | sim | não-zero | mínima |
| Telegram bot | R$ 0 | sim | sim | **sim** | nenhum | trivial |

Fatos que decidem:
- A API oficial só envia mensagem livre (e áudio) dentro de uma **janela de 24 h aberta por você**; fora dela, só templates, e template **não aceita áudio**. Então o fluxo oficial exige um toque seu por dia (botão no template do PDF) para liberar os áudios.
- A partir de 1/10/2026 a API oficial tem 1.000 mensagens de serviço grátis por mês por número; nosso volume (~150/mês) cabe folgado.
- Bibliotecas não oficiais (Baileys, whatsapp-web.js, WAHA, Evolution) violam os termos do WhatsApp; o risco é real (dezenas de issues de ban em 2026 no Baileys). Mitigação: **chip reserva**, volume mínimo, um contato só.

**Decisão:** `whatsapp_waha` como padrão (experiência exatamente como pedida: tudo chega sozinho de manhã), com chip reserva. `whatsapp_cloud` implementado como alternativa oficial (PDF via template + áudios após um toque). `telegram` como rota de escape de 10 linhas caso o chip reserva não compense. Trocar é uma variável de ambiente.

## Decisões de LLM

- **Saída estruturada** (`messages.parse` + pydantic): o PDF, os áudios e o Termômetro são renderizados a partir de JSON validado; o modelo não escreve HTML nem markdown.
- **Dois modelos, dois estágios**: Haiku 5.5 pontua relevância de ~300 títulos (rubrica pontual) e extrai sinais DCM em lote (centavos); Opus 5.5 faz a passada editorial *listwise* (escolhe os cards, escreve "por que importa" e "leia hoje"), três roteiros de áudio e o termômetro. É o padrão dos projetos de referência (Horizon, vigorX777).
- **Sinais de ranking antes do LLM**: proeminência na fonte (edição impressa do Valor, capa dos feeds), **cobertura cruzada** (nº de veículos no mesmo cluster, o sinal barato que melhor correlaciona com importância, arXiv 2402.10302), recência e "já enviado". Timestamps entram como idade relativa para evitar viés de recência.
- **Continuidade**: o briefing de ontem (manchete + 30 segundos) entra no prompt para o modelo não reapresentar como novo e dizer "o que mudou".
- **Termômetro: LLM extrai, código pontua.** O modelo pequeno classifica cada documento na taxonomia e extrai valor, data, tipo de fonte e evidência literal; `dcm_score.py` calcula o score 0–100 com pesos do YAML (reprodutível, auditável); o modelo principal só escolhe o top 5 e escreve a justificativa.
- **Cache de prompt**: o system prompt (perfil do leitor + regras editoriais) é o prefixo estável e leva `cache_control`; as histórias do dia vêm depois.
- **Fallback de recusa** ligado (`fallbacks="default"`) para o pipeline não parar por um falso positivo de segurança.
- **Custo estimado**: ~US$ 0,50/dia (≈ 30k tokens de entrada e 10k de saída no Opus + triagem no Haiku) → ~US$ 11/mês. TTS: R$ 0 com edge-tts; ~US$ 1–2/mês com OpenAI; ElevenLabs a partir de US$ 5/mês.

## Segurança e conformidade

- Segredos só em `.env` (ignorado pelo git). Perfil do navegador com cookies em `browser_profile/` (ignorado).
- Conteúdo assinado: uso pessoal; o PDF traz **resumo + link**, nunca o texto integral; fonte visível em todo card. Ritmo humano na coleta logada (pausa de 2–5 s, ≤ 60 páginas/dia por fonte). FT/NYT/WSJ têm anti-bot forte: priorizar newsletters por e-mail + RSS; texto integral só se a assinatura existir e com parcimônia.
- Falha de uma fonte não derruba o briefing (try/except por coletor; o PDF informa quais fontes entraram).
- Sessão expirada é detectada (paywall na página) e vira aviso no WhatsApp: "refaça `python -m briefing login valor`".

## Observabilidade

`output/<dia>/run.json` guarda contagens, custo de LLM, caracteres de TTS, erros. `logs/<dia>.log` tem o detalhe. Falha total → mensagem de texto no WhatsApp com o erro (nunca silêncio).

## Estrutura de pastas

```
Jornal/
├── README.md
├── docs/                      01 visão · 02 conteúdo · 03 arquitetura · 04 fontes · 05 termômetro · 06 referências · 07 roadmap
├── config/
│   ├── settings.yaml          perfil do leitor, pesos de ranking, quotas, modelo
│   ├── sources.yaml           feeds/URLs por veículo, pesos por editoria, newsletters
│   └── dcm_signals.yaml       taxonomia e palavras-chave do Termômetro
├── briefing/                  pacote Python
│   ├── models.py              Article · Story · Briefing · AudioScript · DCMReport
│   ├── pipeline.py / cli.py   orquestração e linha de comando
│   ├── ingest/                valor · braziljournal · intl (FT/NYT/WSJ) · newsletters · dcm_sources · browser · rss
│   ├── curate/                dedup (cluster) · rank
│   ├── summarize/             client (Claude) · briefing · audio_script · dcm · prompts/*.md
│   ├── render/                pdf (WeasyPrint) · audio (TTS+ffmpeg) · templates/*.html, base.css
│   ├── deliver/               whatsapp_waha · whatsapp_cloud · whatsapp_evolution · telegram
│   └── storage/db.py          SQLite
├── scripts/                   run_daily.sh · launchd plist · preview_pdf.py
├── tests/                     testes + fixtures de exemplo
└── output/<dia>/              artefatos de cada execução (ignorado pelo git)
```
