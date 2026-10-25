"""Construtores de figura. Todo gráfico do dashboard sai daqui, com a mesma anatomia:
template do Design System, legenda acima da área de plotagem (só com 2+ séries), eixo de valor
com marcas compactas pt-BR, tooltip padronizado e alturas da escala de tokens.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from design import formatos, tema_plotly
from design.tokens import BORDA, CORES, GRAFICO, LIMITES, RAIO

# ---------------------------------------------------------------- cor por entidade


def atribuir_cores(mapa, entidades):
    """Mantém a cor de quem continua visível, libera a de quem saiu e dá a primeira livre a quem entrou.

    `mapa` é {entidade: índice de slot}. A cor segue a entidade, nunca a posição na lista.
    """
    slots = len(CORES['claro']['categorica'])
    novo = {e: i for e, i in (mapa or {}).items() if e in entidades}
    for e in entidades:
        if e not in novo:
            livres = [i for i in range(slots) if i not in novo.values()]
            novo[e] = livres[0] if livres else len(novo) % slots
    return novo


def cor_entidade(entidade, mapa, modo):
    """Cor do slot atribuído à entidade (o chamador garante a atribuição com atribuir_cores)."""
    paleta = CORES[modo]['categorica']
    return paleta[mapa[entidade] % len(paleta)]


# ---------------------------------------------------------------- base


def _base(modo, altura, legenda=False):
    fig = go.Figure()
    margem = dict(GRAFICO['margem'])
    if legenda:
        margem['t'] = GRAFICO['margem_legenda']
    fig.update_layout(template=tema_plotly.NOME[modo], height=altura, margin=margem, showlegend=legenda)
    return fig


# formato -> (rótulo em texto, formato d3 do tooltip, multiplicador do eixo)
FORMATOS = {
    'inteiro': (formatos.inteiro, formatos.HOVER_INTEIRO, 1),
    'compacto': (lambda v: formatos.compacto(v, fixo=True), formatos.HOVER_INTEIRO, 1),
    'decimal': (formatos.decimal, formatos.HOVER_DECIMAL, 1),
    'pct': (lambda v: formatos.percentual(v, sinal=False), formatos.HOVER_PCT, 100),
}


def _eixo_valor(fig, eixo, vmin, vmax, com_sinal=False, formato='inteiro'):
    escala = FORMATOS[formato][2]
    vals, textos, faixa = formatos.marcas_eixo(vmin * escala, vmax * escala, GRAFICO['ticks'], com_sinal)
    if escala != 1:   # eixo percentual: marcas redondas em pontos percentuais
        vals, faixa = [v / escala for v in vals], [f / escala for f in faixa]
        textos = [f"{formatos.decimal(v * escala, 0)}%" for v in vals]
    fig.update_layout(**{eixo: dict(tickvals=vals, ticktext=textos, range=faixa)})


def _eixo_tempo(fig, granularidade, n_anos=0):
    if granularidade == 'ano':
        # anos inteiros: passo de 1 em recortes curtos, de 2 nos longos (nunca marcas fracionárias)
        fig.update_xaxes(type='linear', tickformat='d', hoverformat='d', tick0=0,
                         dtick=1 if n_anos <= GRAFICO['anos_passo_1'] else 2)
    else:
        fig.update_xaxes(type='date', tickformatstops=formatos.TICKS_DATA,
                         hoverformat=formatos.DATA_MES if granularidade == 'MS' else formatos.DATA_DIA)


def vazio(modo, altura, mensagem):
    """Estado vazio: mesma altura do gráfico, mensagem centralizada, sem eixos."""
    fig = _base(modo, altura)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=mensagem, x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False,
                       font=dict(size=GRAFICO['fonte_rotulo'], color=CORES[modo]['texto_mudo']))
    return fig


# ---------------------------------------------------------------- formas


def linhas(series, modo, altura, granularidade='ano', formato='inteiro'):
    """Linhas temporais. series = [{'nome', 'x', 'y', 'cor'}]; granularidade: 'ano', 'D', 'W' ou 'MS'."""
    hover = FORMATOS[formato][1]
    fig = _base(modo, altura, legenda=len(series) > 1)
    vmax, anos = 0, set()
    for s in series:
        fig.add_trace(go.Scatter(
            x=s['x'], y=s['y'], name=s['nome'], mode='lines',
            line=dict(color=s['cor'], width=GRAFICO['linha'], shape='linear'),
            hovertemplate=f"{s['nome']}: %{{y:{hover}}}<extra></extra>",
        ))
        if len(s['y']):
            vmax = max(vmax, float(pd.Series(s['y']).max()))
        anos.update(list(s['x']))
    _eixo_tempo(fig, granularidade, len(anos))
    _eixo_valor(fig, 'yaxis', 0, vmax, formato=formato)
    fig.update_layout(hovermode='x unified')
    return fig


def barras_horizontais(chaves, nomes, valores, modo, altura, cor=None, formato='inteiro', referencia=None):
    """Barras horizontais de uma série (cor única: a série principal), maior no topo.

    Anatomia de ranking em lista: cada linha tem, acima da barra, o nome à esquerda e o valor à
    direita; a barra fica logo abaixo. Nenhum texto disputa espaço com barras vizinhas, em qualquer
    largura de cartão. chaves identificam as categorias (evita fundir nomes abreviados iguais);
    o nome completo vai para o tooltip. referencia = {'valor', 'nome'}: linha vertical de comparação
    (ex.: média nacional); barras abaixo dela ficam na cor de destaque.
    """
    c = CORES[modo]
    rotulo, hover, _ = FORMATOS[formato]
    chaves, nomes, valores = list(chaves), list(nomes), list(valores)
    cor = cor or c['serie_principal']
    if referencia is not None:
        cor = [c['serie_comparativa'] if v < referencia['valor'] else c['serie_principal'] for v in valores]
    vmax = max(valores) if valores else 1
    fig = _base(modo, altura)
    fig.add_trace(go.Bar(
        y=chaves, x=valores, orientation='h',
        marker=dict(color=cor, cornerradius=RAIO['barra'], line=dict(width=0)),
        customdata=[[n] for n in nomes],
        hovertemplate=f"%{{customdata[0]}}: %{{x:{hover}}}<extra></extra>",
    ))
    if referencia is not None:
        fig.add_vline(x=referencia['valor'], line=dict(color=c['referencia'], width=BORDA['fina'], dash='dot'))
    # espessura fixa em px: a folga entre barras sai da altura disponível por categoria
    faixa_px = (altura - GRAFICO['margem']['t'] - GRAFICO['margem']['b']) / max(len(chaves), 1)
    folga = min(max(1 - GRAFICO['barra_espessura'] / faixa_px, 0.1), 0.9)
    acima = GRAFICO['barra_espessura'] / 2 + GRAFICO['afastamento_rotulo'] / 2
    fonte = dict(size=GRAFICO['fonte_rotulo'])
    # rótulos posicionados pelo índice da categoria: uma chave com cara de número ("6000002")
    # seria lida como coordenada e esticaria o eixo
    for i, (nome, valor) in enumerate(zip(nomes, valores)):
        comum = dict(y=i, xref='x', yref='y', yanchor='bottom', yshift=acima, showarrow=False)
        fig.add_annotation(x=0, xanchor='left', text=formatos.abreviar(nome, GRAFICO['nome_max']),
                           font=dict(fonte, color=c['texto_sec']), **comum)
        fig.add_annotation(x=vmax, xanchor='right', text=rotulo(valor),
                           font=dict(fonte, color=c['texto']), **comum)
    # categoria sempre: chaves numéricas (ex.: código de grupo exibidor) não podem virar eixo numérico
    fig.update_yaxes(visible=False, type='category', categoryorder='array', categoryarray=chaves,
                     range=[-0.5, len(chaves) - 0.5])
    # todo valor já está rotulado: o eixo de valor seria redundante (e se encavala em cartões estreitos)
    fig.update_xaxes(visible=False, range=[0, vmax])
    fig.update_layout(bargap=folga, hovermode='closest')
    return fig


def colunas_divergentes(datas, valores, positivo, negativo, modo, altura):
    """Colunas mensais acima/abaixo de zero: cada lado na cor da sua entidade.

    positivo / negativo = {'nome', 'cor'}: quem teve mais público quando o valor é > 0 / <= 0.
    """
    c = CORES[modo]
    serie = pd.Series(list(valores), index=pd.to_datetime(list(datas)))
    fig = _base(modo, altura, legenda=True)
    for lado, mascara in ((positivo, serie > 0), (negativo, serie <= 0)):
        parte = serie.where(mascara)
        fig.add_trace(go.Bar(
            x=serie.index, y=parte.values, name=f"{lado['nome']} com mais público",
            marker=dict(color=lado['cor'], line=dict(width=0)),
            customdata=[formatos.inteiro(abs(v)) if pd.notna(v) else '' for v in parte.values],
            hovertemplate=f"{lado['nome']}: +%{{customdata}}<extra></extra>",
        ))
    _eixo_tempo(fig, 'MS')
    _eixo_valor(fig, 'yaxis', float(serie.min()) if len(serie) else 0,
                float(serie.max()) if len(serie) else 1, com_sinal=True)
    fig.update_yaxes(zeroline=True, zerolinecolor=c['texto_mudo'], zerolinewidth=BORDA['fina'])
    fig.update_layout(barmode='relative', bargap=GRAFICO['coluna_folga'], hovermode='x unified')
    return fig


def colunas(categorias, valores, modo, altura, formato='inteiro', destaques=(), detalhe=None):
    """Colunas verticais de uma série (anos, dias, faixas), na cor principal.

    Rótulo seletivo: só as colunas em `destaques` (na cor de destaque) levam o valor no topo; o eixo
    e o tooltip carregam o resto, o que mantém o gráfico legível em qualquer largura.
    detalhe = texto extra por coluna no tooltip (ex.: o maior filme do ano).
    """
    c = CORES[modo]
    rotulo, hover, _ = FORMATOS[formato]
    cats, vals = [str(x) for x in categorias], [float(v) for v in valores]
    marcados = {str(x) for x in destaques}
    # muitas colunas: rótulo na vertical, para caber na largura da própria coluna em qualquer tela
    vertical = len(cats) > GRAFICO['anos_passo_1']
    fig = _base(modo, altura)
    fig.add_trace(go.Bar(
        x=cats, y=vals, marker=dict(color=[c['serie_comparativa'] if k in marcados else c['serie_principal'] for k in cats],
                                    cornerradius=RAIO['barra'], line=dict(width=0)),
        text=[rotulo(v) if k in marcados else '' for k, v in zip(cats, vals)], textposition='outside', cliponaxis=False,
        constraintext='none',   # o Plotly encolheria o rótulo que acha apertado: todos ficam no mesmo corpo
        textangle=-90 if vertical else 0,
        textfont=dict(size=GRAFICO['fonte_rotulo'], color=c['texto']),
        customdata=[[d] for d in (detalhe or [''] * len(cats))],
        hovertemplate=f"%{{x}}: %{{y:{hover}}}%{{customdata[0]}}<extra></extra>",
    ))
    fig.update_xaxes(type='category', showgrid=False)
    if all(k.isdigit() for k in cats) and len(cats) > GRAFICO['anos_passo_1']:
        # muitos anos: um rótulo a cada dois (sempre o último), como no eixo das linhas
        fig.update_xaxes(tickmode='array', tickvals=cats[::-2][::-1])
    folga = GRAFICO['folga_topo_vertical'] if vertical else GRAFICO['folga_topo']
    _eixo_valor(fig, 'yaxis', 0, max(vals, default=1) * folga, formato=formato)
    fig.update_layout(bargap=GRAFICO['coluna_ano_folga'], hovermode='closest')
    return fig


def mapa_calor(matriz, modo, altura, meio=1.0):
    """Mapa de calor divergente em torno de `meio` (ex.: índice 1 = média): abaixo frio, acima quente.

    matriz: DataFrame (linhas = categorias do eixo y, colunas = eixo x). O valor vai escrito na célula.
    """
    c = CORES[modo]
    z = matriz.to_numpy(dtype=float)
    lim = float(np.nanmax(np.abs(z - meio))) or 1
    texto = [[formatos.decimal(v, 2) if pd.notna(v) else '' for v in linha] for linha in z]
    fig = _base(modo, altura)
    fig.add_trace(go.Heatmap(
        z=z, x=[str(x) for x in matriz.columns], y=[str(y) for y in matriz.index], zmin=meio - lim, zmax=meio + lim,
        colorscale=[[0, c['divergente_baixo']], [0.5, c['divergente_meio']], [1, c['divergente_alto']]],
        showscale=False, xgap=GRAFICO['celula_folga'], ygap=GRAFICO['celula_folga'], text=texto,
        texttemplate='%{text}', textfont=dict(size=GRAFICO['fonte_rotulo'], color=c['texto']),
        hovertemplate='%{y} · %{x}: %{text}<extra></extra>',
    ))
    fig.update_xaxes(type='category', showgrid=False, showline=False, side='top')
    fig.update_yaxes(type='category', showgrid=False, showline=False, autorange='reversed')
    fig.update_layout(hovermode='closest')
    return fig


MAX_UFS = LIMITES['max_ufs']
