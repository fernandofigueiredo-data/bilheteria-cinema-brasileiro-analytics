# Perfil dos dados de origem

Os números abaixo foram gerados por `pipeline/perfil.py` sobre a extração integral dos dois zips (detalhes por arquivo em `dados/perfil.json`) e completados com consultas DuckDB sobre o staging.

## Visão geral

| | Distribuidoras | Exibidoras |
|---|---|---|
| Zip | `bilheteria-diaria-obras-por-distribuidoras-csv.zip` (472 MB) | `bilheteria-diaria-obras-por-exibidoras-csv.zip` (1,15 GB) |
| Arquivos | 153 CSVs **mensais** (`…-AAAA-MM.csv`) | 660 CSVs **semanais** (`…-AAAA-MM-sNN.csv`) |
| Tamanho descompactado | 5,03 GB | 8,77 GB |
| Formato | separador `;`, cabeçalho, LF; aspas RFC 4180 só em 15.349 linhas cujos títulos contêm `"` (ex.: `""" A PRIMEIRA MISSA"""` = `" A PRIMEIRA MISSA"`) | idem (22.539 linhas com aspas) |
| Codificação | UTF-8 em todos os arquivos, sem BOM | UTF-8 em todos os arquivos, sem BOM |
| Cabeçalho | idêntico nos 153 arquivos (17 colunas) | idêntico nos 660 arquivos (18 colunas) |
| Linhas de dados | **21.655.622** (de 65 a 210.833 por arquivo) | **38.401.117** (de 3 a 98.219 por arquivo) |
| Período | 01/01/2014 a 30/09/2026 (4.633 dias) | 01/06/2014 a 18/10/2026 (4.027 dias) |
| Granularidade | **dia × obra × sala × distribuidora** (sem horário) | **sessão** (data e hora) × obra × sala |
| Público total | 1.695.424.906 | 1.232.956.821 |
| Linhas rejeitadas pelo parser | 0 | 0 |
| Duplicatas exatas (linha inteira) | 0 | 0 |

**Cobertura da fonte exibidora.** Ela é quase vazia até meados de 2016: 15 mil linhas em 2014 e 20 mil em 2015, contra cerca de 1,5 milhão por ano na fonte distribuidor. A partir de 2017, as duas fontes ficam com público anual muito próximo (diferença abaixo de 3%).

| Ano | Público (distribuidor) | Público (exibidora) |
|---|---:|---:|
| 2014 | 156.945.948 | 15.238 |
| 2015 | 169.242.519 | 20.492 |
| 2016 | 184.850.806 | 60.953.089 |
| 2017 | 181.808.330 | 177.746.991 |
| 2018 | 163.286.368 | 161.657.771 |
| 2019 | 179.262.678 | 174.499.298 |
| 2020 | 39.350.742 | 39.248.445 |
| 2021 | 53.024.171 | 50.946.204 |
| 2022 | 97.441.820 | 96.415.843 |
| 2023 | 117.024.349 | 116.073.663 |
| 2024 | 128.136.624 | 127.189.680 |
| 2025 | 115.456.938 | 114.261.456 |
| 2026 | 109.593.613 (até set.) | 113.928.651 (até 18/out.) |

## Colunas e tipos

Todas as colunas chegam como texto. O tipo é o inferido após validação de 100% das linhas. "Nulos" conta valores vazios.

| Coluna original | Tipo | Distribuidoras: nulos / distintos | Exibidoras: nulos / distintos |
|---|---|---|---|
| DATA_EXIBICAO | data `DD/MM/AAAA` (100% válida) | 0 / 4.633 | 0 / 4.027 |
| SESSAO | data e hora `DD/MM/AAAA HH:MM:SS` (100% válida) | — | 0 / ~875 mil |
| TITULO_ORIGINAL | texto (≤100) | 0 / ~6,1 mil | 14 / ~5,9 mil |
| TITULO_BRASIL | texto | 2.838.444 / ~3,4 mil | 5.406.179 / ~2,8 mil |
| CPB_ROE | código `[BE]` + 13 dígitos | 35 / ~7,6 mil | 0 / ~8,3 mil |
| AUDIO | `DUBLADO` / `ORIGINAL` | — | 0 / 2 |
| LEGENDADA | `SIM` / `NÃO` | — | 0 / 2 |
| PAIS_OBRA | texto | 6.296 / 77 | 218.045 / 84 |
| REGISTRO_SALA | código numérico (7 dígitos) | **568.397** / ~5,0 mil | 0 / ~4,7 mil |
| NOME_SALA | texto | 68 / ~11,9 mil | 0 / ~4,4 mil |
| PUBLICO | inteiro ≥ 0 (100% inteiros) | 0; mín. 0, máx. 16.000; 172.547 zeros | 0; mín. 0, máx. 1.242; 2.425.257 zeros |
| REGISTRO_GRUPO_EXIBIDOR | código numérico | 2.585.059 / 67 | 2.229.131 / 65 |
| REGISTRO_EXIBIDOR | código numérico | 568.397 / ~810 | 0 / ~470 |
| REGISTRO_COMPLEXO | código numérico | 568.397 / ~1,6 mil | 0 / ~1,1 mil |
| MUNICIPIO_SALA_COMPLEXO | texto | 521.800 / ~510 | 0 / ~460 |
| UF_SALA_COMPLEXO | sigla (27 UFs) | 521.800 / 27 | 0 / 27 |
| RAZAO_SOCIAL_DISTRIBUIDORA | texto | 0 / ~420 | — |
| CNPJ_DISTRIBUIDORA | CNPJ com máscara | 0 / ~445 | — |
| NR_PROTOCOLO_ENVIO | código numérico (14 dígitos) | 0 / ~9,0 mil | — |
| DATA_HORA_ENVIO_PROTOCOLO | data e hora `DD/MM/AAAA HH:MM:SS` | 2.311.855 / ~5,2 mil | — |
| RAZAO_SOCIAL_EXIBIDORA | texto | — | 0 / ~560 |
| CNPJ_EXIBIDORA | CNPJ com máscara | — | 0 / ~495 |

