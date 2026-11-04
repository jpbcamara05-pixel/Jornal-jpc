# 06 · Referências

Pesquisa feita em 4/11/2026. Links verificados na data; estrelas/último commit via API do GitHub.

## A. Entrega no WhatsApp

### Fatos que mudam o desenho
- API oficial (Meta Cloud API): mensagem livre só dentro da janela de 24 h aberta pelo usuário; fora dela só templates, e o cabeçalho de template aceita TEXT/IMAGE/VIDEO/DOCUMENT, **não AUDIO**. Preços e janela: https://developers.facebook.com/docs/whatsapp/pricing · componentes de template: https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components
- A partir de 1/10/2026: 1.000 mensagens de serviço grátis/mês por número; template utility para o Brasil ≈ US$ 0,0068 (≈ R$ 0,035). Fonte Meta acima; tabela em BRL (terceiros): https://chatmaxima.com/whatsapp-api-pricing/brazil/
- Número de teste da Meta: até 5 destinatários, grátis, sem expiração documentada: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/
- Nota de voz na API oficial: `"voice": true` com OGG/Opus mono: https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/audio-messages · limites de mídia: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media
- Um número não pode estar no app pessoal e na API ao mesmo tempo: https://docs.360dialog.com/docs/hub/embedded-signup/confirm-number-details
- Termos do WhatsApp proíbem clientes não oficiais: https://www.whatsapp.com/legal/terms-of-service · issues de ban no Baileys em 2026: https://github.com/WhiskeySockets/Baileys/issues/2805 · https://github.com/WhiskeySockets/Baileys/issues/2707
- Twilio sandbox: rejoin a cada 3 dias, 1 msg/3 s, pode ser restrito para o Brasil: https://www.twilio.com/docs/whatsapp/sandbox

### Bibliotecas / serviços
| Projeto | Stars · último push | Nota |
|---|---|---|
| WAHA — https://github.com/devlikeapro/waha | 7.7k · nov/2026 | REST em Docker; `sendFile`, `sendVoice` (converte para Opus); tudo grátis desde a 2026.6: https://waha.devlike.pro/blog/waha-2026-6/ · docs: https://waha.devlike.pro/docs/how-to/send-messages/ |
| Baileys — https://github.com/WhiskeySockets/Baileys | 11.5k · nov/2026 | Node, sem navegador; `ptt: true` para nota de voz |
| whatsapp-web.js — https://github.com/wwebjs/whatsapp-web.js | 22.8k · nov/2026 | Puppeteer/Chromium; `sendAudioAsVoice` |
| Evolution API — https://github.com/evolution-foundation/evolution-api | 10k · jul/2026 | exige ativação de licença desde v2.4 (https://docs.evolutionfoundation.com.br/licensing); Postgres/Redis |
| Z-API — https://www.z-api.io/ | SaaS BR | R$ 99,99/mês por canal; sessão não oficial |
| Telegram Bot API — https://core.telegram.org/bots/api | — | `sendDocument`/`sendVoice` até 50 MB, sem janela, grátis |

### Projetos "notícias → WhatsApp"
- https://github.com/amoolya93/WhatsappNewsDigest — Python; Claude resume manchetes e envia pela Cloud API via GitHub Actions (o mais próximo do caminho oficial).
- https://github.com/dhruubb/news-chatbot — briefing diário de mercado (Índia) filtrado por LLM, envio por Twilio.
- https://github.com/eduardosoliv/lookout-wire — agente pessoal de notícias financeiras/alertas com IA, GitHub Actions.
- https://github.com/payaltandon-xyz/whatsapp-news-group-bot — digests com Baileys.
- https://github.com/polleichtnermoritz/news-digest — digest com entrega por Telegram (boa referência do módulo de notificação).
- https://github.com/n0thingistrue/StayAIware · https://github.com/Muazz4502/ai-news-whatsapp · https://github.com/josesubiabre/morning-tech-digest — RSS + LLM + Twilio/CallMeBot.
- Brasileiros (resumo de grupo, úteis pela fiação WAHA/Evolution): https://github.com/tiberiolemes/resumo-grupo-whatsapp · https://github.com/felixskmarcio/whatsapp-group-summary · https://github.com/moiseszip/whatsapp-group-summary

