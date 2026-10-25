"""Formatos únicos de número, percentual e data (pt-BR) para todo o dashboard."""
import math

import pandas as pd

SEPARADORES_PLOTLY = ',.'      # decimal ',' e milhar '.' em todos os formatos d3 do Plotly
HOVER_INTEIRO = ',.0f'         # 61.327.367
HOVER_DECIMAL = ',.1f'         # 26,0
HOVER_PCT = '.1%'              # 64,9%
DATA_DIA = '%d/%m/%Y'
DATA_MES = '%m/%Y'
DATA_ANO = '%Y'
# marcas do eixo de datas conforme o zoom, sem nomes de mês (o Plotly os escreveria em inglês)
TICKS_DATA = [
    {'dtickrange': [None, 'M1'], 'value': '%d/%m/%Y'},
    {'dtickrange': ['M1', 'M12'], 'value': '%m/%Y'},
    {'dtickrange': ['M12', None], 'value': '%Y'},
]
ESCALAS = [(1e9, 'bi'), (1e6, 'mi'), (1e3, 'mil')]


def inteiro(n):
    """61327367 -> '61.327.367'."""
    return f'{n:,.0f}'.replace(',', '.')


def compacto(n, casas=1, fixo=False):
    """1500000 -> '1,5 mi'; 500000 -> '500 mil'; 0 -> '0'. Sinal de menos tipográfico.

    fixo=False (marcas de eixo): corta zeros à direita ('93 mi'). fixo=True (rótulo de dado): mantém
    as casas ('93,0 mi'), para todos os rótulos de um gráfico terem o mesmo formato.
    """
    sinal = '−' if n < 0 else ''
    n = abs(n)
    for base, sufixo in ESCALAS:
        if n >= base:
            v = n / base
            texto = f'{v:.{casas}f}'
            if casas and not fixo:
                texto = texto.rstrip('0').rstrip('.')
            return f"{sinal}{texto.replace('.', ',')} {sufixo}"
    return f'{sinal}{inteiro(n)}'


def percentual(fracao, sinal=True):
    """-0.301 -> '−30,1%'; 0.591 -> '+59,1%'."""
    s = f'{abs(fracao) * 100:.1f}'.replace('.', ',')
    if not sinal:
        return f'{s}%'
    return f"{'+' if fracao > 0 else '−' if fracao < 0 else ''}{s}%"


def decimal(v, casas=1):
    """26.0026 -> '26,0'."""
    return f'{v:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def data(d):
    return pd.Timestamp(d).strftime(DATA_DIA)


def dia_mes(d):
    return pd.Timestamp(d).strftime('%d/%m')


def _passo_redondo(bruto):
    exp = math.floor(math.log10(bruto)) if bruto > 0 else 0
    for m in (1, 2, 2.5, 5, 10):
        passo = m * 10 ** exp
        if passo >= bruto:
            return passo
    return 10 ** (exp + 1)


def marcas_eixo(vmin, vmax, n=5, com_sinal=False):
    """Marcas "redondas" e rótulos compactos pt-BR para um eixo de valores que sempre inclui o zero.

    Retorna (tickvals, ticktext, faixa). com_sinal=True prefixa '+' nos positivos (eixos de diferença).
    """
    vmin, vmax = min(vmin, 0), max(vmax, 0)
    if vmax == vmin:
        vmax = vmin + 1
    passo = max(_passo_redondo((vmax - vmin) / n), 1)   # contagens: passo mínimo de 1 espectador
    base = math.floor(vmin / passo) * passo
    topo = math.ceil(vmax / passo) * passo
    vals = [base + i * passo for i in range(int(round((topo - base) / passo)) + 1)]
    textos = [('+' if com_sinal and v > 0 else '') + compacto(v) for v in vals]
    folga = passo * 0.05 if base < 0 else 0     # respiro só no lado negativo (o positivo já termina numa marca)
    return vals, textos, [base - folga, topo]


def abreviar(texto, limite):
    """Corta em limite caracteres com reticências (o texto completo vai para o tooltip)."""
    texto = str(texto)
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip() + '…'
