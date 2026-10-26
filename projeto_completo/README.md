# Bilheteria Diária Dash

Dashboard da bilheteria diária de cinema no Brasil (2014–2026), feito em Python com dados abertos da ANCINE.

O dashboard tem duas abas: **Visão geral**, a exploração por UF, período e fonte, e **Recuperação pós-pandemia**, que responde às perguntas de negócio de `../analise.ipynb` em 24 gráficos e 3 KPIs.

## Funções (aba "Visão geral")
- Público diário, semanal ou mensal por UF, com comparação direta entre duas UFs
- Público por região e por UF da região, para o ano escolhido
- Máximos e mínimos de público diário por ano
- Rankings de filmes, distribuidoras e exibidoras
- Seletor de **fonte**: relatórios das distribuidoras ou das exibidoras (as fontes nunca são somadas)
- RangeSlider de anos com Play e Stop, e modo claro/escuro do Design System "Pastel Noturno" (ver `../DESIGN_SYSTEM.md`)

## Aba "Recuperação pós-pandemia"
Cada seção responde a uma pergunta, sempre comparando com 2019, o último ano antes da pandemia. O único filtro é o **ano de comparação** (2020 a 2025, padrão 2025). Ele muda os KPIs, os destaques das colunas e os recortes de um ano só. Cada pergunta usa uma fonte fixa, indicada no subtítulo do gráfico.

| Pergunta | Gráficos | Fonte |
|---|---|---|
| **Principal:** o público voltou ao nível de 2019? | KPIs: público do ano como % de 2019, janeiro a setembro de 2026 como % de 2019 e público por sessão; colunas do público de janeiro a setembro por ano | distribuidor (KPI 3: exibidora) |
| 1. Dependência de poucos sucessos | filmes com 1 milhão ou mais por ano; público dos 10 maiores × demais; os 10 maiores de 2019 e do ano escolhido | distribuidor |
| 2. Filme brasileiro | % do público de filmes que foi para filmes brasileiros; público dos filmes brasileiros (o tooltip mostra o maior do ano) | distribuidor |
| 3. Oferta × demanda | índice de salas, sessões e público (2019 = 100%); público por sessão; % de sessões sem público, por ano e por faixa horária | exibidora (2017+) |
| 4. Geografia | ano como % de 2019 por UF, por região e capital × interior, com a linha da média do Brasil | distribuidor |
| 5. Empresas | fatia das 5 maiores distribuidoras; fatia das líderes de 2019 e de 2025; recuperação das 7 maiores redes, com a linha do mercado | distribuidor / exibidora |
| 6. Ciclo de vida do filme | mediana da % do público nos 7 primeiros dias; mediana das salas no pico, por ano de estreia (filmes com 100 mil ou mais) | distribuidor |
| 7. Quando o público vai | índice por dia da semana (ano e os dois anteriores); público por sessão por faixa horária; mapa de calor de mês × ano | distribuidor / exibidora |
| 8. Dublado × legendado | % do público e das sessões de filmes estrangeiros em cópia dublada; % dublado por região | exibidora (2017+) |

## Como executar

