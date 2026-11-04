# 01 · Visão geral

## O problema
Acompanhar Valor, Brazil Journal, FT, NYT e WSJ todo dia consome 1 a 2 horas e ainda assim escapa coisa. Para quem trabalha com DCM no Brasil, o custo não é só tempo: é perder o aviso de AGD, o capex anunciado sem funding, o rating rebaixado que vira pedido de waiver.

## O que o sistema faz
Todo dia útil, antes das 7h, chega no seu WhatsApp:

1. **Mensagem de texto** com a manchete, 3 bullets e "leia hoje" (para a tela de bloqueio).
2. **Briefing do Dia (PDF)** visual, em cards, com panorama de 30 segundos, seções Mercado & Empresas / Economia / Política / Internacional e recomendações de leitura justificadas para o seu perfil.
3. **3 notas de voz** (Mercado & Empresas · Economia · Política), 2 a 4 min cada, roteiro derivado do mesmo conteúdo do PDF.
4. **Termômetro DCM (PDF)** com temperatura do dia, sinais de nova emissão / refinanciamento / consent-waiver, avisos e editais, radar da semana.

Detalhe de cada entregável: [02-conteudo.md](02-conteudo.md).

## Como funciona (em uma linha por etapa)

```
06:30  coleta     RSS + API + newsletters por e-mail + páginas logadas (sua assinatura)   → ~300 artigos
06:38  curadoria  dedup, cluster entre veículos, ranking (proeminência · cobertura · perfil) → ~40 histórias
06:40  síntese    Claude com saída estruturada → Briefing JSON, 3 roteiros, Termômetro JSON
06:43  render     HTML/CSS → PDF (WeasyPrint) · TTS → OGG/Opus (nota de voz)
06:45  entrega    WhatsApp (Evolution API self-hosted; Cloud API ou Telegram como alternativas)
```

Arquitetura, stack e decisões: [03-arquitetura.md](03-arquitetura.md). Fontes e como acessá-las: [04-fontes.md](04-fontes.md). Termômetro: [05-termometro-dcm.md](05-termometro-dcm.md). Referências de projetos existentes: [06-referencias.md](06-referencias.md). Plano de execução: [07-roadmap.md](07-roadmap.md).

## Princípios de projeto
- **Panorama, não lista.** O PDF é desenhado para bater o olho; o áudio para ouvir no trajeto; o texto para a tela de bloqueio.
- **Fiel à fonte.** Nenhum número sem origem; link em todo card; a assinatura é sua e o uso é pessoal (resumo + link, não redistribuição de texto integral).
- **Brasil primeiro.** Internacional entra com ponte explícita para o mercado local.
- **Barato de rodar.** Modelo pequeno para triagem em massa, modelo grande só para a síntese final; prompts estáveis cacheados; meta de custo < US$ 1/dia de LLM.
- **Robusto a falha de fonte.** Uma fonte fora do ar não derruba o briefing; cada etapa grava seu resultado e pode ser retomada.
- **Configuração, não código.** Perfil do leitor, pesos de ranking, feeds e taxonomia DCM ficam em `config/*.yaml`.
