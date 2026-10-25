# Auditoria de UX/UI: dashboard de bilheteria (antes da revisão)

Esta auditoria foi feita em 22/10/2026 sobre `projeto_completo/` (cópia do estado anterior em `testes/index_antes.py`). O dashboard foi renderizado com gunicorn em 1920×1080, 1366×768, 768×1024 e 390×844, nos temas claro (Flatly) e escuro (Vapor), e o código também foi lido. O dashboard tem uma única página, então a auditoria está organizada por visual. A coluna **Status** foi preenchida depois da revisão.

## Global

| # | Defeito | Tipo | Status |
|---|---|---|---|
| G1 | Dois temas genéricos de Bootstrap (Flatly/Vapor) sem relação com a identidade "cinema". O Vapor tem neon roxo e brilho no texto. | cor, identidade | Corrigido: Design System Cinema Clássico, nos modos claro e escuro |
| G2 | Três famílias de fonte: Lato (tema), Times (texto dentro das barras) e Courier New (anotações). | fonte | Corrigido: Inter (interface/dados) e Playfair Display (títulos) |
| G3 | A hierarquia de títulos é aleatória: `Legend` usada como título do app e para "Dados ANCINE", `H3` nos cards, `H6` como subtítulo, e o card de filtros não tem título. | título | Corrigido: 4 níveis tokenizados (página, seção, card, apoio) |
| G4 | O formato numérico é misto: eixos em inglês (`1.5M`, `0.5M`), rótulos em pt-BR (`61.327.367`), hover no padrão do Plotly (`1,234,567`). | formato numérico | Corrigido: pt-BR em tudo (`1,5 mi`, `61.327.367`, `−30,1%`) |
| G5 | O hover das datas usa o formato do Plotly em inglês ("Jan 2016"). | formato de data | Corrigido: `dd/mm/aaaa` e `mm/aaaa`, sem nome de mês |
| G6 | As legendas são uma caixa escura translúcida sobreposta ao gráfico (x = 0,1; y = 0,9), cobrindo linhas e dados, com fonte branca forçada até no tema claro. | sobreposição, legenda | Corrigido: legenda horizontal acima da área de plotagem, com cor de texto do tema |
| G7 | As cores das séries vêm da sequência padrão do template. A mesma UF muda de cor entre "Público x UF" e "Comparação Direta" (RJ fica vermelho num, azul noutro). | cor de série | Corrigido: cor por UF atribuída uma vez e mantida em todos os visuais, sem repintar ao filtrar |
| G8 | Os dropdowns têm fundo cinza `rgba(0,0,0,.3)` e texto branco forçado: o contraste fica baixo no tema claro e as opções ficam ilegíveis. | cor, contraste | Corrigido: controles com tokens de superfície e texto |
| G9 | A barra de rolagem está oculta (`::-webkit-scrollbar {display:none}`) e o `body` está em `99vh`, então não há pista de que a página continua. | paginação, acessibilidade | Corrigido: rolagem nativa visível |
| G10 | Os filtros estão espalhados: a fonte fica no card de título, o período num slider no rodapé, longe de tudo, e o ano/região e as UFs ficam dentro dos cards. Não se sabe o escopo de cada filtro. | paginação, filtro | Corrigido: barra global (fonte + período) no topo e barra de controles por seção, com escopo declarado |
| G11 | Não há cabeçalho de página nem rodapé com fonte e data dos dados. A atribuição à ANCINE é só um rótulo no card. | cabeçalho, rodapé, nota de fonte | Corrigido: cabeçalho fixo e rodapé com nota de fonte e cobertura |
| G12 | Alturas avulsas nos gráficos (150, 140, 425, 350, 250, 380 px), cards de altura desigual na mesma linha e espaçamentos sem escala. | margem, grade | Corrigido: 3 alturas tokenizadas, escala de espaçamento de 4 px e cards de mesma altura por linha |
| G13 | Valores visuais espalhados pelo código (cores rgba, tamanhos, fontes) e componentes duplicados (dropdowns e indicadores repetidos). | código | Corrigido: `design/tokens.py`, `componentes.py`, `graficos.py`, `dados.py`, `layout.py`, `callbacks.py` |
| G14 | Sem estado de carregamento: durante o recálculo a aba mostra "Updating…" e os gráficos ficam congelados. | estado | Corrigido: `dcc.Loading` mantendo o gráfico anterior a 50% de opacidade |
| G15 | O seletor de tema (lua/sol) não tem rótulo, e o lado do "sol" é ambíguo. | estado, rótulo | Corrigido: interruptor rotulado "Modo escuro", que persiste entre visitas |

## Por visual

