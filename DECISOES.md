# Decisões

Este arquivo registra as escolhas em que havia mais de uma saída razoável e que alteram a estrutura dos dados ou do projeto.

## Ambiente e armazenamento
1. **O CSV unificado é gravado compactado (`dados/bilheteria_unificada.csv.gz`).** O disco tinha 28 GB livres; a extração ocupa 12,9 GB, e o CSV sem compressão passaria de 15 GB. A escolha foi do usuário. O conteúdo é CSV UTF-8 comum, legível por `pandas.read_csv`, DuckDB, `zcat` e `COPY ... PROGRAM 'gunzip -c'`.
2. **As cópias extraídas foram apagadas depois da conferência de contagens**, também por escolha do usuário. Os zips originais não foram alterados e permitem refazer tudo.
3. **Staging em Parquet (`dados/staging/bruto_*.parquet`).** Cada fonte foi lida uma única vez dos CSVs, com todas as colunas como texto e o nome do arquivo de origem, para um Parquet. Perfil e unificação partem dessa cópia. Ela não tem perda: a contagem por arquivo foi conferida contra a varredura linha a linha dos CSVs, e o DuckDB não rejeitou nenhuma linha. O motivo é ler os 13 GB uma vez só.
4. **Python 3.12 em `.venv` (uv), com versões atuais da stack do GasPrices.** As versões fixadas em 2022 (dash 2.3.1, pandas 1.4.2) não instalam em Python ≥ 3.11. A API usada é a mesma: `dash`, `dbc`, `ThemeSwitchAIO`, `plotly`. A única mudança é `app.run_server` → `app.run`, que a versão atual exige.
5. **Sem carga no PostgreSQL**, por escolha do usuário: o servidor local está parado e exige senha. O `docs/schema.sql` foi validado com o parser oficial do PostgreSQL (`pglast`, libpg_query) e traz, comentado, o roteiro de carga.

## Unificação
6. **Nenhuma linha foi descartada, deduplicada ou agregada no CSV unificado.** Valores que não convertem para data ou inteiro viram nulos, e a linha é mantida e contada em `docs/RECONCILIACAO.md`.
7. **O texto é preservado como veio**: títulos, razões sociais, nomes de sala e município, sem trim nem mudança de caixa. Só a string vazia vira nulo. Os nomes divergentes para o mesmo CPB/CNPJ estão em `docs/PERFIL_DADOS.md` e não foram "corrigidos". No dashboard, o nome exibido é o mais frequente (`mode`) por chave.
8. **Os identificadores (CPB/ROE, CNPJ, registros, protocolo) continuam como texto**, para não perder zeros à esquerda nem a máscara do CNPJ. O CNPJ fica com a máscara original `00.000.000/0000-00`.
9. **Datas em ISO 8601**: `data_exibicao` em `AAAA-MM-DD`; `sessao` e `data_hora_envio_protocolo` em `AAAA-MM-DDTHH:MM:SS`, sem fuso, porque a fonte não informa fuso.
10. **Uma única tabela larga com a união das 24 colunas**, em vez de duas saídas, como o enunciado pede. A coluna `fonte` separa as origens, e as colunas exclusivas de uma fonte ficam vazias na outra.

## Modelo (schema.sql)
11. **Dois fatos separados por fonte**, `fato_bilheteria_distribuidora` e `fato_bilheteria_sessao_exibidora`, e não um fato único com `fonte`. As granularidades são diferentes (sala-dia-distribuidora × sessão), e a separação física impede somar as duas por engano.
12. **Chave substituta (`bigint identity`) nos fatos.** O perfil mostrou que a chave natural se repete; os detalhes estão em `docs/PERFIL_DADOS.md`.

