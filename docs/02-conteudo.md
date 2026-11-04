# 02 · Conteúdo dos entregáveis

Tudo que chega no WhatsApp todo dia útil, por volta das 06:45 (horário de Brasília), em **uma única conversa** (o seu próprio número ou um grupo só seu):

| # | Entregável | Formato | Tamanho alvo |
|---|-----------|---------|--------------|
| 1 | **Briefing do Dia** | PDF visual (cards, não lista) | formato celular (420×760 pt, corpo 14 pt), ~8 telas; variante A4 em 2 colunas por configuração |
| 2 | **Áudio · Mercado & Empresas** | Nota de voz (OGG/Opus) | 3 a 4 min |
| 3 | **Áudio · Economia** | Nota de voz (OGG/Opus) | 2 a 3 min |
| 4 | **Áudio · Política** | Nota de voz (OGG/Opus) | 2 a 3 min |
| 5 | **Termômetro DCM** | PDF | formato celular, ~4 telas |
| 0 | Mensagem de texto de abertura | Texto | 5 linhas: manchete do dia + 3 bullets + "leia hoje" |

A mensagem de texto (item 0) existe porque é o que se lê na tela de bloqueio. Os anexos vêm logo depois.

---

## 1. Briefing do Dia (PDF)

Princípio: **panorama em 30 segundos na página 1; profundidade nas seguintes.** Nada de lista corrida de manchetes. Cada notícia é um card com o mesmo esqueleto, para o olho bater sempre no mesmo lugar.

Formato: página do tamanho de uma tela de celular (420×760 pt), uma coluna, corpo 14 pt. Motivo: o WhatsApp mostra a página 1 como miniatura e abre o PDF ajustado à largura da tela; em A4 o texto vira ~7 px. A "página 1" abaixo é, portanto, a primeira tela; as seções seguintes fluem. `settings.pdf.page_size: A4` gera a versão de 2 colunas para ler no computador.

### Página 1 · Panorama
- Cabeçalho: data por extenso, número da edição, fontes consultadas (ícones), quantidade de artigos processados.
- **A frase do dia**: uma linha que resume o clima (ex.: "Dia de Copom com mercado dividido e Valor destacando pressão fiscal").
- **Manchete do dia**: 1 card grande (título, 3 linhas de resumo, por que importa, fonte, link).
- **Em 30 segundos**: 5 bullets curtos, um por tema (Mercado, Economia, Política, Internacional, DCM), cada um com um ícone de direção (▲ positivo / ▼ negativo / ● neutro para o mercado local).
- **Leia hoje** (bloco destacado): 3 a 5 recomendações de leitura, cada uma com: título, veículo, tempo estimado de leitura, e **uma frase dizendo por que você, especificamente, deve ler** (perfil: mercado financeiro, DCM, foco Brasil). Ver critério na seção "Ranking".

### Página 2 · Mercado & Empresas (Brasil)
Grade de cards (2 colunas). Cada card:
- Título reescrito (curto, factual).
- Resumo em até 3 linhas.
- **"Por que importa"** em 1 linha (o valor agregado do LLM; nunca repetir o resumo).
- Tags: setor, empresa(s), impacto (alto/médio/baixo), tipo (resultado, M&A, captação, regulatório, operacional).
- Fonte + link.
Ordem: por relevância, não por veículo. Preferência Valor > Brazil Journal quando a mesma história aparece nos dois (manter link para ambos).

### Página 3 · Economia (Brasil) + Política
- Economia: cards de atividade, inflação, juros, fiscal, câmbio, dados divulgados ontem/hoje.
- Política: cards do que mexe com mercado (Congresso, Executivo, STF, eleições, reformas). Filtro explícito: política **com efeito econômico/regulatório**; o resto fica fora.
- **Agenda do dia** (rodapé): indicadores, decisões de política monetária, leilões do Tesouro, balanços relevantes. (Fase 2: puxar da agenda do Valor / calendário econômico.)

### Página 4 · Internacional (FT, NYT, WSJ)
- 4 a 6 cards, selecionados pelo critério "**o que daqui afeta o Brasil ou o crédito global**": Fed, Treasuries, China/commodities, geopolítica com impacto em preço, bancos globais, crédito privado lá fora.
- Cada card diz explicitamente a ponte: "Impacto para o Brasil: …" em 1 linha.

### Página 5 · Painel de contexto (opcional, fase 2)
- Quadro de mercado de ontem: Ibovespa, dólar, DI jan/27 e jan/29, NTN-B 2035, S&P 500, Treasury 10y, petróleo, minério. Fonte gratuita (ex.: B3/BCB/yfinance). Serve para o áudio e o LLM contextualizarem.
- Legenda e metodologia (curta): como as notícias foram ranqueadas, link para o repositório.

### Regras editoriais do PDF
- Português do Brasil, registro de jornal econômico (não coloquial, não burocrático).
- Nunca inventar número: todo valor citado precisa estar no texto-fonte. O LLM recebe o texto e a instrução de citar só o que está nele.
- Título do card ≤ 70 caracteres; resumo ≤ 280 caracteres; "por que importa" ≤ 160 caracteres.
- Links sempre para o artigo original (o PDF é um índice, não um substituto do jornal).
- Fonte visível em todo card (respeito à assinatura e ao direito autoral; uso pessoal).

