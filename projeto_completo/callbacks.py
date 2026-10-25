"""Callbacks: ligam controles -> dados.py -> graficos.py / componentes.py. Sem estilo nem cálculo aqui."""
import dash
from dash import Input, Output, State

import componentes as ui
import dados as d
import graficos as g
from app import app
from design import formatos
from design.tokens import GRAFICO, modo

ALT = GRAFICO['altura']
TEMA = Input('tema', 'value')
SEM_DADOS = 'Sem dados para este recorte.'

# Tema: aplica data-theme no <html>; o CSS troca as variáveis
app.clientside_callback(
    "function(escuro){document.documentElement.setAttribute('data-theme', escuro ? 'escuro' : 'claro'); return escuro;}",
    Output('tema_aplicado', 'data'), TEMA)


@app.callback(
    Output('serie_cores', 'data'), Output('select_estados0', 'value'),
    Input('select_estados0', 'value'), Input('select_estado1', 'value'), Input('select_estado2', 'value'),
    State('serie_cores', 'data'))
def cores_ufs(estados, uf_a, uf_b, mapa):
    """Limita a seleção a MAX_UFS e mantém a cor de cada UF estável entre os visuais."""
    estados = list(estados or [])[:g.MAX_UFS]
    visiveis = list(dict.fromkeys(estados + [uf_a, uf_b]))
    return g.atribuir_cores(mapa, visiveis), estados


def _cores(mapa, ufs):
    return g.atribuir_cores(mapa, list(dict.fromkeys(ufs)))


@app.callback(Output('static-maxmin', 'figure'), Input('dataset', 'data'), Input('select_fonte', 'value'), TEMA)
def maxmin(data, fonte, escuro):
    m = modo(escuro)
    c = g.CORES[m]
    final_df = d.maximos_minimos(fonte, data['anos'])
    if final_df.empty:
        return g.vazio(m, ALT['compacto'], SEM_DADOS)
    return g.linhas([
        {'nome': 'Máximo', 'x': final_df.index, 'y': final_df['Máximo'], 'cor': c['serie_principal']},
        {'nome': 'Mínimo', 'x': final_df.index, 'y': final_df['Mínimo'], 'cor': c['serie_comparativa']},
    ], m, ALT['compacto'], 'ano')


@app.callback(
    Output('regiaobar_graph', 'figure'), Output('estadobar_graph', 'figure'), Output('subtitulo_estados', 'children'),
    Input('select_fonte', 'value'), Input('select_ano', 'value'), Input('select_regiao', 'value'), TEMA)
def graph1(fonte, ano, regiao, escuro):
    m = modo(escuro)
    dff_regiao, dff_estado = d.por_regiao(fonte, ano, regiao)
    figs = []
    for df, col in ((dff_regiao, 'REGIÃO'), (dff_estado, 'UF')):
        figs.append(g.barras_horizontais(df[col], df[col], df['PUBLICO'], m, ALT['alto'])
                    if len(df) else g.vazio(m, ALT['alto'], SEM_DADOS))
    return figs[0], figs[1], f'{regiao.title()} · {ano}'


@app.callback(
    Output('animation_graph', 'figure'), Output('subtitulo_animacao', 'children'),
    Input('dataset', 'data'), Input('select_fonte', 'value'), Input('select_estados0', 'value'),
    Input('select_freq', 'value'), Input('serie_cores', 'data'), TEMA)
def animation(data, fonte, estados, freq, mapa, escuro):
    m = modo(escuro)
    subtitulo = f"Público {d.FREQUENCIAS[freq].lower()} · {data['anos'][0]}–{data['anos'][1]}"
    if not estados:
        return g.vazio(m, ALT['alto'], 'Escolha ao menos uma UF.'), subtitulo
    dff = d.serie_ufs(fonte, data['anos'], estados, freq)
    if dff.empty:
        return g.vazio(m, ALT['alto'], SEM_DADOS), subtitulo
    mapa = _cores(mapa, estados)
    series = [{'nome': uf, 'x': dff.loc[dff.UF == uf, 'DATA'], 'y': dff.loc[dff.UF == uf, 'PUBLICO'],
               'cor': g.cor_entidade(uf, mapa, m)} for uf in estados if (dff.UF == uf).any()]
    return g.linhas(series, m, ALT['alto'], freq), subtitulo