## Dashboard
13. **O dataframe fica no servidor, e não em `dcc.Store`.** O GasPrices serializa a base inteira no navegador (`df.to_dict()`), o que é inviável com 60 milhões de linhas. Aqui o pipeline gera agregados diários por UF (`data_bilheteria.csv`) e anuais para os rankings (`data_ranking.csv`), lidos com `pd.read_csv` como no original. O `dcc.Store('dataset')` guarda apenas o intervalo de anos do RangeSlider. `dataset_fixed` deixou de ser necessário.
14. **Seletor de fonte, sem soma entre fontes.** O padrão é **distribuidoras**, porque é a única fonte com cobertura completa desde 2014; a exibidora é quase vazia até meados de 2016 (ver `docs/PERFIL_DADOS.md`). A fonte exibidora fica disponível no seletor e traz o detalhe por sessão. O ranking de distribuidoras sempre usa a fonte distribuidor, e o de exibidoras, a fonte exibidora.
15. **Co-distribuição na fonte distribuidor.** A mesma exibição (dia + sala + obra) aparece uma vez por distribuidora, com o mesmo público. Nos totais de público dessa fonte, cada exibição conta uma vez, com o maior público informado. No ranking de distribuidoras, cada uma recebe o público integral das exibições que informou, então a soma do ranking pode superar o total.
16. **A região vem da UF por um mapa fixo do IBGE**, porque os dados não trazem região e o filtro "Região" do GasPrices depende disso. É uma coluna derivada, só no agregado do dashboard, e não existe no CSV unificado.
17. **Referência dos indicadores (cards 1 e 2) = primeiro ano do recorte com cobertura plena da fonte**: 2014 para distribuidor e 2017 para exibidora. Sem isso, a fonte exibidora mostraria variações artificiais de +60% ou mais contra 2016, que tem só um terço da cobertura. O último ano leva o aviso "(até DD/MM)" quando está incompleto (2026). Primeiro tentei um critério por volume de registros, mas ele descartava 2020 (pandemia) por engano.
18. **Rankings por CNPJ, e não por grupo.** Redes com mais de um CNPJ aparecem separadas, porque a origem traz o grupo só como código (`registro_grupo_exibidor`), sem nome. O CNPJ literal "PESSOA FÍSICA" aparece como uma única entrada no ranking de distribuidoras.

## Revisão de UX/UI (Design System "Cinema Clássico")
19. **Os temas Flatly/Vapor e o `ThemeSwitchAIO` deram lugar a tokens próprios e a um interruptor de modo.** O dashboard abre no modo escuro e guarda a escolha entre visitas. A dependência `dash-bootstrap-templates` saiu do `requirements.txt`. Detalhes em `DESIGN_SYSTEM.md`.
20. **O dourado do anexo foi escurecido nas barras do modo claro** (`#B08A1E`, em vez de `#C59B27`), e o valor do KPI no modo claro usa o texto principal. O motivo é contraste: o dourado original tem 2,6:1 sobre branco.
21. **A "Comparação Direta" virou colunas divergentes nas cores das duas UFs.** Antes eram duas linhas sobrepostas com a legenda invertida. Os valores exibidos (diferença mensal) são os mesmos, conferidos por `testes/verificar_numeros.py`.
22. **Os indicadores viraram cartões HTML em vez de `go.Indicator`.** O `go.Indicator` muda o tamanho do número conforme a largura do cartão e não aceita a tipografia do sistema. Valor, referência e variação são os mesmos.
23. **A evolução por UF aceita no máximo 4 UFs.** Assim as cores nunca se repetem: 4 da evolução + UF A + UF B = 6 cores. Antes não havia limite, e mais de 8 linhas ficavam indistinguíveis.
24. **Barras horizontais em formato de lista, sem eixo de valor.** Todo valor já está rotulado, e o eixo se encavalava nos cartões estreitos.