## B. Geração do briefing (ranking, LLM, PDF, áudio, agendamento)

### Projetos de referência (ponta a ponta)
| Repo | Stars · último push | O que ensina |
|---|---|---|
| https://github.com/Thysrael/Horizon | 12,3k · nov/2026 · MIT | "Radar de notícias com IA": HN/RSS/Reddit/Google News/GDELT, texto integral via trafilatura, **rubrica de pontuação por perfil com limiares**, dedup por tópico, balanceamento por categoria, briefing em Markdown; GH Actions/Docker. Base de `profiles/` e `docs/scoring.md` reutilizável |
| https://github.com/iliane5/meridian | 2,4k · mai/2025 | "Agência de inteligência pessoal": centenas de RSS, fallback de render para paywall, **embeddings → UMAP → HDBSCAN** para agrupar a mesma história, prompts multi-estágio, usa o TLDR de ontem para continuidade |
| https://github.com/sansan0/TrendRadar | 63k · out/2026 · GPL | Monitor de listas quentes + RSS com pesos por palavra-chave e **filtro de interesse por IA com limiar**; modo incremental "só o novo"; push multi-canal |
| https://github.com/leiting-eric/DailyBrief | 386 · nov/2026 · MIT | Briefing diário com **fontes financeiras (Bloomberg, WSJ, FT, Economist)**, painel de mercado (Yahoo Finance + comentário do LLM), HTML único, workflow com "trava de fuso horário" |
| https://github.com/vigorX777/ai-daily-digest | 1,7k · fev/2026 · sem licença | IA pontua cada artigo **1–10 em relevância / qualidade / atualidade** numa chamada só; top-N; "por que ler". Só ideias (sem licença) |
| https://github.com/kagisearch/kite-public | 1,1k · out/2026 | Listas de feeds curadas do Kagi News (`kite_feeds.json`), ≥ 25 feeds por categoria; uma edição por dia |
| https://github.com/newsnext/newsnow | 22k · out/2026 | Agregador em tempo real com "calor" por fonte (sinal de proeminência) |
| https://github.com/finaldie/auto-news · https://github.com/piqoni/matcha · https://github.com/yinan-c/RSSbrew · https://github.com/grbtm/news-briefing-generator | — | Padrões de "já visto", filtros e agendamento |

### Áudio / podcast
| Repo | Stars · último push | O que ensina |
|---|---|---|
| https://github.com/DynamicDevices/audionews | novo · out/2026 | **A forma mais próxima deste projeto**: manchetes → Claude → texto normalizado para TTS → edge-tts (ou ElevenLabs) → ffmpeg (compressão de silêncio) → RSS de podcast; GH Actions 05:00 UTC. Ver `digest/tts.py`, `config/ai_prompts.json` |
| https://github.com/souzatharsis/podcastfy | 6,8k · mai/2026 · Apache | Conversa de dois apresentadores; backends OpenAI/Google/ElevenLabs/Edge; exemplo em pt-BR |
| https://github.com/SSShogunn/InkCast | novo · jun/2026 | RSS → dedup 30 dias → roteiro falado numa chamada → Kokoro local; **memória de "fios de história"** para continuidade |
| https://github.com/miantiao-me/hacker-podcast | 2,6k · out/2026 · AGPL | HN → roteiro de locução → Edge TTS → podcast |
| https://github.com/engineervix/zed-news | 11 · nov/2026 | Digest diário (Zâmbia) com prompts otimizados por DSPy; **produziu ~500 episódios de áudio e depois abandonou o áudio** (custo de manutenção) |

