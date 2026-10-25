"""Camada de dados: leitura dos CSVs agregados e todos os cálculos exibidos.

Sem nenhuma dependência visual. Os cálculos são os mesmos da versão anterior do index.py
(conferidos por testes/verificar_numeros.py).
"""
import pandas as pd

# Gerados por ../pipeline/agregar_dashboard.py a partir de ../dados/bilheteria_unificada.csv.gz
df_main = pd.read_csv("data_bilheteria.csv", dtype={'ANO': int}, keep_default_na=False)
df_main['DATA'] = pd.to_datetime(df_main['DATA'])
df_main = df_main.sort_values(by='DATA', ascending=True).reset_index(drop=True)

df_rank = pd.read_csv("data_ranking.csv", dtype={'ANO': int, 'CHAVE': str})

FONTES = {'DISTRIBUIDOR': 'Distribuidoras', 'EXIBIDORA': 'Exibidoras'}
FONTES_DETALHE = {'DISTRIBUIDOR': 'por sala e dia', 'EXIBIDORA': 'por sessão'}
FONTE_PADRAO = 'DISTRIBUIDOR'
# Primeiro ano com cobertura nacional de cada fonte: a exibidora é quase vazia até meados de 2016
INICIO_COBERTURA = {'DISTRIBUIDOR': 2014, 'EXIBIDORA': 2017}
ANO_MIN, ANO_MAX = int(df_main.ANO.min()), int(df_main.ANO.max())
ANOS = sorted(int(a) for a in df_main.ANO.unique())
UFS = sorted(u for u in df_main.UF.unique() if u != 'ND')  # ND = linhas sem UF na origem
REGIOES = sorted(df_main['REGIÃO'].unique())
ULTIMO_DIA = {f: df_main.loc[df_main.FONTE == f, 'DATA'].max() for f in FONTES}

# Escolhas iniciais: as UFs de maior público no período
ufs_top = (df_main[(df_main.FONTE == 'DISTRIBUIDOR') & (df_main.UF != 'ND')].groupby('UF')['PUBLICO'].sum()
           .sort_values(ascending=False).index.tolist())

FREQUENCIAS = {'D': 'Diário', 'W': 'Semanal', 'MS': 'Mensal'}
RANKINGS = [('FILME', None), ('DISTRIBUIDORA', 'DISTRIBUIDOR'), ('EXIBIDORA', 'EXIBIDORA')]


def recorte(fonte, anos):
    """Linhas da fonte escolhida dentro do intervalo de anos do RangeSlider."""
    return df_main[(df_main.FONTE == fonte) & (df_main.ANO >= anos[0]) & (df_main.ANO <= anos[1])]


def maximos_minimos(fonte, anos):
    """Maior e menor público diário nacional de cada ano. Colunas: Máximo, Mínimo; índice ANO."""
    diario = recorte(fonte, anos).groupby(['ANO', 'DATA'])['PUBLICO'].sum().reset_index()
    final_df = pd.concat([diario.groupby('ANO')['PUBLICO'].max(),
                          diario.groupby('ANO')['PUBLICO'].min()], axis=1)
    final_df.columns = ['Máximo', 'Mínimo']
    return final_df


def por_regiao(fonte, ano, regiao):
    """Público do ano por região e por UF da região escolhida (ordem crescente)."""
    df_filtered = df_main[(df_main.FONTE == fonte) & (df_main.ANO == ano)]
    dff_regiao = df_filtered.groupby('REGIÃO')['PUBLICO'].sum().reset_index()
    dff_estado = df_filtered[df_filtered['REGIÃO'] == regiao].groupby('UF')['PUBLICO'].sum().reset_index()
    return (dff_regiao.sort_values(by='PUBLICO', ascending=True),
            dff_estado.sort_values(by='PUBLICO', ascending=True))


def serie_ufs(fonte, anos, estados, freq):
    """Público por UF agregado na frequência escolhida (D, W ou MS)."""
    dff = recorte(fonte, anos)
    dff = dff[dff.UF.isin(estados)]
    return dff.groupby(['UF', pd.Grouper(key='DATA', freq=freq)])['PUBLICO'].sum().reset_index()


def comparacao_mensal(fonte, anos, est1, est2):
    """Diferença mensal de público (est1 − est2). Colunas: DATA, DIF."""
    dff = recorte(fonte, anos)
    mensal = (dff[dff.UF.isin([est1, est2])]
              .groupby([pd.Grouper(key='DATA', freq='MS'), 'UF'])['PUBLICO'].sum()
              .unstack('UF').reindex(columns=[est1, est2]).fillna(0))
    return pd.DataFrame({'DATA': mensal.index, 'DIF': (mensal[est1] - mensal[est2]).values})


def indicador_uf(fonte, anos, estado):
    """Público do último ano do recorte e referência no primeiro ano com cobertura plena.

    Retorna None sem dados; senão dict com valor, referencia, ano_ref, ano, ultimo_dia, parcial.
    """
    dff = recorte(fonte, anos)
    anual = dff[dff.UF == estado].groupby('ANO')['PUBLICO'].sum()
    if not len(anual):
        return None
    cobertos = anual.index[anual.index >= INICIO_COBERTURA[fonte]]
    ano1, ano2 = (cobertos.min() if len(cobertos) else anual.index.min()), anual.index.max()
    # o último ano dos dados pode estar incompleto: avisa até que dia há registro
    ultimo_dia = dff.loc[dff.ANO == ano2, 'DATA'].max()
    return {'valor': anual.loc[ano2], 'referencia': anual.loc[ano1], 'ano_ref': int(ano1), 'ano': int(ano2),
            'ultimo_dia': ultimo_dia, 'parcial': (ultimo_dia.month, ultimo_dia.day) != (12, 31)}


def top10(fonte, anos):
    """Top 10 por público no período: filmes (fonte escolhida), distribuidoras e exibidoras.

    Lista de DataFrames (índice CHAVE; colunas NOME, PUBLICO) em ordem crescente de público.
    """
    dff = df_rank[(df_rank.ANO >= anos[0]) & (df_rank.ANO <= anos[1])]
    saida = []
    for tipo, fonte_tipo in RANKINGS:
        top = (dff[(dff.TIPO == tipo) & (dff.FONTE == (fonte_tipo or fonte))]
               .groupby('CHAVE').agg(NOME=('NOME', 'last'), PUBLICO=('PUBLICO', 'sum'))
               .nlargest(10, 'PUBLICO').sort_values('PUBLICO'))
        saida.append(top)
    return saida
