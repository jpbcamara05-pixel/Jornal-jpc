# 04 · Fontes e acesso

Verificado em 4/11/2026 (HTTP 200 + parse de cada feed). URLs completas em `config/sources.yaml`.

## Resumo por veículo

| Veículo | RSS verificado | O que o feed traz | Paywall / anti-bot | "Capa" / edição do dia | Newsletter | Melhor acesso |
|---|---|---|---|---|---|---|
| **Valor Econômico** | `pox.globo.com/rss/valor/` (capa) + por editoria: empresas, finanças, brasil, política, mundo, legislação, agronegócios, carreira, opinião; mais `rss/pipelinevalor/`, `rss/valorinveste/`, `rss/valorinternational/`. (`valor.globo.com/rss/` → 404.) | 100 itens/feed. `<description>` traz o **texto integral nos artigos abertos** (≈ 50% na capa; Pipeline 93%; Valor International 100%, em inglês) e só o subtítulo nos exclusivos. | Paywall medido; HTML anônimo dos pagos vem **sem corpo**. **Sem DataDome/Cloudflare** (só reCAPTCHA em formulários). `robots.txt` bloqueia crawlers de IA. | **`valor.globo.com/impresso/AAAAMMDD/`**: página pública, server-rendered, com as ~70 matérias da edição impressa por editoria (+ itens de capa em `/impresso/noticia/`). É a fonte da `prominence`. Réplica em PDF (assinante): `valor.com.br/virador`. | Cardápio em `/newsletter/cardapio/`. Chaves: `ValorManha` = "Edição de hoje" (diária), `ValorPolitica` = "Política Hoje", `ValorTarde` = "As mais lidas". **Prévia pública**: `/newsletter/preview/?newsletter=ValorManha`. | RSS (metade já integral) + manifesto do impresso + navegador logado (Conta Globo, cookie `GLBID`) para os exclusivos. |
| **Brazil Journal** | `braziljournal.com/feed` | 15 itens, `content:encoded` = **artigo completo** (mediana 4,1k chars). | Sem paywall, sem anti-bot. ToS proíbe scraping sem consentimento (uso pessoal, volume mínimo). | — (digital) | Newsletter diária gratuita em `/newsletter` (não existe "Morning Call"). | RSS basta. |
| **Financial Times** | `ft.com/rss/home/international`; qualquer seção/tópico + `?format=rss`: markets, companies, world, **brazil**, latin-america, global-economy, emerging-markets, lex, unhedged. | Título + linha fina. Sem corpo. | Paywall rígido + **Cloudflare bot management**. API (developer.ft.com) só B2B. | Feed da home = escolha dos editores. | **FirstFT** (diária, 06:00). | RSS + FirstFT por IMAP; navegador logado tolera perfil persistente de baixo volume. |
| **New York Times** | `rss.nytimes.com/services/xml/rss/nyt/{HomePage,Business,Economy,World,Politics,DealBook}.xml` | 15–50 itens, resumo (~145 chars) + tags. | Paywall medido + **DataDome**. ToS: uso pessoal, não comercial. | HomePage.xml ≈ capa. | **The Morning** (diária), DealBook. | RSS + **NYT Developer API** (chave grátis; Top Stories/Article Search; ~500 req/dia, 5/min; só abstracts) + The Morning por IMAP. Corpo integral via navegador = frágil. |
| **Wall Street Journal** | `feeds.content.dowjones.io/public/rss/{RSSWorldNews, RSSMarketsMain, WSJcomUSBusiness, socialeconomyfeed, socialpoliticsfeed, RSSOpinion}` | Resumo (~120 chars) + imagem. | Paywall rígido + **DataDome** (CloudFront). Sem API para pessoa física (Factiva = contrato). | World/Markets ≈ seções de capa. | **The 10-Point** (diária). | RSS + 10-Point por IMAP. O mais frágil dos cinco para texto integral. |

## Acesso com a sua assinatura

- **Conta Globo (Valor)**: login OIDC; o cookie que vale é `GLBID` em `.globo.com`. Padrão: `python -m briefing login valor` abre um Chromium com **perfil persistente dedicado** (`browser_profile/`), você loga uma vez, e a coleta reutiliza. Sem anti-bot, ~60–70 páginas/dia no ritmo humano é tranquilo. Sessão expirada é detectada (corpo vazio em >70% das páginas) e vira aviso.
- **FT**: mesmo esquema; Cloudflare tolera perfil logado de baixo volume em IP residencial.
- **NYT/WSJ**: DataDome identifica headless + IP de datacenter rapidamente. Preferir API (NYT) + newsletters. Se quiser corpo: perfil headful, IP de casa, ≤ 20 páginas/dia, aceitar falhas. **Nunca** comprar resolvedor de captcha.
- **Newsletters por IMAP**: assinar com o e-mail do `IMAP_USER` (Gmail com senha de app). São a curadoria do editor e chegam antes de 06:30.
- **Onde rodar**: IP residencial (Mac/Raspberry) é o único cenário em que Valor logado funciona de forma confiável. GitHub Actions usa IPs de datacenter da Azure, bloqueados por Cloudflare/DataDome; se quiser Actions, só a parte RSS/API, ou saída via exit node Tailscale em casa.