@app.callback(
    Output('direct_comparison_graph', 'figure'), Output('desc_comparison', 'children'),
    Input('dataset', 'data'), Input('select_fonte', 'value'), Input('select_estado1', 'value'),
    Input('select_estado2', 'value'), Input('serie_cores', 'data'), TEMA)
def comparison(data, fonte, est1, est2, mapa, escuro):
    m = modo(escuro)
    if est1 == est2:
        return g.vazio(m, ALT['padrao'], 'Escolha duas UFs diferentes.'), 'UF A e UF B são iguais.'
    df_final = d.comparacao_mensal(fonte, data['anos'], est1, est2)
    if df_final.empty:
        return g.vazio(m, ALT['padrao'], SEM_DADOS), ''
    mapa = _cores(mapa, [est1, est2])
    fig = g.colunas_divergentes(df_final['DATA'], df_final['DIF'],
                                {'nome': est1, 'cor': g.cor_entidade(est1, mapa, m)},
                                {'nome': est2, 'cor': g.cor_entidade(est2, mapa, m)}, m, ALT['padrao'])
    texto = (f'Público mensal de {est1} menos o de {est2}. Acima de zero, {est1} teve mais público no mês; '
             f'abaixo, {est2}.')
    return fig, texto


def indicador(data, fonte, estado, mapa, escuro):
    r = d.indicador_uf(fonte, data['anos'], estado)
    if r is None:
        return ui.kpi_vazio(f'{estado}: sem dados para este recorte.')
    parcial = f" (até {formatos.dia_mes(r['ultimo_dia'])})" if r['parcial'] else ''
    mapa = _cores(mapa, [estado])
    return ui.kpi_conteudo(
        f"{estado} · público em {r['ano']}{parcial}", g.cor_entidade(estado, mapa, modo(escuro)),
        r['valor'], r['referencia'], r['ano_ref'],
        f"Variação sobre {r['ano_ref']}, primeiro ano do recorte com cobertura plena da fonte.")


for n in (1, 2):
    app.callback(
        Output(f'card{n}_indicators', 'children'),
        Input('dataset', 'data'), Input('select_fonte', 'value'), Input(f'select_estado{n}', 'value'),
        Input('serie_cores', 'data'), TEMA,
    )(indicador)


@app.callback(
    Output('rank_filmes', 'figure'), Output('rank_distribuidoras', 'figure'), Output('rank_exibidoras', 'figure'),
    Input('dataset', 'data'), Input('select_fonte', 'value'), TEMA)
def rankings(data, fonte, escuro):
    m = modo(escuro)
    return [g.barras_horizontais(top.index, top['NOME'], top['PUBLICO'], m, ALT['alto'])
            if len(top) else g.vazio(m, ALT['alto'], SEM_DADOS) for top in d.top10(fonte, data['anos'])]


@app.callback(Output('dataset', 'data'), Input('rangeslider', 'value'), prevent_initial_call=True)
def range_slider(range):
    return {'anos': range}


@app.callback(
    Output('rangeslider', 'value'), Output('controller', 'data'),
    Input('interval', 'n_intervals'), Input('play-button', 'n_clicks'), Input('stop-button', 'n_clicks'),
    State('rangeslider', 'value'), State('controller', 'data'),
    prevent_initial_call=True)
def controller(n_intervals, play, stop, rangeslider, controller):
    trigg = dash.callback_context.triggered[0]["prop_id"]
    if 'play-button' in trigg and not controller["play"]:
        controller["play"] = True
        rangeslider = [d.ANO_MIN, d.ANO_MIN + 1]
    elif 'stop-button' in trigg:
        controller["play"] = False
    elif controller["play"]:
        if rangeslider[1] >= d.ANO_MAX:
            controller['play'] = False
        else:
            rangeslider[1] += 1
    else:
        return dash.no_update, dash.no_update
    return rangeslider, controller
