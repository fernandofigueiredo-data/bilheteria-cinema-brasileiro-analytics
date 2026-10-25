# Relatório de reconciliação — unificação

Este relatório foi gerado a partir de `dados/perfil.json` e `dados/reconciliacao.json` (scripts `pipeline/perfil.py` e `pipeline/unificar.py`).

## Contagem de linhas por fonte

| Fonte | Arquivos | Linhas antes (CSVs originais) | Linhas depois (CSV unificado) | Diferença |
|---|---:|---:|---:|---:|
| distribuidor | 153 | 21.655.622 | 21.655.622 | 0 |
| exibidora | 660 | 38.401.117 | 38.401.117 | 0 |
| **Total** | **813** | **60.056.739** | **60.056.739** | **0** |

Como as contagens foram feitas:
- **Antes**: varredura em Python de cada arquivo extraído, com linhas não vazias menos o cabeçalho. Nenhum arquivo tem linhas em branco.
- **Depois**: o `bilheteria_unificada.csv.gz` gerado foi relido em modo estrito, com contagem por `fonte` × `arquivo_origem`. Nenhum dos 813 arquivos tem diferença. A contagem intermediária do staging Parquet também foi igual à varredura arquivo a arquivo.
- O parser não rejeitou nenhuma linha (`store_rejects` do DuckDB vazio nas duas fontes).

## Linhas descartadas
**Nenhuma.** Não houve deduplicação, filtro ou agregação. As 96 repetições de chave em D e as 605 em E (ver `PERFIL_DADOS.md`) foram mantidas, porque não são duplicatas exatas: há 0 duplicatas de linha inteira nas duas fontes.

## Linhas ajustadas
Os ajustes são só de formato e afetam todas as linhas, sem mudar o valor:

| Ajuste | Linhas afetadas | Falhas de conversão |
|---|---:|---:|
| Nomes das colunas de MAIÚSCULAS para snake_case | todas | — |
| `data_exibicao`: `DD/MM/AAAA` → `AAAA-MM-DD` | 60.056.739 | 0 |
| `sessao`: `DD/MM/AAAA HH:MM:SS` → `AAAA-MM-DDTHH:MM:SS` | 38.401.117 | 0 |
| `data_hora_envio_protocolo`: idem | 19.343.767 (não vazias) | 0 |
| `publico`: texto → inteiro | 60.056.739 | 0 |
| String vazia → nulo | campos vazios | — |
| Inclusão de `fonte` e `arquivo_origem` | todas | — |
| Colunas exclusivas da outra fonte, vazias | todas | — |
| Codificação UTF-8 → UTF-8 (nenhum arquivo em outra codificação) | — | — |

A releitura do CSV final encontrou 0 valores fora do formato ISO em `data_exibicao` e `sessao` e 0 públicos não inteiros. O arquivo inteiro decodifica como UTF-8 válido (`iconv -f UTF-8`). O público total se mantém: 1.695.424.906 (D) e 1.232.956.821 (E).

## Arquivos
- `dados/bilheteria_unificada.csv.gz`: 1,80 GB compactado, cerca de 15 GB descompactado.
- As cópias extraídas (`extraido/`, 12,9 GB) foram apagadas depois desta conferência, conforme `DECISOES.md`. Os zips originais estão intactos.
- `dados/staging/bruto_*.parquet` (0,5 GB) é a cópia textual sem perda usada pelos scripts e pode ser regerada a partir dos zips.

## Derivados do dashboard (fora do CSV unificado)
`pipeline/agregar_dashboard.py` deduplica a co-distribuição da fonte D só nos totais do dashboard. Ficam 21.627.502 exibições, ou seja, 28.120 linhas a menos (28.024 de co-distribuição e 96 repetições), e o público passa de 1.695.424.906 para 1.693.404.126. O CSV unificado não muda.
