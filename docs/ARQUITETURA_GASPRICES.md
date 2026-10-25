# Arquitetura do GasPrices

Esta é a especificação que o dashboard de bilheteria (etapa 4) reproduz. Ela foi escrita a partir da leitura completa de `GasPrices/`.

## Stack
- **Python** puro, sem banco de dados. O dado vem de um único CSV local.
- **Dash 2.3.1**, com `html`, `dcc`, `Input`, `Output`, `State` e `callback_context`.
- **dash-bootstrap-components 1.1.0** (`dbc.Container/Row/Col/Card/Button`) e **dash-bootstrap-templates 1.0.5** (`ThemeSwitchAIO`).
- **Plotly 5.8.0** (`plotly.express` e `graph_objects`) e **pandas 1.4.2**.
- **gunicorn 20.1.0** para o deploy no Heroku (`Procfile`: `web: gunicorn index:server`). O README cita NumPy, mas o código não o importa.
- Ícones vêm do **Font Awesome 5.10.2** por CDN.

## Estrutura de pastas
```
GasPrices/
├── estrutura_inicial/    esqueleto da aula: index.py com app + layout vazio, data_gas.csv, styles/dbc.css
└── projeto_completo/
    ├── app.py            cria dash.Dash(__name__, external_stylesheets=FONT_AWESOME); server = app.server
    ├── index.py          leitura e limpeza, layout, callbacks, run_server   (from app import *)
    ├── assets/styles.css carregado automaticamente pelo Dash
    ├── data_gas.csv      120.823 linhas, separador vírgula, UTF-8 com BOM
    ├── requirements.txt  versões fixadas
    ├── Procfile          gunicorn index:server
    └── README.md
```

## Fluxo dos dados
1. `pd.read_csv("data_gas.csv")` lê o arquivo inteiro na memória.
2. A limpeza é feita em pandas:
   - corrige o nome de coluna com espaço;
   - converte `DATA INICIAL` e `DATA FINAL` para datetime e cria `DATA` como a média das duas;
   - ordena por data e renomeia `PREÇO MÉDIO REVENDA` para `VALOR REVENDA (R$/L)`;
   - cria `ANO` (string);
   - filtra `PRODUTO == 'GASOLINA COMUM'` e descarta 15 colunas.
3. `df_main.to_dict()` é gravado em dois `dcc.Store`: `dataset` (recortado pelo RangeSlider) e `dataset_fixed` (intacto). Um terceiro, `controller`, guarda `{'play': bool}`.
4. Cada callback reconstrói `pd.DataFrame(data)` a partir do Store, filtra, agrega e devolve uma figura Plotly.

## Modelo de dados usado
Uma tabela plana semanal por UF, com as colunas `DATA`, `ANO`, `REGIÃO`, `ESTADO` e `VALOR REVENDA (R$/L)`. A única métrica é o preço médio de revenda; as dimensões são tempo, região e estado.

## Componentes (layout em 3 linhas de cards, `dbc.Container(fluid=True)`)
| Linha | Card | Componentes | Callback / lógica |
|---|---|---|---|
| 1 | Título (lg=2) | `Legend` "Gas Prices Analysis", ícone `fa-filter`, `ThemeSwitchAIO`, botão para o site | o tema alimenta todos os gráficos |
| 1 | Máximos e Mínimos (lg=3) | `dcc.Graph` de linhas, altura 150 | max/min do preço por `ANO` em `dataset` |
| 1 | Filtros (lg=7) | dropdowns `select_ano` e `select_regiao`, 2 barras horizontais | média por região no ano; média por estado da região |
| 2 | Preço x Estado (lg=5) | dropdown multi `select_estados0` e linha temporal (altura 425) | `px.line` por estado |
| 2 | Comparação Direta (lg=4) | dropdowns `select_estado1/2`, `scattergl`, texto explicativo | diferença das médias mensais (est1 − est2), anotações "X mais barato" |
| 2 | Indicadores (lg=3) | 2× `go.Indicator` (`number+delta`, delta relativo) | último valor do estado e variação sobre o primeiro do período |
| 3 | Controle temporal | botões Play/Stop, `dcc.RangeSlider` 2004–2021, `dcc.Interval` de 10 s | o slider recorta `dataset`; Play avança o ano final até 2021 |

## Estilo visual
- O tema alterna entre **FLATLY** (claro) e **VAPOR** (escuro, neon roxo) via `ThemeSwitchAIO`, com os templates Plotly `"flatly"`/`"vapor"`.
- `main_config` é comum a todas as figuras: `hovermode: "x unified"`, legenda translúcida no canto superior esquerdo e margens zeradas.
- Os cards usam `style={'height': '100%'}` e as linhas usam `className='main_row g-2 my-auto'`.
- Os gráficos não mostram a modebar (`displayModeBar: False`).
- No CSS, a barra de rolagem fica oculta, os dropdowns ficam com fundo translúcido `rgba(0,0,0,0.2)` e texto branco, e o `body` ocupa 99vh.

## Execução
`pip install -r requirements.txt`, depois `python index.py` (`app.run_server`, porta 8050) ou, em produção, `gunicorn index:server`.

## Limitações relevantes para a adaptação
- Todo o dataframe vai para o navegador via `dcc.Store` (`to_dict`). Funciona com cerca de 20 mil linhas, mas não com dezenas de milhões.
- As versões fixadas de 2022 não instalam em Python ≥ 3.11.
- Os valores iniciais dos filtros vêm de posições fixas do dataframe (`df_main.index[1]`), e o RangeSlider tem os anos 2004–2021 fixos no código.
