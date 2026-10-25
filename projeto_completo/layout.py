"""Estrutura da página: cabeçalho, duas abas (Visão geral e Recuperação pós-pandemia) e rodapé."""
from dash import dcc, html
import dash_bootstrap_components as dbc

import componentes as ui
import dados as d
import layout_recuperacao
from design import formatos
from design.tokens import MODO_PADRAO
from graficos import MAX_UFS, atribuir_cores

UF_A, UF_B = d.ufs_top[1], d.ufs_top[2]
UFS_INICIAIS = d.ufs_top[:3]


def _opcoes(valores, rotulos=None):
    return [{'label': (rotulos or {}).get(v, str(v)), 'value': v} for v in valores]


def _filtros_globais():
    return ui.barra_filtros([
        ui.controle('Fonte dos dados', ui.segmentado(
            'select_fonte', [{'label': n, 'value': k} for k, n in d.FONTES.items()], d.FONTE_PADRAO),
            ajuda=' · '.join(f'{n}: {d.FONTES_DETALHE[k]}' for k, n in d.FONTES.items()), largura='fonte'),
        ui.controle('Período', html.Div(className='ds-periodo', children=[
            ui.botao_icone('play-button', 'fa-play', 'Animar o período ano a ano'),
            ui.botao_icone('stop-button', 'fa-stop', 'Parar a animação'),
            html.Div(dcc.RangeSlider(
                id='rangeslider', min=d.ANO_MIN, max=d.ANO_MAX, step=1, value=[d.ANO_MIN, d.ANO_MAX],
                marks={a: {'label': str(a)} for a in d.ANOS}, pushable=1, allowCross=False,
                tooltip={'always_visible': False, 'placement': 'bottom'},
            ), className='ds-periodo__slider'),
        ]), largura='periodo'),
    ], nota='A fonte e o período valem para todas as seções, exceto "Público por região", que usa o ano escolhido nela.')


def _secao_panorama():
    return ui.secao(
        'Panorama do período', 'Dias de maior e de menor público no Brasil, ano a ano.',
        ui.grade([(ui.cartao('Máximos e mínimos de público diário', ui.grafico('static-maxmin', 'compacto'),
                             subtitulo='Soma nacional por dia; o ponto é o maior e o menor dia de cada ano'),
                   {'lg': 12})]),
    )


def _secao_regiao():
    controles = [
        ui.controle('Ano', ui.dropdown('select_ano', _opcoes(d.ANOS), d.ANO_MAX - 1), 'select_ano'),
        ui.controle('Região', ui.dropdown('select_regiao', _opcoes(d.REGIOES), 'SUDESTE'), 'select_regiao'),
    ]
    return ui.secao(
        'Público por região', 'Público total do ano escolhido, por região e pelas UFs da região escolhida.',
        ui.grade([
            (ui.cartao('Por região', ui.grafico('regiaobar_graph', 'alto'),
                       nota='"SEM UF": linhas da origem sem UF informada.'), {'lg': 6}),
            (ui.cartao('UFs da região', ui.grafico('estadobar_graph', 'alto'),
                       id_subtitulo='subtitulo_estados'), {'lg': 6}),
        ]),
        controles=controles,
    )


def _secao_ufs():
    controles = [
        ui.controle('UFs', ui.dropdown('select_estados0', _opcoes(d.UFS), UFS_INICIAIS, multi=True,
                                       placeholder='Escolha até 4 UFs'), 'select_estados0',
                    ajuda=f'Até {MAX_UFS} UFs', largura='larga'),
        ui.controle('Agregação', ui.dropdown('select_freq', _opcoes(d.FREQUENCIAS, d.FREQUENCIAS), 'W'),
                    'select_freq'),
    ]
    return ui.secao(
        'Evolução por UF', 'Público ao longo do tempo nas UFs escolhidas.',
        ui.grade([(ui.cartao('Público por UF', ui.grafico('animation_graph', 'alto'),
                             id_subtitulo='subtitulo_animacao'), {'lg': 12})]),
        controles=controles,
    )


def _secao_comparacao():
    controles = [
        ui.controle('UF A', ui.dropdown('select_estado1', _opcoes(d.UFS), UF_A), 'select_estado1'),
        ui.controle('UF B', ui.dropdown('select_estado2', _opcoes(d.UFS), UF_B), 'select_estado2'),
    ]
    return ui.secao(
        'Comparação direta', 'Qual das duas UFs teve mais público em cada mês, e como cada uma variou.',
        ui.grade([
            (html.Div([ui.kpi('card1_indicators'), ui.kpi('card2_indicators')], className='ds-pilha'),
             {'lg': 3, 'md': 12}),
            (ui.cartao('Diferença mensal de público', ui.grafico('direct_comparison_graph', 'padrao'),
                       id_subtitulo='desc_comparison'), {'lg': 9, 'md': 12}),
        ]),
        controles=controles,
    )


def _secao_rankings():
    return ui.secao(
        'Rankings do período', 'Os 10 maiores por público no período escolhido.',
        ui.grade([
            (ui.cartao('Filmes', ui.grafico('rank_filmes', 'alto'), subtitulo='Pela fonte escolhida'), {'lg': 4}),
            (ui.cartao('Distribuidoras', ui.grafico('rank_distribuidoras', 'alto'),
                       subtitulo='Sempre pela fonte distribuidoras',
                       nota='Na co-distribuição, cada distribuidora recebe o público integral.'), {'lg': 4}),
            (ui.cartao('Exibidoras', ui.grafico('rank_exibidoras', 'alto'),
                       subtitulo='Sempre pela fonte exibidoras', nota='Por CNPJ; redes com vários CNPJs aparecem separadas.'),
             {'lg': 4}),
        ]),
    )


def montar():
    ultimo = {f: formatos.data(v) for f, v in d.ULTIMO_DIA.items()}
    return html.Div(className='ds-app', children=[
        dcc.Store(id='dataset', data={'anos': [d.ANO_MIN, d.ANO_MAX]}),
        dcc.Store(id='controller', data={'play': False}),
        dcc.Store(id='serie_cores', data=atribuir_cores({}, UFS_INICIAIS + [UF_A, UF_B])),
        dcc.Store(id='tema_aplicado'),
        dcc.Interval(id='interval', interval=3000),
        ui.cabecalho(
            'Bilheteria diária do cinema no Brasil',
            f'Público por dia, {d.ANO_MIN}–{d.ANO_MAX} · dados abertos da ANCINE',
            dbc.Switch(id='tema', label='Modo escuro', value=MODO_PADRAO == 'escuro', persistence=True,
                       className='ds-interruptor'),
        ),
        ui.abas('abas', 'visao', [
            ('visao', 'Visão geral', [
                _filtros_globais(),
                html.Main(className='ds-pagina', children=[
                    _secao_panorama(), _secao_regiao(), _secao_ufs(), _secao_comparacao(), _secao_rankings(),
                ]),
            ]),
            ('recuperacao', 'Recuperação pós-pandemia', layout_recuperacao.montar()),
        ]),
        ui.rodape([
            'Fonte: ANCINE, Bilheteria diária de obras por distribuidoras e por exibidoras (dados abertos).',
            f"Dados até {ultimo['DISTRIBUIDOR']} (distribuidoras) e {ultimo['EXIBIDORA']} (exibidoras). "
            'As duas fontes descrevem as mesmas exibições e nunca são somadas; a fonte exibidora só tem '
            'cobertura nacional a partir de 2017.',
        ]),
    ])