**Campos nas duas fontes (13):** data_exibicao, titulo_original, titulo_brasil, cpb_roe, pais_obra, registro_sala, nome_sala, publico, registro_grupo_exibidor, registro_exibidor, registro_complexo, municipio_sala_complexo, uf_sala_complexo.
**Só em distribuidoras (4):** razao_social_distribuidora, cnpj_distribuidora, nr_protocolo_envio, data_hora_envio_protocolo.
**Só em exibidoras (5):** sessao, audio, legendada, razao_social_exibidora, cnpj_exibidora.

## Problemas de qualidade encontrados
1. **Sala sem registro (distribuidoras).** 568.397 linhas não têm REGISTRO_SALA, exibidor nem complexo, e 521.800 delas também não têm município e UF. Os casos se concentram em 2014 (370 mil) e 2015 (85 mil). Nelas, só NOME_SALA identifica a sala, com grafias livres. Por isso há cerca de 11,9 mil nomes de sala para cerca de 5 mil registros.
2. **Co-distribuição (distribuidoras).** Há 28.024 exibições (dia + sala + obra) informadas por mais de uma distribuidora, num total de 56.048 linhas, sempre com o mesmo público. Somar o público dessa fonte conta essas exibições duas vezes.
3. **Chave repetida.** Em distribuidoras, (dia, sala, nome, obra, CNPJ) se repete em 96 linhas, por reenvio de protocolo. Em exibidoras, (sessão, sala, obra) se repete em 605 linhas. Não há chave natural garantida em nenhuma das fontes.
4. **CNPJ "PESSOA FÍSICA".** 1.057 linhas de distribuidoras trazem o texto `PESSOA FÍSICA` no lugar do CNPJ, com quatro razões sociais diferentes (pessoas físicas distribuidoras). O CNPJ não identifica a distribuidora nesses casos.
5. **CPB/ROE.** 35 linhas sem código (distribuidoras); 3 linhas com código de 12 dígitos (`B130174300000`); o código genérico `E1300000100000` aparece com vários títulos (THE HUNGER, APPLAUSE, RAGING BULL, GRBAVICA…), ou seja, é um coringa para obras antigas. No sentido inverso, 101 títulos originais aparecem com mais de um CPB (homônimos ou relançamentos).
6. **Títulos.** TITULO_BRASIL fica vazio quando o título nacional é igual ao original (13% e 14% das linhas). Os títulos estão em maiúsculas e com acentos, sem variações de grafia para o mesmo CPB, exceto o coringa acima.
7. **Sessões após a meia-noite.** Em 8.829 sessões da fonte exibidora, a data da SESSAO é o dia seguinte à DATA_EXIBICAO (por exemplo, exibição 01/07/2016, sessão 02/07/2016 00:00). É a convenção do "dia de exibição" do setor, não um erro.
8. **PAIS_OBRA vazio** em 6.296 linhas de distribuidoras e 218.045 de exibidoras. Um CPB aparece com mais de um país.
9. **DATA_HORA_ENVIO_PROTOCOLO vazia** em 2.311.855 linhas de distribuidoras (protocolos antigos).
10. **Formatos.** Não há divergência de formato de data ou número: 100% das datas estão em `DD/MM/AAAA`, 100% dos públicos são inteiros sem separador, e todos os CNPJs, exceto o caso 4, seguem a máscara.

## Consistência cadastral (exibidoras)
Cada REGISTRO_SALA tem um único nome e um único complexo; cada complexo, uma única UF e um único exibidor; cada REGISTRO_EXIBIDOR, um único CNPJ, e vice-versa. Essa hierarquia (grupo → exibidor → complexo → sala) é estável e justifica dimensões normalizadas.

## Sobreposição entre as fontes
As duas fontes descrevem as mesmas exibições, uma do ponto de vista da distribuidora e outra do exibidor. Comparando por (data_exibicao, registro_sala, cpb_roe):

| | Exibições (dia, sala, obra) |
|---|---:|
| Nas duas fontes | 15.976.985 |
| Só em distribuidoras | 5.082.215 (inclui 2014–2016, sem cobertura da exibidora) |
| Só em exibidoras | 2.799.532 |
| Nas duas, com público idêntico | 12.997.530 (81% das comuns) |
| Público nas comuns | 1.169.236.891 (distribuidor) × 1.150.318.968 (exibidora) |

As 4.710 salas e 4.851 obras são compartilhadas. **Somar as duas fontes duplicaria cerca de 1,15 bilhão de espectadores.**
