# Contexto da análise

## Objetivo
- **Pergunta de negócio:** o público de cinema no Brasil voltou ao nível de antes da pandemia? O que explica a distância que ainda falta?
- **Perguntas secundárias:** (1) dependência de poucos sucessos; (2) participação do filme brasileiro; (3) oferta × demanda (salas, sessões, público por sessão); (4) geografia da recuperação; (5) quem ganhou e quem perdeu espaço (distribuidoras e grupos exibidores); (6) ciclo de vida do filme em cartaz; (7) quando o público vai ao cinema; (8) dublado × legendado.
- **Quem lê o resultado:** gestores do setor audiovisual (exibição, distribuição, política pública) e, como portfólio, recrutadores da área de dados.
- **Decisão que a análise apoia:** onde concentrar esforço para recuperar público (programação, praças, tipo de filme, horários).

## Dados

### dados/bilheteria_limpa.csv.gz
- **O que é:** bilheteria diária da ANCINE, nas fontes *distribuidor* (dia × sala × obra × distribuidora) e *exibidora* (por sessão). É o resultado da limpeza em `dados/limpeza_bilheteria_unificada.ipynb`.
- **Período:** distribuidor de 01/01/2014 a 30/09/2026; exibidora de 01/06/2014 a 18/10/2026, com cobertura nacional só a partir de 2017.
- **Linhas:** 60.056.739, sendo 21.655.622 da fonte distribuidor e 38.401.117 da exibidora.
- **Como ler:** CSV UTF-8, `sep=","`, compactado em gzip. Para a análise, ele é convertido em `saidas/bilheteria_limpa.parquet`, com datas em ISO e `publico` inteiro.
- **Dicionário de colunas:** `docs/DICIONARIO_DADOS.md`.

## Decisões de tratamento
- 2026-10-23: as duas fontes **nunca são somadas**, porque descrevem as mesmas exibições.
- 2026-10-23: a fonte distribuidor é usada para séries longas (2014+) e **sem co-distribuição**. A mesma exibição (dia + sala + nome da sala + obra) informada por várias distribuidoras conta uma vez, com o maior público informado, como no dashboard.
- 2026-10-23: a fonte exibidora é usada para análises por sessão (horário, áudio, sessões vazias), só de 2017 em diante.
- 2026-10-23: 2026 vai só até setembro/outubro. Comparações com 2026 usam os mesmos meses (janeiro a setembro) em todos os anos.
- 2026-10-23: as análises de filmes usam só obras com CPB/ROE (prefixo B = brasileira, E = estrangeira). O prefixo G (eventos, mostras e shows) fica de fora.
- 2026-10-23: as linhas mantidas com dúvida na limpeza (`dados/bilheteria_limpeza_duvidas.csv`, 1.466 linhas) continuam na análise. O efeito delas nos totais é desprezível.

## Histórico
- 2026-10-23 — `analise.ipynb`: o público não voltou. 2025 teve 65% do público de 2019, e janeiro a setembro de 2026 chegou a 77%. A oferta voltou (salas e sessões iguais às de 2019); o que caiu foi o público por sessão (−34%). Cerca de dois terços da distância vêm dos 10 maiores filmes do ano.
