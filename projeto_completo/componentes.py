"""Componentes de interface reutilizáveis. Só estrutura e classes CSS: nenhum valor visual aqui
(cores, fontes e espaços vêm de assets/styles.css, que lê os tokens)."""
from dash import dcc, html
import dash_bootstrap_components as dbc

from design import formatos
from design.tokens import GRAFICO, TRANSPARENTE

CONFIG_GRAFICO = {'displayModeBar': False, 'showTips': False, 'responsive': True}
# figura inicial (antes do 1º callback): sem os eixos 0–6 padrão do Plotly
FIGURA_INICIAL = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False},
                                         'paper_bgcolor': TRANSPARENTE, 'plot_bgcolor': TRANSPARENTE,
                                         'margin': GRAFICO['margem']}}


def cabecalho(titulo, subtitulo, acoes):
    return html.Header(className='ds-cabecalho', children=html.Div(className='ds-pagina ds-cabecalho__conteudo', children=[
        html.Div([
            html.H1([html.I(className='fa fa-film ds-cabecalho__icone', **{'aria-hidden': 'true'}), titulo],
                    className='ds-titulo-pagina'),
            html.P(subtitulo, className='ds-cabecalho__subtitulo'),
        ]),
        html.Div(acoes, className='ds-cabecalho__acoes'),
    ]))


def controle(rotulo, componente, id_rotulo=None, ajuda=None, largura='auto'):
    """Rótulo + controle + ajuda opcional, sempre na mesma anatomia."""
    return html.Div(className=f'ds-controle ds-controle--{largura}', children=[
        html.Label(rotulo, htmlFor=id_rotulo, className='ds-controle__rotulo'),
        componente,
        html.Small(ajuda, className='ds-controle__ajuda') if ajuda else None,
    ])


def dropdown(id_, opcoes, valor, multi=False, **kw):
    return dcc.Dropdown(id=id_, options=opcoes, value=valor, clearable=False, multi=multi,
                        searchable=multi, className='ds-dropdown', **kw)


def segmentado(id_, opcoes, valor):
    """Escolha única em botões segmentados (substitui o rádio solto)."""
    return dbc.RadioItems(id=id_, options=opcoes, value=valor, inline=True, className='ds-segmentado',
                          inputClassName='btn-check', labelClassName='ds-segmentado__opcao',
                          labelCheckedClassName='ds-segmentado__opcao--ativa')


def barra_filtros(controles, rotulo='Filtros globais', nota=None):
    """Faixa de filtros acima de tudo o que ela controla."""
    return html.Section(className='ds-filtros', **{'aria-label': rotulo}, children=html.Div(className='ds-pagina', children=[
        html.Div(controles, className='ds-filtros__linha'),
        html.P(nota, className='ds-nota') if nota else None,
    ]))


def secao(titulo, descricao, conteudo, controles=None, escopo=None):
    """Seção da página: título, descrição, controles próprios (com escopo declarado) e cartões."""
    return html.Section(className='ds-secao', children=[
        html.Div(className='ds-secao__topo', children=[
            html.Div([html.H2(titulo, className='ds-titulo-secao'),
                      html.P(descricao, className='ds-secao__descricao')]),
            html.Div(controles, className='ds-secao__controles') if controles else None,
        ]),
        html.P(escopo, className='ds-nota ds-secao__escopo') if escopo else None,
        conteudo,
    ])


def grade(colunas):
    """Linha da grade de 12 colunas. colunas = [(componente, {'lg': 6, ...})]."""
    return dbc.Row([dbc.Col(c, xs=12, **tam, className='ds-col') for c, tam in colunas],
                   className='ds-grade g-3')


def _texto(conteudo, id_, classe):
    """Parágrafo opcional: fixo (conteudo), preenchido por callback (id_) ou ausente."""
    if not (conteudo or id_):
        return None
    return html.P(conteudo, className=classe, **({'id': id_} if id_ else {}))


def cartao(titulo, corpo, subtitulo=None, id_subtitulo=None, nota=None, id_nota=None):
    return html.Article(className='ds-cartao', children=[
        html.Header(className='ds-cartao__cabecalho', children=[
            html.H3(titulo, className='ds-titulo-cartao'),
            _texto(subtitulo, id_subtitulo, 'ds-cartao__subtitulo'),
        ]),
        html.Div(corpo, className='ds-cartao__corpo'),
        _texto(nota, id_nota, 'ds-nota ds-cartao__nota'),
    ])


