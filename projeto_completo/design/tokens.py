"""Design System "Pastel Noturno": fonte única de todos os valores visuais.

Nenhum outro módulo define cor, fonte, tamanho, espaçamento, raio ou sombra:
- o Python (gráficos e componentes) lê os dicionários abaixo;
- o CSS (assets/styles.css) lê as variáveis CSS geradas por `css_variaveis()`.

Base: a paleta da imagem de referência (fundo quase preto, texto branco e acentos pastel:
lavanda, menta, pêssego, orquídea, aço, oliva e rosa). Os acentos de interface usam as cores
da imagem como vieram. As marcas dos gráficos usam os mesmos matizes em passos validados pelo
script da skill dataviz (faixa de luminosidade, croma, daltonismo e contraste), nos dois modos.
Ajustes e o motivo de cada um estão em ../DESIGN_SYSTEM.md.
"""

# ---------------------------------------------------------------- cor
# Acentos da imagem de referência, como vieram (texto e detalhes de interface, nunca marcas de gráfico).
ACENTOS = {'lavanda': '#BA94FA', 'menta': '#55FBB1', 'pessego': '#E3B48C', 'orquidea': '#C561CB', 'aco': '#69A9CC'}
_FAIXA = f"linear-gradient(90deg, {', '.join(ACENTOS.values())})"

# Mesmas chaves nos dois modos; o modo escuro é uma seleção própria, não uma inversão.
CORES = {
    'claro': {
        'canvas': '#FAFAFA',
        'superficie': '#FFFFFF',        # cartões
        'superficie_alt': '#F4F4F5',    # barra de filtros
        'cabecalho': '#0F0F0F',         # o cabeçalho fica escuro nos dois modos, como a imagem
        'cabecalho_texto': '#FFFFFF',
        'cabecalho_destaque': ACENTOS['lavanda'],   # ícone e interruptor sobre o cabeçalho (7,9:1)
        'faixa': _FAIXA,                # filete do cabeçalho com os acentos da imagem
        'estrutura': '#0F0F0F',         # títulos de seção
        'destaque': '#7A52C7',          # lavanda escurecida: foco, aba ativa, trilho do slider (5,4:1)
        'destaque_texto': '#6D45B5',    # lavanda legível como texto (6,6:1 sobre branco)
        'sobre_destaque': '#FFFFFF',    # texto sobre fundo lavanda (5,4:1)
        'kpi_valor': '#6D45B5',
        'texto': '#0F0F0F',
        'texto_sec': '#525252',         # 7,8:1
        'texto_mudo': '#6B6B6B',        # 5,3:1
        'borda': '#E5E5E5',
        'grade': 'rgba(15, 15, 15, 0.06)',
        'eixo': '#D4D4D4',
        'controle': '#FFFFFF',
        'controle_borda': '#D4D4D4',
        'foco': 'rgba(122, 82, 199, 0.35)',
        'tooltip_fundo': '#0F0F0F',
        'tooltip_texto': '#FFFFFF',
        'sombra': '0 1px 2px rgba(15, 15, 15, 0.05), 0 2px 8px rgba(15, 15, 15, 0.04)',
        # séries (passos validados para a superfície branca)
        'serie_principal': '#835CBD',   # lavanda
        'serie_comparativa': '#A0652B', # pêssego (comparação, nunca "negativo"); ΔE 22 da principal
        'categorica': ['#118A5B', '#4399C5', '#A0652B', '#A744AE', '#81761F', '#8F4249'],
        # estado (reservadas; sempre com ícone + texto)
        'positivo': '#2E7D32',
        'negativo': '#D32F2F',
        'alerta': '#B84A00',
        'info': '#1976D2',
        # divergente do mapa de calor (aço / neutro / pêssego); passos claros para o texto escuro ler (12:1)
        'divergente_baixo': '#ABD8F3',
        'divergente_meio': '#F4F4F5',
        'divergente_alto': '#EEC9A9',
        'referencia': '#8C8C8C',        # linha de referência (média nacional etc.)
    },
    'escuro': {
        'canvas': '#0F0F0F',            # o fundo da imagem
        'superficie': '#171717',
        'superficie_alt': '#131313',
        'cabecalho': '#0F0F0F',
        'cabecalho_texto': '#FFFFFF',
        'cabecalho_destaque': ACENTOS['lavanda'],
        'faixa': _FAIXA,
        'estrutura': '#FFFFFF',
        'destaque': ACENTOS['lavanda'],          # 7,4:1 sobre o cartão
        'destaque_texto': ACENTOS['lavanda'],
        'sobre_destaque': '#0F0F0F',             # 8,0:1
        'kpi_valor': ACENTOS['lavanda'],
        'texto': '#FFFFFF',
        'texto_sec': '#A3A3A3',         # 7,1:1
        'texto_mudo': '#8A8A8A',        # 5,2:1
        'borda': '#262626',
        'grade': 'rgba(255, 255, 255, 0.06)',
        'eixo': '#333333',
        'controle': '#141414',
        'controle_borda': '#2E2E2E',
        'foco': 'rgba(186, 148, 250, 0.40)',
        'tooltip_fundo': '#262626',
        'tooltip_texto': '#FFFFFF',
        'sombra': '0 1px 2px rgba(0, 0, 0, 0.5), 0 4px 12px rgba(0, 0, 0, 0.3)',
        'serie_principal': '#A47EE2',   # lavanda no topo da faixa escura (L 0,67)
        'serie_comparativa': '#C3864E', # pêssego; ΔE 22 da principal
        'categorica': ['#15B075', '#3C93BF', '#C3864E', '#CB67D1', '#A29745', '#B36267'],
        'positivo': '#0CA30C',          # 5,3:1
        'negativo': '#F47174',          # 6,4:1
        'alerta': '#FAB219',
        'info': ACENTOS['aco'],
        'divergente_baixo': '#094864',  # texto branco 9,9:1
        'divergente_meio': '#262626',
        'divergente_alto': '#5E3811',   # texto branco 10,3:1
        'referencia': '#8A8A8A',
    },
}
MODO_PADRAO = 'escuro'
TRANSPARENTE = 'rgba(0, 0, 0, 0)'   # fundo dos gráficos: quem pinta é o cartão

