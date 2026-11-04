# 05 · Termômetro DCM

Objetivo: converter notícia e aviso legal em **sinal de originação** com evidência literal, interpretação separada e confiança calibrada. Layout do PDF em [02-conteudo.md](02-conteudo.md#3-termômetro-dcm-pdf).

## Taxonomia de sinais (config/dcm_signals.yaml)

Seis famílias, cada uma com subtipos e palavras-chave **validadas contra o campo "Assunto" dos documentos IPE/CVM de 2026** (frequências entre parênteses):

| Família | Subtipos (base do score) | Termos que aparecem de fato nos documentos |
|---|---|---|
| **A · nova_emissao** | rca_aprova_emissao (25) · oferta_em_curso (15) · captacao_anunciada (25) · encerramento_oferta (5) | "emissão de debêntures" (54 FR / 104 CM), "oferta pública" (72 FR), "bookbuilding" (23), escrituras e aditamentos (398), termo de emissão de NC (27) |
| **B · refinanciamento** | resgate_antecipado (30) · alongamento_rolagem (30) · muro_vencimentos (30) · pressao_liquidez (25) | "resgate antecipado facultativo" (82 avisos aos debenturistas), "recompra" (75 FR), "amortização extraordinária" (11), "alteração do prazo e data de vencimento", `Destinacao_recursos` com "refinanciamento/reembolso" |
| **C · consent_waiver** | agd_convocada (35) · waiver_covenant (35) · deterioracao (30) · reestruturacao_formal (30) | editais AGDEB (276), "waiver" (24 CM), "repactuação" (5), "aditamento" (11), "sustação dos efeitos do vencimento antecipado", RE (33 FR) / RJ (23 FR) |
| **D · gatilho_funding** | aquisicao_mna (25) · capex_projeto (25) · evento_societario (15) | "aquisição" (120 FR), "alienação" (54), "leilão" (33 FR), "concessão" (19), "investimento" (44) |
| **E · evento_credito** | rebaixamento_rating (20) · elevacao_rating (15) · rating_afirmado (5) · alavancagem_inadimplencia (20) | "rating" (14 FR / 106 CM), Fitch (36), Moody's (20) |
| **F · macro_regulatorio** | fluxo_spread (10) · regulacao (10) · juros (5) | crédito privado, spread, captação líquida, RCVM 160, Lei 14.801 |

**Ruído excluído** (159 dos 325 avisos aos debenturistas são só "pagamento de juros"): pagamento de juros/remuneração, posição consolidada, relatório de proventos, mapa de votação, manual de participação, relatório anual do agente fiduciário, calendário de eventos.

Três camadas: (1) palavras-chave selecionam candidatos (custo zero, alto recall); (2) o modelo pequeno classifica em família/subtipo e extrai valor, data, tipo de fonte, partes e **evidência literal**; (3) **o código pontua** (`briefing/summarize/dcm_score.py`), deduplica e calcula a temperatura. O modelo principal só escolhe o top 5, escreve a justificativa, lista avisos e eventos.

## Score de cada sinal (0–100) — calculado em código

```
score = base(subtipo, 0–40)
      + urgência (data do evento):  AGD ≤7 dias 20 · 8–30 dias 12 · vencimento ≤6 meses 20 · 6–12 m 14 · 12–18 m 8
      + tamanho (R$):               ≥1 bi 15 · 300 mi–1 bi 10 · 100–300 mi 6 · <100 mi 2
      + confiança da fonte (0–15):  documento oficial 15 · trustee 13 · jornal legal 12 · Valor/Pipeline/BJ 10 · outra mídia 6 · rumor 4
                                    × confiança da extração (alta 1,0 · média 0,7 · baixa 0,4)
      + corroboração:               +5 por fonte independente extra (máx. 10)
      ± modificadores:              setor prioritário +5 · destinação "refinanciamento" +5 · 2ª convocação/reabertura +5 · macro −10
bandas: frio 0–19 (arquivar) · morno 20–39 (monitorar) · aquecendo 40–59 (preparar material)
        · quente 60–79 (contato esta semana) · fervendo 80–100 (contato hoje)
decaimento no radar: meia-vida de 7 dias úteis; eventos datados (AGD, vencimento) só decaem após a data
dedup: chave (empresa normalizada, família, subtipo); fontes extras viram corroboração
temperatura do dia = 0,6 × maior score + 0,4 × média dos 3 maiores
```

Exemplo (teste em `tests/test_dcm_score.py`): AGD com waiver em 5 dias, R$ 500 mi, edital no IPE, saneamento → 35 + 20 + 10 + 15 + 5 = **85, fervendo**. Rumor macro de juros → frio.

Revisão humana a partir de **40**. Os pesos ficam em `config/dcm_signals.yaml → scoring`; mudar lá não exige reprompt.

Referências do desenho: S&P CreditCompanion para originadores de DCM (screening de risco de refinanciamento e liability management, fev/2026), Crisil sobre "repayment wall" 2026–2029, Latham & Watkins (agir com ~2 anos até o vencimento), prática de refinanciamento proativo 12–18 meses antes; detecção de eventos em notícias (SPEED, Hogenboom et al.). Não existe score público de "deal signal" para DCM; o desenho é próprio, calibrado pelas frequências do IPE 2026. Links em [06-referencias.md](06-referencias.md#d-dcm).

## Campos de cada sinal (card)

empresa · setor · grupo · família/subtipo · instrumento · valor (R$) · data do evento · tipo de fonte · confiança · **evidência literal** · leitura (1 frase) · próximo passo · partes (coordenador, agente fiduciário, rating) · fonte/link · **score + componentes + banda** · corroborações · status. Modelos: `DCMSignalDraft` (o que o LLM extrai) e `DCMSignal` (pontuado) em `briefing/models.py`.

## Radar da semana

Sinais ficam no SQLite (`dcm_signals`) com status `novo / acompanhando / concluido / descartado` e score com decaimento. O prompt de consolidação recebe os últimos 7 dias para não reapresentar como novo o que já foi reportado e para montar a linha do tempo de eventos (AGDs, liquidações, vencimentos).

## Fontes estruturadas (verificadas em 4/11/2026)

**"Valor Legais" não existe mais como seção web.** Avisos legais do Valor só aparecem na réplica em PDF do impresso (`valor.com.br/virador`, assinante). A Lei 13.818/19 levou a publicidade legal para resumo no impresso + íntegra no site do jornal, e a RCVM 160 moveu avisos de oferta para sites do emissor/coordenador/B3/CVM. O que substitui:

| Fonte | URL | O que traz | Acesso / frequência |
|---|---|---|---|
| **CVM Dados Abertos · Ofertas** | `https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip` → `oferta_resolucao_160.csv` | Requerimentos de rito automático (RCVM 160) desde 2023: emissor, líder, coordenadores, valor, status, destinação, público-alvo; ~2.000 debêntures, ~1.900 CRI, ~600 CRA, ~800 notas comerciais | CSV em zip, **diário**, ODbL. Melhor feed de mercado primário |
| **CVM Dados Abertos · IPE** (documentos eventuais) | `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_AAAA.zip` | Categoria/Tipo/Espécie/Assunto/Link: **Fato Relevante**, Comunicado ao Mercado, **Aviso aos Debenturistas** (325 em 2026), **Assembleia · AGDEB · Edital de Convocação** (98), AGDEB Ata, Documentos de Oferta (Aviso ao Mercado etc.), Escrituras e aditamentos, Relatório de Agente Fiduciário | CSV; **atraso de alguns dias** na atualização. É o substituto estruturado dos "Legais" |
| RAD CVM consulta externa | `https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx` | Os mesmos documentos, em tempo real | UI ASP.NET (viewstate); raspável com esforço (`mai0li/docvments`) |
| **B3 · Publicação de Ofertas Públicas** | `.../ofertas-publicas/ofertas-em-andamento/empresas/publicacao-de-ofertas-publicas/` (+ `/ofertas-encerradas/`) | Tabela com PDFs: **Aviso ao Mercado, Anúncio de Início, Anúncio de Encerramento** (176 PDFs hoje) | HTML server-rendered, sem login |
| B3 · API de cias listadas | `sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetMaterialFacts/<base64>` | Fatos relevantes/comunicados de listadas | JSON não documentado, estável |
| B3 · Fundos.NET | `fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosDados?...` | Assembleias/ofertas de FIDC/FII/FIP | JSON público |
| B3 · renda fixa | Boletim Diário (capítulo Renda Fixa), série histórica | Negociação e estoque de debêntures | arquivos. "Central de Debêntures" não existe; não há página de AGDs na B3 |
| **ANBIMA** | `data.anbima.com.br` (SPA) · `debentures.com.br` (SND, **será descontinuado**) · `developers.anbima.com.br` (API Títulos Privados, paga) | Características, agenda de eventos, ofertas por coordenador | headless ou API paga |
| CVM 476 consulta | `web.cvm.gov.br/app/esforcosrestritos/#/consultarOferta` | Início/encerramento de ofertas restritas | app jQuery; o CSV acima cobre o mesmo |
| Notícias DCM | Pipeline Valor (`rss/pipelinevalor/`, 93% integral), Valor Investe renda fixa (`rss/valorinveste/`), Brazil Journal, Valor PRO (terminal pago) | camada de notícia; filtrar por debênture/CRI/CRA/emissão/waiver | RSS |

### Mais fontes confirmadas pela segunda pesquisa

| Fonte | URL | O que traz | Acesso |
|---|---|---|---|
| **RAD · `ListarDocumentos`** | `POST frmConsultaExternaCVM.aspx/ListarDocumentos` (JSON; campos separados por `$&`, linhas por `&*`) | Os documentos do IPE em **minutos** (841 docs em 2 dias; `palavraChave=debenturistas` → 51 docs, 44 AGDEB). Template: `danxhp/cvm-fatos-relevantes` | WebMethod não documentado; manter o CSV semanal como fallback |
| **B3 · Declaração de autorização RCVM 160 (Balcão)** | página "boletim-diario/declaracao-de-autorizacao-para-distribuicao-balcao" | XLSX (~1.940 linhas): emissor, CNPJ, instrumento (DEB/NC/CRI/CRA/FIDC/FII), nº emissão, série, **coordenador líder**, **data de liberação** | raspar a página e seguir o href (muda a cada upload) |
| **Valor RI** (sucessor do "Valor Legais") | `valor.globo.com/valor-ri/` → atas-e-comunicados · fatos-relevantes · mercado-de-capitais | editais de convocação e avisos de oferta (ex.: CRA Marfrig) | renderizado por JS (headless); RSS `rss/valor/valor-ri/` estagnado |
| **Vórtx · Assembleias e Eventos** (melhor fonte em tempo real de consents) | `vortx.com.br/investidor/eventos?page=N` | 22 mil eventos: tipo (Assembleia/Consulta Formal), ativo (DEB/CRI/NC), nome (AGD/AGT/edital/ata), prazo, **status Ativa/Iniciada/Finalizada**; materiais em `cdn.vortx.com.br` | HTML server-rendered paginado; implementado em `dcm_sources.py` |
| Oliveira Trust | `oliveiratrust.com.br/investidor/documentos?documento=Assembleias` | assembleias e documentos | API protegida por reCAPTCHA → headless |
| Pentágono | `pentagonotrustee.com.br/Site/` (POST Investidores por tipo de ativo) | emissões e documentos por ativo; sem seção de assembleias | sessão de navegador |
| Simplific Pavarini | `simplificpavarini.com.br` | fora do ar na pesquisa (504); pode ter migrado para a Vórtx | verificar |
| **Diário Comercial (SP)** | `diariocomercial.com.br/wp-content/uploads/AAAA/MM/dcedicaodigitalDDMMAAAA.pdf` | PDF diário de publicidade legal (editais de AGD da Raízen saíram aqui) | texto do PDF + regex "ASSEMBLEIA GERAL DE DEBENTURISTAS" |
| Gazeta SP · Jornal Empresas & Negócios · Diários Oficiais | ver `config/sources.yaml` | editais de AGD de SPEs | Cloudflare / PDFs |
| SND (debentures.com.br) | `registronacvm.asp` (diário) · `agenda_r.asp` (vencimentos, amortizações, repactuações) | muro de vencimentos | HTML; site será descontinuado → ANBIMA Data |
| CVM notícias | `gov.br/cvm/pt-br/assuntos/noticias/RSS` | ofertas e regulação | RSS |

Por que os agentes fiduciários importam: emissores registrados arquivam o edital de AGD no IPE, mas **os não registrados (SPEs, S.A. fechadas em ofertas 476/160 para profissionais, a maioria da infraestrutura) só convocam nos sites dos trustees e nos jornais legais**. A Justiça do RJ suspendeu AGDs da Light justamente porque os debenturistas "só tomaram conhecimento nos sites dos agentes fiduciários".

Implementado em `briefing/ingest/dcm_sources.py`: IPE (categorias acima, filtro de dívida em Fatos Relevantes), ofertas RCVM 160 (diff por data de requerimento), página de ofertas da B3, eventos ativos da Vórtx. Fase 3: RAD `ListarDocumentos` de hora em hora, XLSX da B3, Fundos.NET (FIDC/CRI/CRA), Valor RI e Oliveira Trust via headless, Diário Comercial (PDF), SND/ANBIMA Data para o muro de vencimentos.

### Cadência sugerida
- **06:00 diário**: CSV de ofertas CVM, XLSX B3, SND registros + agenda, Vórtx páginas 1–5, PDF do Diário Comercial, feeds.
- **de hora em hora** (fase 3): RAD `ListarDocumentos` e Fundos.NET para Fato Relevante, Comunicado, AGDEB, Aviso aos Debenturistas, Escrituras, Recuperação.
- **semanal**: `ipe_cia_aberta_AAAA.zip` para reconciliação/backfill; normalizar emissores por CNPJ (`cad_cia_aberta.csv`).

## Aprendizados da primeira coleta real (4/11/2026)

- **CVM IPE (CSV anual)** sai com **3–5 dias de atraso** (em 4/11 o arquivo ia até 30/10). Por isso o coletor usa janela própria (`dcm_ipe_lookback_days: 8`) e o SQLite deduplica por `signal_id` entre dias; o decaimento do score cuida do resto. Para "mesmo dia" é preciso o RAD (`ListarDocumentos`, fase 3).
- Em 8 dias o IPE rendeu 31 itens úteis depois dos filtros: "Assembleia" só entra se Tipo = AGDEB ou a pauta fala de emissão/dívida (senão são ~30 AGE/AGO por dia); Fato Relevante e Comunicado só com palavras de dívida; "Relatório de Agente Fiduciário" saiu da lista (relatórios anuais, ruído). "Escrituras e aditamentos de debêntures" entrou: escritura nova = emissão, aditamento = consent aprovado.
- Exemplos reais do período: Hospital Care Caledonia (4 AGDs de postergação de remuneração — consent/waiver em curso), Elfa (4ª suspensão de AGDEB), V.tal (AGE para emissão de valores mobiliários), Turbi (11ª e 12ª emissões de notas comerciais).
- `oferta_resolucao_160.csv` (5,7 MB) e `ipe_cia_aberta_2026.zip` (1,8 MB) ficam em `data/cache/` com cache diário.
- B3 "ofertas em andamento" trouxe 107 PDFs (aviso ao mercado / início / encerramento) e a Vórtx 40 assembleias ativas: são o grosso do volume; o filtro por palavra-chave + o Haiku é que separam oportunidade de rotina.
