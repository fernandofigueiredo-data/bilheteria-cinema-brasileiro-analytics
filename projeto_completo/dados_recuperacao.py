"""Cálculos da aba "Recuperação pós-pandemia". Cada função responde a uma pergunta de ../analise.ipynb
e reproduz a mesma conta, a partir dos agregados gerados por ../pipeline/agregar_dashboard.py.

Fontes por pergunta (nunca somadas): distribuidor (dedup de co-distribuição) para séries longas e
filmes; exibidora (2017+) para tudo que é por sessão.
"""
import pandas as pd

import dados as d

ANO_BASE = 2019                       # último ano antes da pandemia
ANOS_COMPARACAO = list(range(2020, 2026))   # anos completos depois da pandemia
ANO_COMPARACAO_PADRAO = 2025
MES_JAN_SET = 9                       # último mês com dados em 2026 (comparação justa com o ano em curso)
ANOS_SAZONAIS = [2016, 2017, 2018, 2019, 2022, 2023, 2024, 2025]   # anos completos fora da pandemia
FILME_GRANDE = 1_000_000
DIAS_SEMANA = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

oferta = pd.read_csv('data_oferta.csv')
filmes = pd.read_csv('data_filmes_ano.csv', dtype={'CHAVE': str})
local = pd.read_csv('data_local.csv')
redes = pd.read_csv('data_redes.csv', dtype={'CHAVE': str})
vida_filmes = pd.read_csv('data_vida_filmes.csv', dtype={'CHAVE': str})
sessoes = pd.read_csv('data_sessoes.csv')
_dist = d.df_main[d.df_main.FONTE == 'DISTRIBUIDOR']


def anual():
    """Público por ano (ano completo e janeiro a setembro) e % de 2019. Fonte distribuidor."""
    a = _dist.groupby('ANO').agg(publico=('PUBLICO', 'sum'), dias=('DATA', 'nunique'))
    a['jan_set'] = _dist[_dist.DATA.dt.month <= MES_JAN_SET].groupby('ANO')['PUBLICO'].sum()
    a['pct_ano'] = a['publico'] / a.loc[ANO_BASE, 'publico']
    a['pct_jan_set'] = a['jan_set'] / a.loc[ANO_BASE, 'jan_set']
    return a


def oferta_demanda():
    """Salas, sessões, público por sessão e % sem público, por ano. Fonte exibidora (2017+)."""
    o = oferta[oferta.FONTE == 'EXIBIDORA'].set_index('ANO')
    o = o.assign(por_sessao=o.PUBLICO / o.REGISTROS, pct_vazias=o.REGISTROS_SEM_PUBLICO / o.REGISTROS)
    indice = o[['SALAS', 'REGISTROS', 'PUBLICO']] / o.loc[ANO_BASE, ['SALAS', 'REGISTROS', 'PUBLICO']]
    return o, indice


def faixas(ano):
    """Sessões, público por sessão e % sem público por faixa horária no ano. Fonte exibidora."""
    f = sessoes[sessoes.ANO == ano].groupby('FAIXA')[['SESSOES', 'SESSOES_SEM_PUBLICO', 'PUBLICO']].sum()
    return f.assign(por_sessao=f.PUBLICO / f.SESSOES, pct_vazias=f.SESSOES_SEM_PUBLICO / f.SESSOES)


def concentracao():
    """Por ano: nº de filmes, filmes com 1 mi+, público dos 10 maiores e dos demais. Fonte distribuidor."""
    f = filmes.sort_values(['ANO', 'PUBLICO'], ascending=[True, False])
    f['posicao'] = f.groupby('ANO').cumcount() + 1
    return f.groupby('ANO').apply(lambda g: pd.Series({
        'filmes': len(g), 'grandes': int((g.PUBLICO >= FILME_GRANDE).sum()),
        'top10': g.loc[g.posicao <= 10, 'PUBLICO'].sum(), 'demais': g.loc[g.posicao > 10, 'PUBLICO'].sum()}),
        include_groups=False)


def maiores_filmes(ano, n=10):
    """Os n filmes de maior público no ano (ordem crescente, para barras). Fonte distribuidor."""
    return filmes[filmes.ANO == ano].nlargest(n, 'PUBLICO').sort_values('PUBLICO')


def brasileiro():
    """Participação do filme brasileiro (CPB 'B') no público de filmes e o maior filme brasileiro do ano."""
    f = filmes.groupby(['ANO', 'TIPO_OBRA'])['PUBLICO'].sum().unstack(fill_value=0)
    maior = filmes[filmes.TIPO_OBRA == 'B'].sort_values('PUBLICO').groupby('ANO').last()
    return pd.DataFrame({'publico_br': f['B'], 'pct': f['B'] / (f['B'] + f['E']),
                         'maior': maior['NOME'], 'maior_publico': maior['PUBLICO']})


