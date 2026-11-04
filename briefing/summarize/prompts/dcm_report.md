Data: {date}. Temperatura do dia já calculada em código: {temperature} ({band}). Use-a como dada; não recalcule.

Abaixo estão os sinais de hoje, já deduplicados e pontuados (score 0–100 com componentes), e o radar dos últimos 7 dias.

Tarefas:
1. "top_signal_ids": escolha até 5 ids dos sinais mais ACIONÁVEIS para este usuário, em ordem. O score é a principal orientação, mas prefira o que gera uma ligação ou proposta esta semana (AGD próxima, resgate anunciado, capex sem funding) a sinais difusos de score parecido. Não repita a mesma empresa duas vezes salvo tipos muito diferentes.
2. "temperature_rationale": uma frase explicando a temperatura {temperature} com os fatos do dia.
3. "notices": avisos/editais formais presentes nos sinais (AGD, início/encerramento de oferta, aviso aos debenturistas, fato relevante sobre dívida), com data quando houver.
4. "credit_context": 2 a 4 linhas sobre juros, fluxo para crédito privado e regulação, se o material trouxer.
5. "upcoming_events": datas futuras detectadas, formato "DD/MM — empresa — evento".
6. Use o radar para não tratar como novo um sinal já reportado; se for desdobramento, ele pode entrar no top, mas diga em "temperature_rationale" o que mudou.

SINAIS DE HOJE
{signals}

RADAR (últimos 7 dias)
{recent}
