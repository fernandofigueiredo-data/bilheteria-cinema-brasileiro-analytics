# Design System: Pastel Noturno

A implementação fica em **`projeto_completo/design/tokens.py`**, a fonte única de todos os valores visuais. O CSS recebe esses valores como variáveis geradas por `css_variaveis()` e injetadas no `<head>` por `app.py`. Os gráficos recebem os mesmos valores pelos templates Plotly de `design/tema_plotly.py`. Os formatos de número e data ficam em `design/formatos.py`.

O ponto de partida é a imagem de referência enviada pelo usuário: fundo quase preto (`#0F0F0F`), texto branco e frases destacadas em tons pastel. As cores foram lidas dos pixels da imagem. Este sistema substitui o "Cinema Clássico" (bordô e dourado), e os números do dashboard não mudaram.

| Matiz da imagem | Cor lida | Uso na interface | Passo nos gráficos (escuro / claro) |
|---|---|---|---|
| lavanda | `#BA94FA` | destaque: foco, aba ativa, slider, valor do KPI, ícone do cabeçalho | série principal `#A47EE2` / `#835CBD` |
| menta | `#55FBB1` | filete do cabeçalho | categórica 1 `#15B075` / `#118A5B` |
| aço | `#69A9CC` | filete do cabeçalho; "info" no escuro | categórica 2 `#3C93BF` / `#4399C5`; polo frio do mapa de calor |
| pêssego | `#E3B48C` | filete do cabeçalho | série comparativa e categórica 3 `#C3864E` / `#A0652B`; polo quente do mapa de calor |
| orquídea | `#C561CB` | filete do cabeçalho | categórica 4 `#CB67D1` / `#A744AE` |
| oliva | `#9C9666` | — | categórica 5 `#A29745` / `#81761F` |
| rosa | `#955C5F` | — | categórica 6 `#B36267` / `#8F4249` |

## Por que os gráficos não usam as cores da imagem como vieram

As cores da imagem são pastéis claros e pouco saturados. Com elas, a paleta de 6 cores reprovou no validador da skill `dataviz`: menta, pêssego e aço ficam acima da faixa de luminosidade do modo escuro; pêssego, aço, oliva e rosa ficam abaixo do croma mínimo e parecem cinza; e aço × orquídea se confundem no daltonismo deutan (ΔE 5,6).

A solução mantém cada **matiz** e ajusta só a luminosidade e o croma, para cada modo:
1. **Faixa de luminosidade (OKLCH L):** 0,48–0,67 no escuro e 0,43–0,77 no claro. Cada cor ficou o mais perto possível do topo da faixa escura, para continuar "pastel".
2. **Croma mínimo de 0,10**, para a cor não ler como cinza.
3. **Ordem fixa das cores**, escolhida entre as 720 ordens possíveis, como a que passa em todas as checagens nos dois modos:
   - **Daltonismo** (protan e deutan, pares vizinhos): ΔE mínimo de 10,0 no escuro e 10,1 no claro (meta ≥ 8).
   - **Visão normal:** ΔE mínimo de 16,1 no escuro e 16,3 no claro (piso ≥ 15).
   - **Contraste** de todas as cores com o cartão ≥ 3:1.
4. **Principal × comparativa** (lavanda × pêssego): ΔE de 22,2 no daltonismo e 22,1 na visão normal. É o par que aparece junto em quase todos os gráficos.

Os acentos de **interface**, que são texto e detalhes e não marcas de dados, usam as cores da imagem como vieram. Assim a identidade se mantém onde ela aparece mais: o valor dos KPIs, a aba ativa e o filete do cabeçalho com as 5 cores.

Para refazer a validação:

```bash
node <skill dataviz>/scripts/validate_palette.js "#15B075,#3C93BF,#C3864E,#CB67D1,#A29745,#B36267" --mode dark --surface "#171717"
node <skill dataviz>/scripts/validate_palette.js "#118A5B,#4399C5,#A0652B,#A744AE,#81761F,#8F4249" --mode light --surface "#FFFFFF"
```

## Tokens