## Termos de uso (resumo honesto)

Uso pessoal, uma assinatura própria, volume mínimo, **sem redistribuir** o texto (o PDF traz resumo + link, fonte em todo card). Mesmo assim, NYT/FT/WSJ proíbem acesso automatizado fora das APIs, e o Valor bloqueia crawlers de IA no `robots.txt`. Postura de menor risco: newsletters + RSS + API onde bastam; navegador logado só no Valor (e FT, com parcimônia); nada de contornar desafios anti-bot.

## Ferramentas de extração

| Ferramenta | Stars | Uso |
|---|---|---|
| trafilatura | 7,1k | extrator principal (melhor F1 em benchmark 2026) |
| newspaper4k | 1,2k | metadados (autores, datas) |
| RSSHub | 46,8k | rotas `/ft/myft/:key`, `/nytimes/en`, `/wsj/en-us/:category`; **não tem rota para Globo/Valor/Brazil Journal** |
| browser_cookie3 | 1,1k | exportar cookies do Chrome (alternativa ao perfil Playwright) |
| pynytimes | 63 | wrapper da API do NYT |

## Projetos que consomem estas fontes
`vmesel/valor_alert` (scraper antigo do Valor, 2018), `jailsondamaceno/globo-rss-bigdata-pipeline`, ~10 repos consumindo `pox.globo.com/rss/valor` (`leoheim/invest-agent`, `jeronimo-mg/notifyinvest`, `efpv/news-intelligence-hub`), `Elyanouti/ft-daily-scraper-ppt` (FT diário + resumos LLM, o análogo mais próximo), `gustavo-candidoo/raspagens` (Brazil Journal), `TobySuch/earlybird` e `iloveitaly/gmail-digest` (newsletter → digest por LLM).

## Estratégia de ingestão (ordem de esforço → confiabilidade)

1. **Backbone RSS** (horas, sem login): 12 feeds do Valor + Brazil Journal + FT/NYT/WSJ. Já dá texto integral para metade do Valor e 100% de Pipeline/Valor International/Brazil Journal.
2. **Manifesto do impresso + newsletters** (1 dia): `/impresso/AAAAMMDD/` como conjunto autoritativo das "principais" do Valor; newsletters por IMAP como proeminência extra.
3. **Corpo dos exclusivos do Valor** (1–2 dias): Playwright com perfil logado, só para os itens do impresso cujo RSS veio curto.
4. **Corpo do FT** (2–3 dias, moderado).
5. **NYT/WSJ** (frágil): API + newsletters; corpo só se sobrar paciência.
6. **DCM diário** (1 dia, confiável): CSVs da CVM (ofertas RCVM 160, IPE) + página de ofertas da B3 — ver [05-termometro-dcm.md](05-termometro-dcm.md).

## Aprendizados da primeira coleta real (4/11/2026)

- **Valor, feed `capa`** = home do site (~100 itens), não a capa do impresso. Quase metade dos itens já traz o texto integral na `<description>` (matérias abertas). A editoria dessas matérias vem da URL (`valor.globo.com/<editoria>/…`), não do feed.
- **Manifesto `/impresso/AAAAMMDD/`** agrupa as matérias por caderno em `<h2>` ("Primeira página", "Brasil", "Política", "Internacional", "Opinião", "Empresas", "Agronegócios", "Finanças", "Legislação & Tributos"): o coletor usa o cabeçalho anterior ao link como editoria. Os 6–9 itens de "Primeira página" apontam para `/impresso/noticia/…` (teasers) e recebem prominence 1.0.
- **Ruído filtrado no Valor**: `/patrocinado/` (conteúdo pago), `/ao-vivo/` (blog com URL antiga e título reciclado), "Cartas de Leitores", "Correção", "Frase do dia".
- **FT** entrega links com `?syn-…` de rastreio; **feedparser** devolve `*_parsed` em UTC — usar `calendar.timegm`, não `time.mktime` (dava +3 h e datas "de amanhã").
- **Brazil Journal** publica ~10 itens/dia no feed, sem editoria ("geral"); o modelo classifica.
- **Sem o LLM de relevância** (Haiku) o ranking vira proeminência pura e o Valor ocupa tudo; por isso `curation.min_per_source: 8` garante um piso de FT/WSJ/NYT/BJ no material enviado ao modelo principal.
