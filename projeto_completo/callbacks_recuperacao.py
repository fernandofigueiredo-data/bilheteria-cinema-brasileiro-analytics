"""Callbacks da aba "Recuperação pós-pandemia": ano de comparação + tema -> dados_recuperacao -> graficos."""
from dash import Input, Output

import componentes as ui
import dados_recuperacao as r
import graficos as g
from app import app
from design import formatos
from design.tokens import GRAFICO, modo

ALT = GRAFICO['altura']
ANO = Input('ano_comparacao', 'value')
TEMA = Input('tema', 'value')
BASE = r.ANO_BASE


def _pct(v):
    return formatos.percentual(v, sinal=False)


def _estado(fracao):
    return ('negativo', 'fa-arrow-down') if fracao < 1 else ('positivo', 'fa-arrow-up')


@app.callback(Output('kpi_rec_ano', 'children'), Output('kpi_rec_2026', 'children'), Output('kpi_por_sessao', 'children'),
              Output('g_jan_set', 'figure'), ANO, TEMA)
def principal(ano, escuro):
    a = r.anual()
    o, indice = r.oferta_demanda()
    ultimo = int(a.index.max())
    k1 = ui.kpi_simples(f'Público em {ano} como % de {BASE}', _pct(a.loc[ano, 'pct_ano']),
                        f"{formatos.compacto(a.loc[ano, 'publico'], fixo=True)} contra {formatos.compacto(a.loc[BASE, 'publico'], fixo=True)}",
                        *_estado(a.loc[ano, 'pct_ano']))
    k2 = ui.kpi_simples(f'Janeiro a setembro de {ultimo} como % de {BASE}', _pct(a.loc[ultimo, 'pct_jan_set']),
                        f"{formatos.compacto(a.loc[ultimo, 'jan_set'], fixo=True)} contra {formatos.compacto(a.loc[BASE, 'jan_set'], fixo=True)}",
                        *_estado(a.loc[ultimo, 'pct_jan_set']))
    k3 = ui.kpi_simples(f'Público por sessão em {ano}', formatos.decimal(o.loc[ano, 'por_sessao']),
                        f"{formatos.decimal(o.loc[BASE, 'por_sessao'])} em {BASE}, com {_pct(indice.loc[ano, 'REGISTROS'])} "
                        f"das sessões de {BASE}", *_estado(o.loc[ano, 'por_sessao'] / o.loc[BASE, 'por_sessao']))
    fig = g.colunas(a.index, a['jan_set'], modo(escuro), ALT['padrao'], formato='compacto', destaques=(BASE, ano, ultimo))
    return k1, k2, k3, fig


@app.callback(Output('g_filmes_grandes', 'figure'), Output('g_top10_demais', 'figure'), Output('g_maiores_base', 'figure'),
              Output('g_maiores_ano', 'figure'), Output('sub_maiores_ano', 'children'), ANO, TEMA)
def sucessos(ano, escuro):
    m, c = modo(escuro), r.concentracao().loc[:r.ANOS_COMPARACAO[-1]]
    cores = g.CORES[m]
    grandes = g.colunas(c.index, c['grandes'], m, ALT['padrao'], destaques=(BASE, ano))
    partes = g.linhas([{'nome': '10 maiores filmes', 'x': c.index, 'y': c['top10'], 'cor': cores['serie_principal']},
                       {'nome': 'demais filmes', 'x': c.index, 'y': c['demais'], 'cor': cores['serie_comparativa']}],
                      m, ALT['padrao'], 'ano')
    rank = [r.maiores_filmes(a) for a in (BASE, ano)]
    figs = [g.barras_horizontais(f.CHAVE, f.NOME, f.PUBLICO, m, ALT['alto']) for f in rank]
    return grandes, partes, figs[0], figs[1], f'Público em {ano} · fonte distribuidoras'


@app.callback(Output('g_br_pct', 'figure'), Output('g_br_publico', 'figure'), ANO, TEMA)
def brasileiro(ano, escuro):
    m, b = modo(escuro), r.brasileiro()
    detalhe = [f"<br>maior: {n} ({formatos.compacto(p, fixo=True)})" for n, p in zip(b['maior'], b['maior_publico'])]
    pct = g.colunas(b.index, b['pct'], m, ALT['padrao'], formato='pct', destaques=(BASE, ano), detalhe=detalhe)
    publico = g.colunas(b.index, b['publico_br'], m, ALT['padrao'], formato='compacto', destaques=(BASE, ano), detalhe=detalhe)
    return pct, publico


@app.callback(Output('g_indice_oferta', 'figure'), Output('g_por_sessao', 'figure'), Output('g_vazias_ano', 'figure'),
              Output('g_vazias_faixa', 'figure'), Output('sub_vazias_faixa', 'children'), ANO, TEMA)
def oferta(ano, escuro):
    m = modo(escuro)
    cores = g.CORES[m]['categorica']
    o, indice = r.oferta_demanda()
    series = [{'nome': n, 'x': indice.index, 'y': indice[c], 'cor': cores[i]}
              for i, (c, n) in enumerate([('SALAS', 'salas'), ('REGISTROS', 'sessões'), ('PUBLICO', 'público')])]
    linhas = g.linhas(series, m, ALT['padrao'], 'ano', formato='pct')
    por_sessao = g.colunas(o.index, o['por_sessao'], m, ALT['padrao'], formato='decimal', destaques=(BASE, ano))
    vazias = g.colunas(o.index, o['pct_vazias'], m, ALT['padrao'], formato='pct', destaques=(BASE, ano))
    f = r.faixas(ano)
    faixa = g.barras_horizontais(f.index, f.index.str[3:], f['pct_vazias'], m, ALT['padrao'], formato='pct')
    return linhas, por_sessao, vazias, faixa, f'% das sessões sem público em {ano} · fonte exibidoras'