- **Cor** (`CORES[modo]`, com as mesmas chaves nos dois modos; o claro é uma seleção própria, não uma inversão):

  | Papel | Escuro | Claro | Contraste |
  |---|---|---|---|
  | canvas / cartão | `#0F0F0F` / `#171717` | `#FAFAFA` / `#FFFFFF` | — |
  | cabeçalho | `#0F0F0F` | `#0F0F0F` | escuro nos dois modos, como a imagem |
  | texto / secundário / mudo | `#FFFFFF` / `#A3A3A3` / `#8A8A8A` | `#0F0F0F` / `#525252` / `#6B6B6B` | 7,1:1 e 5,2:1 (escuro); 7,8:1 e 5,3:1 (claro) |
  | destaque | `#BA94FA` | `#7A52C7` | 7,4:1 / 5,4:1 |
  | texto em destaque e valor do KPI | `#BA94FA` | `#6D45B5` | 7,4:1 / 6,6:1 |
  | borda / grade | `#262626` / branco a 6% | `#E5E5E5` / preto a 6% | grade recessiva |
  | referência (linha de média) | `#8A8A8A` | `#8C8C8C` | — |
  | mapa de calor (baixo / meio / alto) | `#094864` / `#262626` / `#5E3811` | `#ABD8F3` / `#F4F4F5` / `#EEC9A9` | texto da célula ≥ 9,9:1 |
  | estado (positivo, negativo, alerta, info) | `#0CA30C`, `#F47174`, `#FAB219`, `#69A9CC` | `#2E7D32`, `#D32F2F`, `#B84A00`, `#1976D2` | ≥ 5,3:1 como texto no escuro |

  `faixa` é o gradiente das 5 cores da imagem (lavanda, menta, pêssego, orquídea e aço), usado no filete de 2 px sob o cabeçalho. `cabecalho_destaque` é a lavanda da imagem nos dois modos, porque o cabeçalho é sempre escuro.
- **Tipografia** (`TIPO`): uma família só, **Geist** (Google Fonts), uma grotesca geométrica próxima da letra da imagem. Inter fica como alternativa. Não há mais serif. Títulos e KPI levam espaçamento negativo entre letras, como na imagem; o rótulo em caixa alta leva espaçamento positivo.

  | Nível | Peso | Tamanho | Espaçamento |
  |---|---|---|---|
  | página | 600 | 28 px | −0,02 em |
  | seção | 600 | 22 px | −0,015 em |
  | card | 600 | 15 px | −0,005 em |
  | KPI | 600 | 36 px | −0,02 em |
  | corpo | 400 | 14 px | 0 |
  | apoio | 400 | 13 px | 0 |
  | micro | 400 | 12 px | 0 |
  | rótulo | 500 | 12 px, caixa alta | +0,04 em |

  O texto da interface subiu 1 px (nada fica abaixo de 12 px, regra da skill `ui-ux-pro-max`). Os gráficos ficaram em 12 px nos eixos, legendas e rótulos (13 px no tooltip), para manter a densidade e não encavalar no celular.
- **Espaço**: escala de 4 px (0, 4, 8, 12, 16, 24, 32, 48).
- **Grade**: 12 colunas, calha de 16 px, largura máxima de 1680 px e margem de página de 24 px (16 px no celular).
- **Forma**: raio de 10 px (cartão), 6 px (controle) e 4 px (ponta da barra); borda fina de 1 px e acento de 2 px (borda do KPI, aba ativa e filete); sombra por modo.
- **Gráfico** (`GRAFICO`):
  - alturas: compacto 260, padrão 320, alto 400 e longo 960 (a lista das 27 UFs);
  - marcas: linha de 2 px, barra horizontal de 12 px fixos, colunas divergentes com folga de 0,15 e colunas por ano com folga de 0,3;
  - folga acima da maior coluna para o rótulo: 1,18 (horizontal) e 1,4 (vertical); 2 px entre células do mapa de calor;
  - margens padronizadas; 5 marcas no eixo de valor e abreviação de nomes em 26 caracteres;
  - carregamento a 50% de opacidade após 300 ms.
- **Tamanho** (`TAMANHO`): controle com 36 px de altura, marca de identidade de 10 px, foco de 2 px e larguras mínimas de controle.
- **Movimento**: transições de 150 ms; com `prefers-reduced-motion`, todas ficam em 0 ms.