---

## 2. Áudios (3 notas de voz)

Roteiro gerado pelo LLM a partir do **mesmo JSON do PDF** (consistência total entre o que se lê e o que se ouve). Estrutura fixa de cada áudio:

1. **Abertura** (1 frase): "Bom dia. Briefing de Mercado e Empresas de terça-feira, 4 de novembro."
2. **Manchete do bloco** (2 a 3 frases).
3. **4 a 6 notícias** em ordem de relevância, cada uma com 2 a 4 frases e uma transição natural ("Ainda em bancos…", "No setor elétrico…").
4. **Fechamento** (1 a 2 frases): "O que observar hoje: …".

| Áudio | Escopo | Duração | Palavras |
|-------|--------|---------|----------|
| Mercado & Empresas | Bolsa, câmbio, juros de mercado, resultados, M&A, captações, setores, **mais o bloco internacional que afeta preços** | 3–4 min | 450–600 |
| Economia | Atividade, inflação, Selic/Copom, fiscal, dados macro BR, Fed/BCE quando relevante | 2–3 min | 300–450 |
| Política | Congresso, Executivo, STF, reformas, eleições, regulação; sempre com a ponte "efeito para mercado" | 2–3 min | 300–450 |

Regras do roteiro de áudio:
- Escrito **para ser ouvido**: frases curtas, números por extenso quando ambíguos ("dois vírgula cinco por cento", não "2,5%"), siglas explicadas na primeira vez (exceto as óbvias: Selic, Copom, Ibovespa, PIB).
- Sem markdown, sem bullets, sem URLs. Nomes de veículos citados ("segundo o Valor").
- Velocidade de fala ~150 palavras/min (base para o cálculo de duração).
- Enviado como **nota de voz (PTT)**, para tocar com um toque e permitir 1,5x/2x no WhatsApp.

---

## 3. Termômetro DCM (PDF)

Objetivo: transformar notícia e aviso legal em **sinal de originação**. Três tipos de oportunidade, conforme pedido: **nova emissão**, **refinanciamento**, **consent/waiver**. Mais dois tipos auxiliares que antecedem os três primeiros: **gatilho de funding** (M&A, capex, leilão, concessão) e **evento de crédito** (rating, covenant, RJ/RE).

### Página 1 · Termômetro do dia
- **Temperatura geral** (0–100, cinco bandas: frio <20 · morno · aquecendo ≥40 · quente ≥60 · fervendo ≥80) e uma frase de justificativa. Calculada em código a partir dos scores dos sinais do dia (fórmula em `docs/05-termometro-dcm.md`).
- **Top 5 sinais do dia** em cards:
  - Empresa · Setor · Grupo econômico
  - Tipo de oportunidade (nova emissão / refi / consent / gatilho / evento de crédito)
  - **Score 0–100** com banda (e 🔥 1–5 para bater o olho), tipo de fonte e confiança (alta/média/baixa)
  - **Evidência**: trecho literal da fonte (1 a 2 linhas) com link
  - **Leitura**: 1 frase de interpretação ("capex de R$ 4 bi anunciado sem funding definido → provável debênture incentivada")
  - **Próximo passo sugerido**: 1 linha acionável ("checar vencimentos 2026 no SND", "ligar para RI antes da AGD de 20/11")
- **Avisos e editais do dia** (tabela compacta): AGDs convocadas, anúncios de início/encerramento de oferta, fatos relevantes sobre dívida. Fonte: Valor (publicações legais), CVM, B3, agentes fiduciários.

### Página 2 · Radar da semana
- Sinais ainda "abertos" dos últimos 7 dias (status: novo / em acompanhamento / concluído / descartado), para não perder o fio.
- Linha do tempo de eventos futuros detectados (AGDs, vencimentos citados, datas de liquidação).
- Contexto de crédito: Selic/DI, notícias de fluxo (captação líquida de fundos de crédito, spreads), notícias regulatórias (CVM, CMN, tributação de incentivadas).

### Página 3 · Metodologia e fontes (fixa)
- Taxonomia de sinais e palavras-chave (resumo da `config/dcm_signals.yaml`).
- Aviso: ferramenta de triagem; toda oportunidade precisa de validação humana.

---

## Ranking: como escolher "as principais notícias" e "o que ler"

Entram ~200–400 artigos/dia; saem ~25 cards. Critérios combinados (detalhe em `docs/03-arquitetura.md`):

1. **Proeminência na fonte**: posição na capa / edição impressa do Valor, feed de "destaques" do Brazil Journal, FirstFT, NYT Top Stories, WSJ "What's News".
2. **Cobertura cruzada**: a mesma história em 2+ veículos sobe.
3. **Relevância para o perfil** (pontuação pelo LLM com o perfil explícito): mercado financeiro brasileiro, crédito/DCM, empresas emissoras, juros, fiscal, regulação de mercado de capitais.
4. **Novidade**: dedup contra os últimos 3 dias (não repetir o que já foi enviado, a menos que haja desdobramento).
5. **"Leia hoje"** = alto valor de leitura integral: análises, entrevistas, reportagens longas (não notas curtas), onde o resumo não substitui o texto.

O perfil do leitor fica em `config/settings.yaml` (`reader_profile`) e é injetado no prompt. Ajustar lá muda o ranking sem mexer em código.