### Técnicas de seleção das "principais"
- Tamanho do cluster (quantos veículos cobrem o mesmo fato) é o sinal barato que melhor correlaciona com importância julgada por LLM: https://arxiv.org/abs/2402.10302 (embedding de título + ~1.000 chars basta).
- Fatores do Google News: relevância, proeminência, autoridade, atualidade: https://www.google.ca/search/howsearchworks/how-news-works
- Dois estágios de LLM: pontuação pontual (rubrica 1–10) nos ~40 clusters → **passada editorial listwise** que escolhe 10–12 e escreve "por que ler". Cuidado com viés de recência ao injetar timestamps: https://arxiv.org/abs/2509.11353
- Produtos: Particle.news (clusters multi-fonte), Perplexity Discover (curadoria + personalização), Kagi News (só RSS, uma edição/dia).

### TTS pt-BR (custo para ~120k chars/mês)
| Provedor | Vozes pt-BR | Grátis | Custo neste volume | Nota |
|---|---|---|---|---|
| **Google Cloud Chirp 3 HD** | 30 (`pt-BR-Chirp3-HD-Kore/Leda/Charon/Puck…`) | **1M chars/mês sempre** | **US$ 0** | OGG_OPUS nativo, `speaking_rate`, `[pause]`. https://cloud.google.com/text-to-speech/pricing |
| Azure Neural / HD | Francisca, Antonio, Thalita, MAI-Voice-2 (Caio, Luana…) | F0: 500k/mês | US$ 0 (F0) | https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support |
| OpenAI gpt-4o-mini-tts | 13 vozes (otimizadas p/ inglês) | — | ~US$ 2 | `instructions` para tom; sotaque pode oscilar. https://developers.openai.com/api/docs/pricing |
| ElevenLabs Multilingual v2 | biblioteca | 10k créditos | US$ 22 (Creator) | melhor prosódia; conta de créditos é a pegadinha. https://elevenlabs.io/pricing |
| Amazon Polly | Camila, Vitória, Thiago (+ generativas) | 12 meses | US$ 0 → ~US$ 2 | OGG Vorbis (não Opus) → reencodar |
| edge-tts | Antonio, Francisca, Thalita | — | US$ 0 | endpoint não oficial; ótimo p/ dev, frágil p/ produção. https://github.com/rany2/edge-tts |
| Kokoro / Piper (local) | poucas | — | US$ 0 | qualidade inferior em pt-BR; auditar |

Nota de voz no WhatsApp: OGG com codec **Opus, mono**, ≤ 16 MB; `voice: true` na Cloud API; ícone de play inline só se ≤ 512 KB (https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/audio-messages). Receita ffmpeg: libopus, 1 canal, ~24 kbps VBR, `application voip`.

### PDF
- WeasyPrint (9,8k★): CSS Paged Media completo, grid/flex, fontes embutidas, sem navegador. https://doc.courtbouillon.org/weasyprint/stable/api_reference.html
- Alternativas: Playwright `page.pdf()` (JS, mais pesado), Typst (57k★, ótima tipografia, outra linguagem).
- **Leitura no celular**: o WhatsApp mostra a página 1 como miniatura e abre ajustado à largura da tela; A4 com 11 pt vira ~7 px. Daí o formato de página ~400×720 pt com corpo 15–16 pt, uma coluna, 2–3 cards por página. https://foxit.com/blog/how-to-make-pdfs-mobile-friendly