| # | Visual | Defeito | Tipo | Status |
|---|---|---|---|---|
| V1 | Card de título | O título "Bilheteria Diária – Brasil" quebra em 2 ou 3 linhas na coluna `lg=2`. O ícone a 300% compete com o título, e "Dados ANCINE" tem o mesmo peso do título. | truncamento, título | Corrigido: o card virou o cabeçalho da página |
| V2 | Máximos e Mínimos | A legenda cobre a linha do máximo; a altura de 150 px comprime o eixo; o eixo y está em inglês; não há título de eixo nem unidade. | sobreposição, eixo | Corrigido |
| V3 | Barras por região | O eixo x é invertido (as barras crescem da direita) e confunde. O rótulo dentro da barra é encolhido pelo Plotly (Times 6 a 9 px) e, fora dela, fica em 12 px, com dois tamanhos no mesmo gráfico. Os nomes das categorias ficam ocultos (`showticklabels=False`). Em 390 px, os rótulos de fora invadem o eixo. | sobreposição, inconsistência de fonte | Corrigido: barra horizontal à esquerda, categoria no eixo, valor na ponta com espaço reservado |
| V4 | Barras por UF | Os mesmos problemas de V3. O formato do rótulo é "valor - UF" aqui e "UF - valor" em V3, com ordem invertida entre gráficos irmãos. | formato, inconsistência | Corrigido |
| V5 | Público x UF | A legenda fica sobre os dados; o título do eixo y existe só aqui; as cores das UFs seguem o padrão do Plotly; a seleção de UFs não tem limite (8 ou mais linhas indistinguíveis); a frequência "Diário" não tem rótulo. | sobreposição, cor, legenda | Corrigido: até 4 UFs, com cor estável e rótulos nos controles |
| V6 | Comparação Direta | Dois traços sobrepostos (linha inteira + só a parte positiva) parecem uma linha que muda de cor. A legenda inverte os nomes (o traço chamado "MG" é a linha inteira). As anotações em Courier ficam por cima da linha. O eixo simétrico fixo desperdiça metade da área. Com UF A = UF B, o callback dá erro. | sobreposição, legenda, erro | Corrigido: colunas divergentes nas cores de cada UF, legenda correta e estado vazio para UFs iguais |
| V7 | Indicadores | O número é um `go.Indicator` com tamanho automático (muda de tamanho conforme a largura e transborda em `lg=3`). O título usa um CSS inválido (`size:60%`). A cor do delta é a padrão do Plotly, sem rótulo do período de referência legível. | transbordamento, fonte, cor de estado | Corrigido: cartão de KPI em HTML com borda dourada, valor em Inter 36 px e delta com ícone e cor de estado |
| V8 | Top 10 (três cards) | Nomes cortados em 40 caracteres sem reticências ("DIAMOND FILMS DO BRASIL PRODUÇÃO E DISTR"); rótulos internos em Times minúsculo; barras cinza-ardósia sem relação com a marca; 380 px fixos. | truncamento, fonte, cor | Corrigido: nome abreviado com "…", nome completo no hover e valor na ponta |
| V9 | RangeSlider e Play/Stop | O slider fica no rodapé, longe dos visuais que controla, sem rótulo "Período". Os botões ficam em `md=1` (apertados), e as 13 marcas se encavalam em 390 px. | paginação, rótulo, sobreposição | Corrigido: na barra global, com rótulo, e marcas alternadas em tela estreita |
| V10 | Tooltips | Formato padrão do Plotly (inglês, sem separador de milhar pt-BR) e `hovermode` unificado sem formato de data. | tooltip | Corrigido: `hovertemplate` padronizado por tipo de gráfico |

## Tamanhos de tela
- **1920 px**: os cards da linha 2 têm alturas diferentes; o título do app quebra; as barras de região e de UF ficam a 140 px, com rótulos ilegíveis.
- **1366 px**: igual, com os indicadores a ponto de transbordar.
- **768 px**: os gráficos de barras ficam com rótulos em 2 tamanhos; o slider fica apertado.
- **390 px**: o card de título ocupa a primeira tela inteira; os rótulos das barras de região invadem o eixo; as marcas do slider se sobrepõem.

## Verificação depois da revisão (23/10/2026)

- **Números**: `testes/verificar_numeros.py` chama os 10 visuais pelo endpoint do Dash em 72 combinações de filtro (fonte × período × ano/região × UFs/agregação × UF A/B). O resultado foi **720 de 720 iguais à linha de base** gravada a partir do código anterior.
- **Layout**: `testes/auditar_layout.js` verifica textos sobrepostos, texto sobre barra, texto cortado, marcas de eixo repetidas, transbordamento de cartões e rolagem horizontal. Rodou em 1920×1080, 1366×768, 768×1024 e 390×844, nos dois modos, também com fonte exibidora, períodos de 2014–2015 e 2017–2019, região Nordeste, 4 UFs em agregação diária, UF A = UF B e animação Play. Resultado: **0 problemas**; os 8 gráficos com dados e os 2 KPIs renderizados; nenhum erro de callback.
- **Tooltips**: conferidos em linha, barra e coluna, todos em pt-BR (ex.: `RJ: +1.001.039`).

## Não corrigido
- **Visão em tabela para cada gráfico** (recomendação de acessibilidade da skill `dataviz`): ficou fora do escopo. Os valores das barras estão todos rotulados, mas os de linhas e colunas só aparecem no tooltip.
- **Fontes da web**: Inter e Playfair Display vêm do Google Fonts. Sem internet, o navegador usa as alternativas declaradas (Roboto/system-ui e Georgia).