# ---------------------------------------------------------------- tipografia
# Uma família só, como a imagem: Geist (grotesca geométrica), com números tabulares nos eixos e tabelas.
FONTE = {
    'sans': "Geist, Inter, system-ui, -apple-system, 'Segoe UI', sans-serif",
    'display': "Geist, Inter, system-ui, -apple-system, 'Segoe UI', sans-serif",
    'url': 'https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap',
}
# tamanho (px), peso, família, altura de linha, espaçamento entre letras (em)
TIPO = {
    'pagina':     {'tamanho': 28, 'peso': 600, 'familia': 'display', 'linha': 1.15, 'tracking': -0.02},  # título da página
    'secao':      {'tamanho': 22, 'peso': 600, 'familia': 'display', 'linha': 1.2, 'tracking': -0.015}, # título de seção
    'card':       {'tamanho': 15, 'peso': 600, 'familia': 'sans', 'linha': 1.35, 'tracking': -0.005},  # título de card/gráfico
    'kpi':        {'tamanho': 36, 'peso': 600, 'familia': 'display', 'linha': 1.1, 'tracking': -0.02},  # valor de KPI
    'corpo':      {'tamanho': 14, 'peso': 400, 'familia': 'sans', 'linha': 1.5, 'tracking': 0},       # rótulos, controles
    'apoio':      {'tamanho': 13, 'peso': 400, 'familia': 'sans', 'linha': 1.45, 'tracking': 0},      # subtítulos, descrições
    'micro':      {'tamanho': 12, 'peso': 400, 'familia': 'sans', 'linha': 1.4, 'tracking': 0},       # notas, legendas de slider
    'rotulo':     {'tamanho': 12, 'peso': 500, 'familia': 'sans', 'linha': 1.3, 'tracking': 0.04},    # rótulos de controle (caixa alta)
}

# ---------------------------------------------------------------- espaço, grade, forma
ESPACO = {0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48}   # escala de 4 px
GRADE = {'colunas': 12, 'calha': ESPACO[4], 'largura_max': 1680, 'margem_pagina': ESPACO[5]}
RAIO = {'card': 10, 'controle': 6, 'pilula': 999, 'barra': 4}
BORDA = {'fina': 1, 'acento': 2}          # acento = borda lavanda do KPI e filete do cabeçalho
TRANSICAO = '150ms ease-out'
# medidas de componentes (px)
TAMANHO = {
    'controle': 36,            # altura de dropdown, botão e segmentado
    'marca': 10,               # bolinha de identidade da série no rótulo do KPI
    'icone_cabecalho': 22,
    'foco': 2,                 # anel de foco
    'largura_controle': 150,   # largura mínima de um dropdown
    'largura_larga': 300,      # dropdown múltiplo de UFs
    'largura_fonte': 360,
    'largura_periodo': 520,
}