### Agendamento
- GitHub Actions: cron em UTC (06:30 BRT = `30 9 * * 1-5`), atrasa em horário cheio (use minuto ímpar), desativa após 60 dias sem commit em repo público, **IPs de datacenter Azure bloqueados por Cloudflare/DataDome** (https://simonwillison.net/2025/Feb/23/tailscale-github-actions). https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Mac/launchd: `StartCalendarInterval` roda job perdido no próximo despertar; usar `pmset repeat wakeorpoweron` (https://www.josephspurrier.com/macos-sleep-cron). Raspberry: systemd timer com `Persistent=true`.
- Modal (US$ 30 de crédito/mês, cron com fuso IANA), Cloud Run Jobs + Scheduler (3 jobs grátis), Render (US$ 1/mês por cron), Railway — todos com IP de datacenter.

## C. Fontes de notícias e DCM

Detalhe por veículo em [04-fontes.md](04-fontes.md); fontes estruturadas em [05-termometro-dcm.md](05-termometro-dcm.md). Links-chave:
- Valor feeds: `https://pox.globo.com/rss/valor/` (+ editorias), `https://pox.globo.com/rss/pipelinevalor/`, `https://pox.globo.com/rss/valorinveste/`, `https://pox.globo.com/rss/valorinternational/` · edição impressa: `https://valor.globo.com/impresso/` · newsletters: `https://valor.globo.com/newsletter/cardapio/`
- Conta Globo / cookie GLBID (padrão usado pelo yt-dlp): https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/globo.py · Playwright auth: https://playwright.dev/python/docs/auth
- Brazil Journal: `https://braziljournal.com/feed` · newsletter `https://braziljournal.com/newsletter`
- FT: `https://www.ft.com/rss/home/international`, seções com `?format=rss` · developer.ft.com (B2B) · NYT: `https://www.nytimes.com/rss`, API https://developer.nytimes.com/ · WSJ: `https://feeds.content.dowjones.io/public/rss/RSSMarketsMain` etc.
- CVM Dados Abertos: ofertas https://dados.cvm.gov.br/dataset/oferta-distrib · IPE https://dados.cvm.gov.br/dataset/cia_aberta-doc-ipe · RAD https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx
- B3: ofertas em andamento https://www.b3.com.br/pt_br/produtos-e-servicos/solucoes-para-emissores/ofertas-publicas/ofertas-em-andamento/empresas/publicacao-de-ofertas-publicas/ · Fundos.NET https://fnet.bmfbovespa.com.br/fnet/publico/abrirGerenciadorDocumentosCVM
- ANBIMA: https://data.anbima.com.br/ · https://www.debentures.com.br/ (a ser descontinuado) · https://developers.anbima.com.br/
- Publicidade legal (Lei 13.818/19, art. 289 LSA): cartilha ANJ https://www.anj.org.br/wp-content/uploads/2024/01/2024-Publicidade-Legal-S.As-edicao-jan24.pdf
- Repos: `lucastlsabara/anbima-debentures-monitor`, `mai0li/docvments` (RAD), `jackrj090603-prog/fatos-relevantes-cvm`, `araujovito/radar-cvm`, `wilsonfreitas/rbmfbovespa` (API GetMaterialFacts da B3)

## D. DCM

### Projetos e ferramentas
| Repo | Stars · último push | O que faz |
|---|---|---|
| https://github.com/danxhp/cvm-fatos-relevantes | 0 · nov/2026 | Monitor do RAD (`ListarDocumentos`) por watchlist, resumos com Claude, e-mail, GH Actions — **template mais próximo do termômetro** |
| https://github.com/wilsonfreitas/brasa | 56 · nov/2026 | Extração de dados B3, ANBIMA, CVM em Python — melhor base genérica |
| https://github.com/marvin-monitoramento/marvin-cvm-fatos-relevantes | 0 · nov/2026 | Baixa IPE, watchlist de devedores, histórico CSV, alertas |
| https://github.com/robertoecf/OpenFinData | 11 · nov/2026 | REST/MCP/CLI sobre dados públicos (CVM, BCB) |
| https://github.com/lobobruno/brFinance · https://github.com/royopa/anbima_scraper | 17 · 16 | scraping CVM / ANBIMA |
| https://github.com/gtazevedo/debentures_dot_com (PyPI `debentures-dot-com`) · https://github.com/jvpigozzo/rbentures | 0 · 5 | clientes do SND (eventos, PU) |
| https://github.com/enzojunq/deb-spreads · https://github.com/LucasRizzoli/spread-analyzer | 2 · 1 | spreads do secundário ANBIMA (+ alertas Telegram) |
| https://github.com/dutrinha/ofertas-publicas-cvm · https://github.com/dwsoliv73/case-c2p-ser | 0 · 1 | novas ofertas pela "API" da CVM |
| https://github.com/ThePaulean/scraper-fundos-net · https://github.com/edineibauer/rap-fnet-docs | 0 · 0 | espelho de documentos do Fundos.NET |
| https://github.com/mai0li/docvments · https://github.com/araujovito/radar-cvm · https://github.com/jackrj090603-prog/fatos-relevantes-cvm | — | scrapers/agentes sobre rad.cvm.gov.br |
| Guia: https://www.partnr.ai/blog/dados-da-cvm-como-acessar | — | portal, Python, API e MCP para dados da CVM |

### Fontes de dados (links)
- CVM ofertas: https://dados.cvm.gov.br/dataset/oferta-distrib (zip https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip) · IPE: https://dados.cvm.gov.br/dataset/cia_aberta-doc-ipe · RAD: https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx · SRE: https://web.cvm.gov.br/sre-publico-cvm/ · Plano de Dados Abertos 2026-28 (API prevista): https://legismap.com.br/conteudos/artigos-e-noticias/cvm-publica-plano-de-dados-abertos-2026-2028
- B3 autorização RCVM 160 (XLSX): https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/declaracao-de-autorizacao-para-distribuicao-balcao/ · boletim diário balcão: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/boletim-diario/dados-publicos-de-produtos-listados-e-de-balcao/ · UP2DATA (pago): https://arquivos.b3.com.br/
- ANBIMA Data: https://data.anbima.com.br/ · SND: https://www.debentures.com.br/informacoesaomercado/registronacvm.asp · agenda: https://www.debentures.com.br/exploreosnd/consultaadados/eventosfinanceiros/agenda_r.asp · secundário: https://www.anbima.com.br/informacoes/merc-sec-debentures/ · ANBIMA Feed: https://developers.anbima.com.br/ · ANBIMA Input (documentos de AGD pelos fiduciários): https://www.anbima.com.br/pt_br/noticias/agentes-fiduciarios-agora-podem-enviar-documentos-das-ofertas-de-debentures-por-meio-de-sistema-online-2CA08A9A6B00F5CD016B1EDEF4E70F59.htm
- Trustees: https://www.vortx.com.br/investidor/eventos · https://www.oliveiratrust.com.br/investidor/documentos?documento=Assembleias · https://www.pentagonotrustee.com.br/Site/ · caso Light (convocações só nos sites dos fiduciários): https://www.infomoney.com.br/?p=2168680 e https://capitalaberto.com.br/empresas/2024/04/vortx-debenturistas-da-light-votam-em-assembleia-por-whats
- Publicidade legal: Valor RI https://valor.globo.com/valor-ri/ · Diário Comercial https://www.diariocomercial.com.br/publicidade-legal · Gazeta SP https://publicidadelegal.gazetasp.com.br/ · cartilha ANJ (Lei 13.818/19) https://www.anj.org.br/wp-content/uploads/2024/01/2024-Publicidade-Legal-S.As-edicao-jan24.pdf
- Feeds de mercado testados: NeoFeed, InfoMoney, Money Times, Suno, Exame Invest, E-Investidor, Bloomberg Línea, Seu Dinheiro, Monitor Mercantil (URLs em `config/sources.yaml → extra_news`); CVM notícias RSS https://www.gov.br/cvm/pt-br/assuntos/noticias/RSS; agregadores https://atlaspublico.com.br/cvm/noticias e https://www.dadosdemercado.com.br/fatos-relevantes

### Desenho do score
- S&P CreditCompanion para originadores de DCM (fev/2026): https://www.spglobal.com/market-intelligence/en/news-insights/research/2026/02/enhancing-deal-execution-and-credit-positioning-for-dcm-originators-with-creditcompanion
- Crisil, "repayment wall" 2026–2029: https://integraliq.crisil.com/en/homepage/what-we-think/all-our-thinking/blog/2026/05/scaling-the-repayment-wall-in-private-credit.html
- Latham & Watkins Q&A (abr/2026), ~2 anos até o vencimento: https://www.lw.com/en/practices/admin/upload/SiteAttachments/Latham-QA-April-2026.pdf
- Refinanciamento proativo 12–18 meses antes: https://ibinterviewquestions.com/guides/debt-capital-markets/refinancing-waves-and-maturity-wall-management
- Detecção de eventos em notícias: SPEED (Hogenboom et al.) https://personal.eur.nl/frasincar/papers/DIR2012a/dir2012a.pdf · event-driven trading https://arxiv.org/pdf/2105.12825.pdf