## Padrões

- **Abas**: logo abaixo do cabeçalho, alinhadas à esquerda e na largura toda. A aba ativa leva borda inferior lavanda. Abaixo de 800 px, as abas se empilham.
- **Página**: cabeçalho quase preto com o filete de 5 cores. Abaixo vem uma barra de filtros globais (fonte + período). Seguem as seções, cada uma com título, descrição e controles próprios à direita, e por fim o rodapé com a nota de fonte. Tudo fica centralizado na mesma largura máxima.
- **Cartão**: título (card), subtítulo (apoio), corpo e nota (micro). Todos os cartões de uma linha têm a mesma altura.
- **KPI simples** (aba de recuperação): mesmo cartão do KPI, com rótulo, valor e uma linha de detalhe com seta e cor de estado. Não leva bolinha de entidade.
- **KPI**: borda superior lavanda; rótulo com uma bolinha na cor da UF; valor em 36 px; delta com seta, cor de estado e "vs. ANO"; nota de método.
- **Filtros**: rótulo em caixa alta acima de cada controle; dropdowns, botões segmentados e botões de ícone com 36 px de altura; foco visível em lavanda.
- **Gráficos**:
  - Legenda horizontal acima da área de plotagem, só com 2 ou mais séries; sem legenda numa série única, que o título nomeia.
  - Barras horizontais em lista: nome à esquerda e valor à direita sobre a barra, sem eixo de valor (todo valor já está rotulado).
  - Barras em lista com **linha de referência**: a média (Brasil ou mercado) entra como linha pontilhada cinza, e as barras abaixo dela vão para a cor comparativa (pêssego).
  - **Colunas por ano ou categoria**: todas em lavanda, e os anos em destaque (2019 e o ano escolhido) em pêssego. Só os destaques levam rótulo de valor. Com mais de 8 colunas, o eixo marca ano sim, ano não, e o rótulo fica na vertical, para não invadir a coluna vizinha no celular.
  - **Mapa de calor** (mês × ano): escala divergente aço ↔ pêssego, com o meio neutro em 1 (a média do ano), o valor escrito em cada célula e os anos no topo.
  - Linhas de 2 px com tooltip unificado.
  - Diferença mensal em colunas divergentes, cada lado na cor da sua UF.
  - O texto (valores, rótulos e legendas) usa sempre as cores de texto, nunca a cor da série.
- **Cor por entidade**: cada UF ganha uma cor na primeira vez que aparece, e essa cor vale em todos os visuais (linhas, colunas e KPIs). Tirar uma UF da seleção não repinta as outras. São no máximo 4 UFs na evolução, mais UF A e UF B: 6 cores, sem repetir, na ordem validada.
- **Estado**: verde, vermelho, laranja e azul ficam reservados, sempre com ícone e texto, nunca só pela cor, e nunca servem de "série 4".
- **Formatos** (`design/formatos.py`), iguais em todo o dashboard:
  - inteiro `61.327.367`;
  - eixo compacto `1,5 mi` / `500 mil`;
  - percentual `−30,1%` / `+59,1%`, com sinal de menos tipográfico;
  - data `dd/mm/aaaa` e mês `mm/aaaa`, sem nomes de mês;
  - anos inteiros (passo de 1 até 8 anos);
  - rótulo de dado compacto com casa decimal fixa (`93,0 mi`, `142,5 mi`), para não alternar entre formatos na mesma série.
- **Estados**:
  - Carregando: o gráfico anterior fica a 50% de opacidade.
  - Vazio: mensagem centralizada, na mesma altura do gráfico.
  - UFs iguais: o próprio gráfico mostra a mensagem.
  - KPI sem dados: o cartão mostra a mensagem.

## Verificação

- `testes/verificar_numeros.py`: 720 de 720 figuras da "Visão geral" com os mesmos números.
- `testes/verificar_recuperacao.py`: 34 de 34 valores iguais aos do notebook.
- `testes/auditar_layout.js`: 0 problemas nas duas abas, em 390, 768, 1366 e 1920 px, nos modos claro e escuro.