## Aba "Recuperação pós-pandemia"
25. **Os agregados passaram a sair do CSV limpo (`dados/bilheteria_limpa.csv.gz`) e não mais do unificado.** Os números da aba "Visão geral" ficaram idênticos: `testes/verificar_numeros.py` deu 720 de 720 figuras iguais. Só mudaram 38 nomes de filme no ranking, porque o nome exibido agora é o título mais frequente da obra (`mode`) em vez do primeiro encontrado. Os públicos são os mesmos.
26. **Uma aba nova, em vez de mais seções na página existente.** A "Visão geral" é exploratória, com fonte, período e UFs livres. A aba nova responde a perguntas fechadas, com regras fixas. Misturar as duas faria os filtros de uma valerem pela metade na outra. As abas usam `dcc.Tabs` e guardam a escolha entre visitas.
27. **A fonte é fixa por pergunta, e não escolhida pelo usuário.** As séries longas, os filmes e a geografia usam a fonte distribuidor, a única completa desde 2014. O que é medido por sessão (oferta, faixa horária, áudio, redes) usa a fonte exibidora, só de 2017 em diante, quando a cobertura dela fica nacional. O subtítulo de cada gráfico diz a fonte. As duas nunca se somam.
28. **A base é sempre 2019, e o único filtro é o ano de comparação (2020 a 2025).** 2019 é o último ano antes da pandemia. 2026 não entra no filtro porque só vai até setembro. Ele aparece no KPI e no gráfico de janeiro a setembro, que comparam os mesmos meses em todos os anos.
29. **A sazonalidade usa só os anos fora da pandemia (2016 a 2019 e 2022 a 2025).** O índice é o público por dia do mês dividido pela média do ano, o que corrige a diferença de dias entre os meses. 2020 e 2021 distorceriam o padrão. 2014 e 2015 ficam de fora para manter o mesmo conjunto do notebook.
30. **Capital × interior compara o nome do município sem acento e em caixa alta** com a lista das 27 capitais, para que a comparação não dependa de acento nem de caixa na grafia do município.
31. **Ciclo de vida só considera filmes com 100 mil espectadores ou mais**, e a estreia é o primeiro dia com pelo menos 25% do pico de salas. Assim, pré-estreias e sessões avulsas antes do lançamento não contam como estreia. Os valores são medianas por ano de estreia, para que um único grande lançamento não puxe a média.
32. **Todos os valores da aba conferem com `analise.ipynb`.** O teste `testes/verificar_recuperacao.py` confere 34 deles, com tolerância igual às casas decimais que o notebook mostra.

## Design System "Pastel Noturno"
33. **O "Cinema Clássico" deu lugar ao "Pastel Noturno"**, a pedido do usuário, a partir de uma imagem de referência: fundo quase preto, texto branco e acentos pastel. Isso substitui os itens 19 e 20 no que diz respeito a cores e fontes. Os números não mudaram: 720/720 e 34/34. Detalhes em `DESIGN_SYSTEM.md`.
34. **Os gráficos usam os matizes da imagem, mas não os tons exatos.** Os tons originais reprovaram no validador da skill `dataviz` (luminosidade alta demais no modo escuro, croma baixo demais e confusão no daltonismo). Cada matiz foi mantido e só a luminosidade e o croma foram ajustados. A ordem das 6 cores foi escolhida entre as 720 possíveis como a que passa em todas as checagens nos dois modos. Os tons exatos da imagem ficaram para a interface: KPI, aba ativa, foco e o filete do cabeçalho.
35. **Lavanda é a série principal e pêssego, a comparativa.** O pêssego tem a maior separação da lavanda (ΔE 22 em visão normal e no daltonismo) e não sugere "bom" nem "ruim", ao contrário da menta, que lembraria o verde de "positivo".
36. **O cabeçalho é escuro também no modo claro**, como na imagem. Por isso o ícone e o interruptor sobre ele usam a lavanda clara (`cabecalho_destaque`), e não o destaque do modo claro, que ficaria sem contraste sobre o preto.
37. **Uma fonte só (Geist), no lugar de Inter + Playfair Display.** A imagem usa uma grotesca geométrica, e a skill `dataviz` recomenda uma única família sem serifa também nos números. O texto da interface subiu 1 px, para que nada fique abaixo de 12 px. Os gráficos continuam em 12 px.
