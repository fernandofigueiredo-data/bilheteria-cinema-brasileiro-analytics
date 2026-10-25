"""Templates Plotly do Design System, um por modo, montados só a partir dos tokens."""
import plotly.graph_objects as go
import plotly.io as pio

from design import formatos
from design.tokens import BORDA, CORES, FONTE, GRAFICO, TRANSPARENTE

NOME = {'claro': 'cinema_claro', 'escuro': 'cinema_escuro'}


def _template(modo):
    c = CORES[modo]
    eixo = dict(
        showgrid=True, gridcolor=c['grade'], gridwidth=BORDA['fina'], griddash='solid',
        zeroline=False, showline=True, linecolor=c['eixo'], linewidth=BORDA['fina'],
        ticks='', tickfont=dict(size=GRAFICO['fonte_eixo'], color=c['texto_sec']),
        title=dict(font=dict(size=GRAFICO['fonte_eixo'], color=c['texto_sec'])),
        automargin=True, fixedrange=True, ticklabelstandoff=GRAFICO['afastamento_rotulo'],
    )
    return go.layout.Template(layout=dict(
        font=dict(family=FONTE['sans'], size=GRAFICO['fonte_eixo'], color=c['texto_sec']),
        paper_bgcolor=TRANSPARENTE,
        plot_bgcolor=TRANSPARENTE,
        colorway=c['categorica'],
        separators=formatos.SEPARADORES_PLOTLY,
        margin=GRAFICO['margem'],
        xaxis=eixo, yaxis=eixo,
        hoverlabel=dict(bgcolor=c['tooltip_fundo'], bordercolor=c['tooltip_fundo'],
                        font=dict(family=FONTE['sans'], size=GRAFICO['fonte_tooltip'], color=c['tooltip_texto'])),
        legend=dict(orientation='h', x=0, xanchor='left', y=1.0, yanchor='bottom',
                    bgcolor=TRANSPARENTE, title=dict(text=None),
                    font=dict(size=GRAFICO['fonte_legenda'], color=c['texto_sec']),
                    itemclick=False, itemdoubleclick=False),
        dragmode=False,
    ))


for _modo, _nome in NOME.items():
    pio.templates[_nome] = _template(_modo)