def grafico(id_, altura='padrao', rotulo=None):
    """Gráfico com altura da escala de tokens e carregamento que mantém o desenho anterior esmaecido."""
    return dcc.Loading(
        dcc.Graph(id=id_, figure=FIGURA_INICIAL, config=CONFIG_GRAFICO, className='ds-grafico',
                  style={'height': f"{GRAFICO['altura'][altura]}px"},
                  **({'aria-label': rotulo} if rotulo else {})),
        type='dot', delay_show=GRAFICO['carregando_atraso_ms'], className='ds-carregando',
        overlay_style={'visibility': 'visible', 'opacity': GRAFICO['carregando_opacidade']},
    )


def kpi(id_):
    """Contêiner do cartão de KPI (o conteúdo vem de kpi_conteudo, preenchido por callback)."""
    return html.Article(id=id_, className='ds-cartao ds-kpi', **{'aria-live': 'polite'})


def kpi_conteudo(rotulo, cor_identidade, valor, referencia, ano_ref, nota):
    """Corpo do KPI: rótulo com marca de cor da UF, valor, delta com ícone e cor de estado, nota.

    data-valor / data-referencia guardam os números exatos (usados por testes/verificar_numeros.py).
    """
    variacao = (valor - referencia) / referencia if referencia else 0
    estado = 'positivo' if variacao > 0 else 'negativo' if variacao < 0 else 'neutro'
    icone = {'positivo': 'fa-arrow-up', 'negativo': 'fa-arrow-down', 'neutro': 'fa-minus'}[estado]
    return html.Div(className='ds-kpi__interno', **{'data-valor': str(valor), 'data-referencia': str(referencia)}, children=[
        html.P(className='ds-kpi__rotulo', children=[
            html.Span(className='ds-marca', style={'backgroundColor': cor_identidade}, **{'aria-hidden': 'true'}),
            rotulo]),
        html.P(formatos.inteiro(valor), className='ds-kpi__valor'),
        html.P(className=f'ds-kpi__delta ds-estado--{estado}', children=[
            html.I(className=f'fa {icone}', **{'aria-hidden': 'true'}),
            html.Span(f' {formatos.percentual(variacao)} '),
            html.Span(f'vs. {ano_ref}', className='ds-kpi__referencia'),
        ]),
        html.P(nota, className='ds-nota'),
    ])


def kpi_simples(rotulo, valor, detalhe, estado=None, icone=None):
    """KPI sem identidade de série: rótulo, valor e uma linha de detalhe (com ícone de estado, se houver)."""
    linha = [html.I(className=f'fa {icone}', **{'aria-hidden': 'true'}), html.Span(f' {detalhe}')] if icone else detalhe
    return html.Div(className='ds-kpi__interno', children=[
        html.P(rotulo, className='ds-kpi__rotulo'),
        html.P(valor, className='ds-kpi__valor'),
        html.P(linha, className=f'ds-kpi__delta ds-estado--{estado or "neutro"}'),
    ])


def abas(id_, valor, paginas):
    """Páginas do dashboard. paginas = [(valor, rótulo, conteúdo)]."""
    return dcc.Tabs(id=id_, value=valor, className='ds-abas', parent_className='ds-abas__pai',
                    content_className='ds-abas__conteudo', persistence=True, children=[
        dcc.Tab(label=rotulo, value=v, className='ds-aba', selected_className='ds-aba--ativa', children=conteudo)
        for v, rotulo, conteudo in paginas])


def kpi_vazio(mensagem):
    return html.Div(className='ds-kpi__interno ds-kpi--vazio', children=html.P(mensagem, className='ds-nota'))


def botao_icone(id_, icone, rotulo):
    return html.Button(html.I(className=f'fa {icone}', **{'aria-hidden': 'true'}), id=id_, n_clicks=0,
                       className='ds-botao-icone', title=rotulo, **{'aria-label': rotulo})


def rodape(linhas):
    return html.Footer(className='ds-rodape', children=html.Div(className='ds-pagina', children=[
        html.P(l, className='ds-nota') for l in linhas]))