Pré-requisitos: Python 3.12 e [uv](https://docs.astral.sh/uv/) (ou `venv` + `pip`).

```bash
cd BilheteriaDash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r projeto_completo/requirements.txt duckdb
```

Os CSVs agregados (`data_*.csv`) já estão nesta pasta. Para rodar o dashboard:

```bash
cd projeto_completo && ../.venv/bin/python index.py
```

Depois, abra http://127.0.0.1:8050. Em produção, use `gunicorn index:server` (Procfile).

Para regerar os dados a partir dos zips da ANCINE, que ficam na pasta acima de `BilheteriaDash/`:

```bash
cd BilheteriaDash
mkdir -p extraido/distribuidoras extraido/exibidoras
unzip -q ../bilheteria-diaria-obras-por-distribuidoras-csv.zip -d extraido/distribuidoras
unzip -q ../bilheteria-diaria-obras-por-exibidoras-csv.zip -d extraido/exibidoras
.venv/bin/python -I pipeline/perfil.py extraido dados/staging - dados/perfil.json
.venv/bin/python -I pipeline/unificar.py dados/staging dados/perfil.json dados/bilheteria_unificada.csv.gz dados/reconciliacao.json
.venv/bin/python -I pipeline/agregar_dashboard.py dados/bilheteria_limpa.csv.gz projeto_completo
```

Entre a unificação e a agregação, o notebook `dados/limpeza_bilheteria_unificada.ipynb` gera `dados/bilheteria_limpa.csv.gz`, que é a entrada da agregação. A extração ocupa cerca de 13 GB, e o pipeline completo leva perto de 10 minutos. Depois da unificação, `extraido/` pode ser apagado.

## Estrutura do código

| Arquivo | Papel |
|---|---|
| `design/tokens.py` | **Fonte única dos valores visuais**: cor, tipografia, espaço, grade, forma e gráficos. Gera as variáveis CSS. |
| `design/formatos.py` | Formatos pt-BR de número, percentual e data, e marcas de eixo |
| `design/tema_plotly.py` | Templates Plotly claro e escuro, montados a partir dos tokens |
| `dados.py` | Leitura dos CSVs e todos os cálculos da aba "Visão geral" (sem estilo) |
| `dados_recuperacao.py` | Cálculos da aba "Recuperação pós-pandemia", com uma função por pergunta, na mesma conta do notebook |
| `graficos.py` | Construtores de figura: linhas, barras em lista (com linha de referência), colunas por ano ou categoria, colunas divergentes, mapa de calor, estado vazio e cor por entidade |
| `componentes.py` | Componentes de interface: cabeçalho, abas, filtros, seção, grade, cartão, KPI, KPI simples, gráfico, rodapé |
| `layout.py` / `layout_recuperacao.py` | Montagem da página (as duas abas) e da aba de recuperação |
| `callbacks.py` / `callbacks_recuperacao.py` | Interação: controles → dados → gráficos/componentes, uma para cada aba |
| `app.py` / `index.py` | Instância Dash (fontes, CSS dos tokens) e ponto de entrada (`gunicorn index:server`) |
| `assets/styles.css` | Estilos dos componentes, só com `var(--…)` |

Testes, rodados de dentro de `projeto_completo/`:
- `../.venv/bin/python ../testes/verificar_numeros.py comparar ../testes/base_numeros.json` confere as 720 figuras da aba "Visão geral" contra a base gravada antes das mudanças.
- `../.venv/bin/python ../testes/verificar_recuperacao.py` confere 34 valores da aba "Recuperação pós-pandemia" contra as saídas de `../analise.ipynb`.
- `../testes/auditar_layout.js`, colado no console do navegador, aponta na aba visível textos cortados ou sobrepostos, barras não desenhadas e transbordamentos.

## Indicadores e colunas de origem (aba "Visão geral")

As colunas referem-se a `dados/bilheteria_limpa.csv.gz`, que mantém as colunas do unificado (ver `../docs/DICIONARIO_DADOS.md`).

| Indicador (card) | Cálculo | Colunas de origem |
|---|---|---|
| **Máximos e Mínimos** | soma de `publico` por dia no Brasil; maior e menor dia de cada ano | `data_exibicao`, `publico`, `fonte` |
| **Barras por região** | soma de `publico` no ano escolhido, por região | `data_exibicao`, `uf_sala_complexo` → região (mapa IBGE), `publico` |
| **Barras por UF** | soma de `publico` no ano, por UF da região escolhida | `data_exibicao`, `uf_sala_complexo`, `publico` |
| **Público x UF** | soma de `publico` por dia, semana ou mês, por UF selecionada | `data_exibicao`, `uf_sala_complexo`, `publico` |
| **Comparação direta** | público mensal da UF A menos o da UF B, em colunas acima/abaixo de zero | `data_exibicao`, `uf_sala_complexo`, `publico` |
| **Indicadores (UF A e UF B)** | público do último ano do recorte (com aviso quando o ano é parcial) e variação relativa sobre o primeiro ano com cobertura plena (distribuidor ≥ 2014; exibidora ≥ 2017) | `data_exibicao`, `uf_sala_complexo`, `publico` |
| **Top 10 Filmes** | soma de `publico` por obra no intervalo, pela fonte escolhida; o nome exibido é `titulo_brasil`, ou `titulo_original` quando aquele é nulo | `cpb_roe`, `titulo_brasil`, `titulo_original`, `publico`, `data_exibicao` |
| **Top 10 Distribuidoras** | soma de `publico` por CNPJ da distribuidora (só a fonte distribuidor) | `cnpj_distribuidora`, `razao_social_distribuidora`, `publico`, `data_exibicao` |
| **Top 10 Exibidoras** | soma de `publico` por CNPJ da exibidora (só a fonte exibidora) | `cnpj_exibidora`, `razao_social_exibidora`, `publico`, `data_exibicao` |
| **RangeSlider / Play** | restringe todos os cards acima ao intervalo de anos | `data_exibicao` |

Regras de cálculo (detalhes em `../DECISOES.md`):
- **As fontes não se somam.** A fonte vem do seletor; o padrão é distribuidoras, a única com cobertura completa desde 2014.
- Na fonte distribuidor, uma exibição em **co-distribuição** (mesmo dia, sala e obra informados por mais de uma distribuidora) conta uma única vez nos totais. No ranking de distribuidoras, cada uma recebe o público integral.
- Linhas sem UF na origem (521.800 da fonte distribuidor, quase todas de 2014–2015) entram nos totais nacionais e aparecem como região "SEM UF".

## Arquivos de dados do dashboard
| Arquivo | Linhas | Colunas |
|---|---:|---|
| `data_bilheteria.csv` | 218.588 | `FONTE, DATA, ANO, REGIÃO, UF, PUBLICO, REGISTROS` (dia × UF × fonte) |
| `data_ranking.csv` | 22.478 | `FONTE, ANO, TIPO, CHAVE, NOME, PUBLICO` (ano × filme/distribuidora/exibidora) |
| `data_oferta.csv` | 23 | `FONTE, ANO, SALAS, REGISTROS, REGISTROS_SEM_PUBLICO, PUBLICO` (ano × fonte) |
| `data_filmes_ano.csv` | 8.544 | `ANO, CHAVE, TIPO_OBRA, NOME, PUBLICO` (ano × filme; `TIPO_OBRA` é a letra do CPB: B brasileiro, E estrangeiro) |
| `data_local.csv` | 658 | `ANO, UF, REGIÃO, LUGAR, SALAS, PUBLICO` (ano × UF × capital/interior) |
| `data_redes.csv` | 654 | `ANO, CHAVE, NOME, PUBLICO` (ano × grupo exibidor; sem grupo = `SEM GRUPO`) |
| `data_vida_filmes.csv` | 1.208 | `CHAVE, NOME, ANO_ESTREIA, PUBLICO, SALAS_PICO, PCT_7_DIAS, DIAS_ATE_90` (filmes com 100 mil ou mais) |
| `data_sessoes.csv` | 1.465 | `ANO, FAIXA, AUDIO, TIPO_OBRA, REGIÃO, SESSOES, SESSOES_SEM_PUBLICO, PUBLICO` (exibidora, 2017+) |

`REGISTROS` conta sessões na fonte exibidora e exibições (dia, sala, obra) na fonte distribuidor.

## Tecnologias
Python, Dash 2.18, Dash Bootstrap Components, Plotly, pandas, gunicorn. Fonte Geist (Google Fonts), com Inter como alternativa. O pipeline usa DuckDB.