@app.callback(Output('g_rec_uf', 'figure'), Output('sub_rec_uf', 'children'), Output('g_rec_regiao', 'figure'),
              Output('g_rec_lugar', 'figure'), Output('sub_rec_lugar', 'children'), ANO, TEMA)
def geografia(ano, escuro):
    m = modo(escuro)
    media = {'valor': r.anual().loc[ano, 'pct_ano'], 'nome': 'Brasil'}
    figs = []
    for por, altura in (('UF', 'longo'), ('REGIÃO', 'compacto'), ('LUGAR', 'compacto')):
        t = r.recuperacao_local(ano, por).sort_values('pct')
        figs.append(g.barras_horizontais(t.index, t.index.str.title() if por != 'UF' else t.index, t['pct'], m,
                                         ALT[altura], formato='pct', referencia=media))
    lugar = r.recuperacao_local(ano, 'LUGAR')['salas']
    return (figs[0], f'{ano} como % de {BASE} · média do Brasil: {_pct(media["valor"])} · fonte distribuidoras',
            figs[1], figs[2], f"Salas em {ano}: {formatos.inteiro(lugar['capital'])} nas capitais e "
                              f"{formatos.inteiro(lugar['interior'])} no interior")


@app.callback(Output('g_top5', 'figure'), Output('g_lideres', 'figure'), Output('g_redes', 'figure'),
              Output('sub_redes', 'children'), ANO, TEMA)
def empresas(ano, escuro):
    m = modo(escuro)
    cores = g.CORES[m]
    top5, serie, nomes = r.distribuidoras()
    fig_top5 = g.linhas([{'nome': '5 maiores', 'x': top5.index, 'y': top5, 'cor': cores['serie_principal']}],
                        m, ALT['padrao'], 'ano', formato='pct')
    lideres = g.linhas([{'nome': formatos.abreviar(nomes[k].title(), 22), 'x': serie.index, 'y': serie[k],
                         'cor': cores['categorica'][i]} for i, k in enumerate(serie.columns)], m, ALT['padrao'], 'ano', formato='pct')
    rd = r.recuperacao_redes(ano).sort_values('pct')
    o, _ = r.oferta_demanda()
    media = {'valor': o.loc[ano, 'PUBLICO'] / o.loc[BASE, 'PUBLICO'], 'nome': 'mercado'}
    redes = g.barras_horizontais(rd.CHAVE, rd.NOME.str.title(), rd['pct'], m, ALT['alto'], formato='pct', referencia=media)
    return fig_top5, lideres, redes, f'Público de {ano} como % de {BASE} · mercado: {_pct(media["valor"])} · fonte exibidoras'


@app.callback(Output('g_semana1', 'figure'), Output('g_pico', 'figure'), ANO, TEMA)
def vida(ano, escuro):
    m, v = modo(escuro), r.vida()
    semana = g.linhas([{'nome': '7 primeiros dias', 'x': v.index, 'y': v['semana1'], 'cor': g.CORES[m]['serie_principal']}],
                      m, ALT['padrao'], 'ano', formato='pct')
    pico = g.colunas(v.index, v['pico'], m, ALT['padrao'], destaques=(BASE, ano),
                     detalhe=[f'<br>{formatos.inteiro(n)} filmes' for n in v['filmes']])
    return semana, pico


@app.callback(Output('g_dia_semana', 'figure'), Output('sub_dia_semana', 'children'), Output('g_faixa', 'figure'),
              Output('sub_faixa', 'children'), Output('g_sazonal', 'figure'), ANO, TEMA)
def quando(ano, escuro):
    m = modo(escuro)
    s = r.dia_da_semana(ano)
    dias = g.colunas(s.index, s['indice'], m, ALT['padrao'], destaques=('sáb',),
                     detalhe=[f'<br>{formatos.inteiro(p)} por dia' for p in s['mean']])
    f = r.faixas(ano)
    faixa = g.colunas(f.index.str[3:], f['por_sessao'], m, ALT['padrao'], formato='decimal', destaques=('18h–21h',))
    sazonal = g.mapa_calor(r.sazonalidade(), m, ALT['alto'])
    return (dias, f'Índice: média dos dias = 100 · {ano - 2} a {ano} · fonte distribuidoras', faixa,
            f'Espectadores por sessão em {ano} · fonte exibidoras', sazonal)


@app.callback(Output('g_dub_ano', 'figure'), Output('g_dub_regiao', 'figure'), Output('sub_dub_regiao', 'children'), ANO, TEMA)
def dublado(ano, escuro):
    m = modo(escuro)
    cores = g.CORES[m]
    du = r.dublado()
    anos = g.linhas([{'nome': '% do público', 'x': du.index, 'y': du['pct_publico'], 'cor': cores['serie_principal']},
                     {'nome': '% das sessões', 'x': du.index, 'y': du['pct_sessoes'], 'cor': cores['serie_comparativa']}],
                    m, ALT['padrao'], 'ano', formato='pct')
    reg = r.dublado_regiao(ano)
    regiao = g.barras_horizontais(reg.index, reg.index.str.title(), reg.values, m, ALT['padrao'], formato='pct')
    return anos, regiao, f'% do público de filmes estrangeiros em {ano} · fonte exibidoras'
