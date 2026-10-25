# Dicionário de dados — `dados/bilheteria_unificada.csv.gz`

CSV em UTF-8, compactado com gzip, separador vírgula, cabeçalho na primeira linha e aspas RFC 4180 quando necessário. São 60.056.739 linhas e 24 colunas. Vazio significa nulo. Datas seguem ISO 8601, e números são inteiros sem separador de milhar.

**Fonte**: **D** = só distribuidoras; **E** = só exibidoras; **D+E** = as duas. Um campo de uma fonte só fica vazio nas linhas da outra; nenhum valor foi inventado.

| # | Coluna | Tipo | Fonte | Origem | Descrição |
|---|---|---|---|---|---|
| 1 | `fonte` | texto | controle | — | `distribuidor` ou `exibidora`: o zip de onde a linha veio. |
| 2 | `arquivo_origem` | texto | controle | — | Nome do CSV dentro do zip (ex.: `bilheteria-diaria-obras-por-exibidoras-2016-01-s01.csv`). |
| 3 | `data_exibicao` | data `AAAA-MM-DD` | D+E | DATA_EXIBICAO (`DD/MM/AAAA`) | Dia de exibição. Sessões de madrugada pertencem ao dia anterior. |
| 4 | `sessao` | data e hora `AAAA-MM-DDTHH:MM:SS` | E | SESSAO (`DD/MM/AAAA HH:MM:SS`) | Início da sessão (horário local, sem fuso). Pode cair em `data_exibicao` + 1. |
| 5 | `titulo_original` | texto | D+E | TITULO_ORIGINAL | Título original da obra. |
| 6 | `titulo_brasil` | texto | D+E | TITULO_BRASIL | Título de lançamento no Brasil; vazio quando igual ao original. |
| 7 | `cpb_roe` | texto (14) | D+E | CPB_ROE | CPB (`B…`, obra brasileira) ou ROE (`E…`, obra estrangeira) na ANCINE. É a chave da obra, mas não é única (ver PERFIL_DADOS.md). |
| 8 | `pais_obra` | texto | D+E | PAIS_OBRA | País (ou países) de produção. |
| 9 | `audio` | texto | E | AUDIO | `DUBLADO` ou `ORIGINAL`. |
| 10 | `legendada` | texto | E | LEGENDADA | `SIM` ou `NÃO`. |
| 11 | `registro_sala` | texto (código) | D+E | REGISTRO_SALA | Registro da sala na ANCINE. Vazio em 568.397 linhas D. |
| 12 | `nome_sala` | texto | D+E | NOME_SALA | Nome da sala. Em D, a grafia é livre e varia. |
| 13 | `publico` | inteiro ≥ 0 | D+E | PUBLICO | Espectadores. Em D, por dia × sala × obra × distribuidora; em E, por sessão. |
| 14 | `registro_grupo_exibidor` | texto (código) | D+E | REGISTRO_GRUPO_EXIBIDOR | Registro do grupo exibidor (rede); vazio para exibidores independentes. |
| 15 | `registro_exibidor` | texto (código) | D+E | REGISTRO_EXIBIDOR | Registro da empresa exibidora. |
| 16 | `registro_complexo` | texto (código) | D+E | REGISTRO_COMPLEXO | Registro do complexo (conjunto de salas). |
| 17 | `municipio_sala_complexo` | texto | D+E | MUNICIPIO_SALA_COMPLEXO | Município do complexo. |
| 18 | `uf_sala_complexo` | texto (2) | D+E | UF_SALA_COMPLEXO | UF do complexo (27 UFs). |
| 19 | `razao_social_distribuidora` | texto | D | RAZAO_SOCIAL_DISTRIBUIDORA | Razão social da distribuidora que informou a linha. |
| 20 | `cnpj_distribuidora` | texto | D | CNPJ_DISTRIBUIDORA | CNPJ com máscara, ou o texto `PESSOA FÍSICA` (1.057 linhas). |
| 21 | `nr_protocolo_envio` | texto (código) | D | NR_PROTOCOLO_ENVIO | Protocolo do relatório enviado à ANCINE. |
| 22 | `data_hora_envio_protocolo` | data e hora `AAAA-MM-DDTHH:MM:SS` | D | DATA_HORA_ENVIO_PROTOCOLO | Momento do envio do protocolo; vazio em 2.311.855 linhas. |
| 23 | `razao_social_exibidora` | texto | E | RAZAO_SOCIAL_EXIBIDORA | Razão social da exibidora que informou a sessão. |
| 24 | `cnpj_exibidora` | texto | E | CNPJ_EXIBIDORA | CNPJ da exibidora, com máscara. |

Os códigos (`cpb_roe`, `registro_*`, `nr_protocolo_envio`, CNPJ) são **texto** de propósito: não são quantidades, e assim os zeros e a máscara se preservam.

## Sobreposição potencial entre as fontes

**Não some `publico` entre as fontes.** As duas descrevem as mesmas exibições, de ângulos diferentes: a distribuidora informa o que suas obras fizeram em cada sala; a exibidora informa cada sessão que realizou.

- **Chave de comparação**: (`data_exibicao`, `registro_sala`, `cpb_roe`). Somando o público das sessões E nessa chave, obtém-se o equivalente a uma linha D.
- **Tamanho da sobreposição**: 15.976.985 exibições aparecem nas duas fontes. Em 81% delas o público é idêntico, e o público dessas exibições soma cerca de 1,15–1,17 bilhão em cada fonte. A partir de 2017, o público anual das duas difere menos de 3%.
- **Colunas sobrepostas**: as 13 marcadas D+E. Os cadastros de sala, complexo, exibidor e grupo são os mesmos registros da ANCINE nas duas fontes (4.710 salas e 4.851 obras em comum).
- **Sobreposição dentro da fonte D (co-distribuição)**: 28.024 exibições aparecem uma vez por distribuidora (56.048 linhas), com o mesmo público. Para total de público em D, deduplique por (`data_exibicao`, `registro_sala`, `nome_sala`, `cpb_roe`). Para ranking por distribuidora, use as linhas como estão.
- **Cobertura diferente**: D cobre 2014-01-01 a 2026-09-30 de forma contínua. E vai de 2014-06-01 a 2026-10-18, mas é quase vazia até meados de 2016. Comparações entre fontes só fazem sentido a partir de 2017.

Para escolher a fonte: use D para séries longas e rankings de distribuidoras; use E para detalhes por sessão (horário, áudio, legenda) e rankings de exibidoras.