# ---------------------------------------------------------------- gráficos
GRAFICO = {
    'altura': {'compacto': 260, 'padrao': 320, 'alto': 400, 'longo': 960},   # longo: lista das 27 UFs (~35 px por linha)
    'linha': 2,                 # espessura de linha (px)
    'marcador': 8,              # diâmetro de marcador (px)
    'barra_folga': 0.35,        # bargap: mantém a barra ~<= 24 px nas alturas acima
    'barra_espessura': 12,      # espessura fixa (px) das barras horizontais, igual em todos os gráficos
    'coluna_folga': 0.15,       # bargap das colunas da comparação mensal
    'coluna_ano_folga': 0.3,    # bargap das colunas por ano / por categoria
    'folga_topo': 1.18,         # espaço acima da maior coluna para o rótulo de valor
    'folga_topo_vertical': 1.4,  # idem, com o rótulo na vertical (séries longas)
    'celula_folga': 2,          # espaço entre células do mapa de calor (px)
    'afastamento_rotulo': 6,    # distância entre marca de eixo/ponta da barra e o texto (px)
    'margem': {'l': 8, 'r': 16, 't': 20, 'b': 8},   # t acomoda o nome sobre a primeira barra
    'margem_legenda': 36,       # espaço no topo quando há legenda
    'fonte_eixo': 12,           # os gráficos mantêm 12 px, mesmo com o texto da interface em 13–14 px
    'fonte_legenda': 12,
    'fonte_rotulo': 12,
    'fonte_tooltip': 13,
    'ticks': 5,                 # nº aproximado de marcas no eixo de valor
    'anos_passo_1': 8,          # até quantos anos o eixo anual marca ano a ano
    'nome_max': 26,             # caracteres antes de abreviar com "…" (nome completo no tooltip)
    'carregando_opacidade': 0.5,
    'carregando_atraso_ms': 300,
}

# ---------------------------------------------------------------- comportamento
LIMITES = {'max_ufs': 4}       # séries simultâneas em "Público x UF" (cores não se repetem: 4 + UF A + UF B = 6)


def _nome_css(chave):
    return chave.replace('_', '-')


def css_variaveis():
    """Gera as variáveis CSS (:root) a partir dos tokens. O CSS do app só usa var(--...)."""
    def bloco(modo):
        c = CORES[modo]
        linhas = [f'--cor-{_nome_css(k)}: {v};' for k, v in c.items() if isinstance(v, str)]
        linhas += [f'--cor-serie-{i + 1}: {v};' for i, v in enumerate(c['categorica'])]
        return '\n  '.join(linhas)

    fixos = [f"--fonte-sans: {FONTE['sans']};", f"--fonte-display: {FONTE['display']};"]
    for nome, t in TIPO.items():
        fixos += [f'--tipo-{nome}-tamanho: {t["tamanho"]}px;', f'--tipo-{nome}-peso: {t["peso"]};',
                  f'--tipo-{nome}-familia: var(--fonte-{t["familia"]});', f'--tipo-{nome}-linha: {t["linha"]};',
                  f'--tipo-{nome}-tracking: {t["tracking"]}em;']
    fixos += [f'--espaco-{k}: {v}px;' for k, v in ESPACO.items()]
    fixos += [f'--raio-{k}: {v}px;' for k, v in RAIO.items()]
    fixos += [f'--borda-{k}: {v}px;' for k, v in BORDA.items()]
    fixos += [f'--tamanho-{_nome_css(k)}: {v}px;' for k, v in TAMANHO.items()]
    fixos += [f"--grade-calha: {GRADE['calha']}px;", f"--grade-largura-max: {GRADE['largura_max']}px;",
              f"--grade-margem-pagina: {GRADE['margem_pagina']}px;", f'--transicao: {TRANSICAO};',
              f"--carregando-opacidade: {GRAFICO['carregando_opacidade']};"]
    fixos = '\n  '.join(fixos)
    return (f":root {{\n  {fixos}\n}}\n"
            f":root, :root[data-theme='claro'] {{\n  color-scheme: light;\n  {bloco('claro')}\n}}\n"
            f":root[data-theme='escuro'] {{\n  color-scheme: dark;\n  {bloco('escuro')}\n}}\n")


def modo(escuro):
    """Valor do interruptor de tema -> nome do modo."""
    return 'escuro' if escuro else 'claro'