def recuperacao_local(ano, por):
    """Público do ano como fração do de 2019, por 'UF', 'REGIÃO' ou 'LUGAR'. Fonte distribuidor."""
    g = local[local.ANO.isin([ANO_BASE, ano])].groupby([por, 'ANO'])['PUBLICO'].sum().unstack()
    salas = local[local.ANO == ano].groupby(por)['SALAS'].sum()
    return pd.DataFrame({'base': g[ANO_BASE], 'atual': g[ano], 'pct': g[ano] / g[ANO_BASE],
                         'faltam': g[ANO_BASE] - g[ano], 'salas': salas})


def distribuidoras():
    """% das 5 maiores distribuidoras por ano e a fatia anual das líderes de 2019 e de 2025."""
    r = d.df_rank[(d.df_rank.TIPO == 'DISTRIBUIDORA') & (d.df_rank.ANO <= ANOS_COMPARACAO[-1])].copy()
    r['fatia'] = r.PUBLICO / r.groupby('ANO').PUBLICO.transform('sum')
    top5 = r.sort_values('PUBLICO', ascending=False).groupby('ANO').head(5).groupby('ANO')['fatia'].sum()
    lideres = pd.concat([r[r.ANO == a].nlargest(3, 'PUBLICO').CHAVE for a in (ANO_BASE, ANO_COMPARACAO_PADRAO)]).unique()
    serie = r[r.CHAVE.isin(lideres)].pivot_table(index='ANO', columns='CHAVE', values='fatia', fill_value=0)
    nomes = r[r.CHAVE.isin(lideres)].groupby('CHAVE')['NOME'].agg(lambda s: s.mode().iat[0])
    return top5, serie, nomes


def recuperacao_redes(ano, n=7):
    """Público das maiores redes (por público em 2019) no ano como fração de 2019. Fonte exibidora."""
    g = redes[redes.ANO.isin([ANO_BASE, ano])].pivot_table(index=['CHAVE', 'NOME'], columns='ANO', values='PUBLICO')
    g = g.nlargest(n, ANO_BASE).reset_index()
    return g.assign(pct=g[ano] / g[ANO_BASE])


def vida():
    """Mediana, por ano de estreia, de % do público nos 7 primeiros dias, dias até 90% e salas no pico."""
    v = vida_filmes[vida_filmes.ANO_ESTREIA.between(2015, ANOS_COMPARACAO[-1])]
    return v.groupby('ANO_ESTREIA').agg(filmes=('CHAVE', 'size'), semana1=('PCT_7_DIAS', 'median'),
                                        dias90=('DIAS_ATE_90', 'median'), pico=('SALAS_PICO', 'median'))


def dia_da_semana(ano):
    """Público médio por dia da semana no ano e nos dois anteriores, como índice (média = 100)."""
    dia = _dist[_dist.ANO.between(ano - 2, ano)].groupby('DATA')['PUBLICO'].sum()
    media = dia.groupby(dia.index.dayofweek).agg(['mean', 'size'])
    media.index = DIAS_SEMANA
    return media.assign(indice=100 * media['mean'] / media['mean'].mean())


def sazonalidade():
    """Público por dia de cada mês ÷ média do ano (1 = média), para os anos fora da pandemia."""
    m = _dist[_dist.ANO.isin(ANOS_SAZONAIS)].groupby(['ANO', _dist.DATA.dt.month])['PUBLICO'].sum().rename('p').reset_index()
    m['por_dia'] = m.p / pd.to_datetime(dict(year=m.ANO, month=m.DATA, day=1)).dt.days_in_month
    m['indice'] = m.por_dia / m.groupby('ANO').por_dia.transform('mean')
    tabela = m.pivot(index='DATA', columns='ANO', values='indice')
    tabela.index = MESES
    return tabela


def dublado():
    """% do público e das sessões de filmes estrangeiros em cópia dublada, por ano. Fonte exibidora."""
    e = sessoes[(sessoes.TIPO_OBRA == 'E') & (sessoes.ANO <= ANOS_COMPARACAO[-1])]
    g = e.groupby(['ANO', 'AUDIO'])[['PUBLICO', 'SESSOES']].sum().unstack()
    return pd.DataFrame({'pct_publico': g['PUBLICO']['DUBLADO'] / g['PUBLICO'].sum(axis=1),
                         'pct_sessoes': g['SESSOES']['DUBLADO'] / g['SESSOES'].sum(axis=1)})


def dublado_regiao(ano):
    """% do público de filmes estrangeiros em cópia dublada por região, no ano. Fonte exibidora."""
    e = sessoes[(sessoes.TIPO_OBRA == 'E') & (sessoes.ANO == ano) & (sessoes.REGIÃO != 'SEM UF')]
    g = e.groupby(['REGIÃO', 'AUDIO'])['PUBLICO'].sum().unstack()
    return (g['DUBLADO'] / g.sum(axis=1)).sort_values()
