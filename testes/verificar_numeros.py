"""Captura e compara os números exibidos pelo dashboard (antes × depois de mudanças visuais).

Uso:
  python testes/verificar_numeros.py salvar   <saida.json>
  python testes/verificar_numeros.py comparar <base.json>

Chama cada callback de figura pelo endpoint HTTP do Dash (/_dash-update-component),
em vários cenários de filtro, e reduz cada figura aos seus pares (categoria, valor).
Rótulos, cores e formatação são ignorados de propósito: só os números contam.
Deve ser executado de dentro de projeto_completo/.
"""
import json
import re
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import index  # noqa: E402

FIGURAS = ['static-maxmin', 'regiaobar_graph', 'estadobar_graph', 'animation_graph',
           'direct_comparison_graph', 'card1_indicators', 'card2_indicators',
           'rank_filmes', 'rank_distribuidoras', 'rank_exibidoras']

CENARIOS = [
    dict(fonte=f, anos=a, ano=y, regiao=r, estados=e, freq=q, uf1=u1, uf2=u2)
    for f, a, (y, r), (e, q), (u1, u2) in product(
        ['DISTRIBUIDOR', 'EXIBIDORA'],
        [[2014, 2026], [2017, 2019], [2020, 2022]],
        [(2025, 'SUDESTE'), (2016, 'NORDESTE')],
        [(['SP', 'RJ', 'MG'], 'W'), (['BA', 'AM'], 'MS'), (['DF'], 'D')],
        [('RJ', 'MG'), ('PE', 'RS')],
    )
]


def valor_entrada(id_, prop, c):
    """Valor de cada entrada de callback no cenário c (tema e controles sem efeito nos números ficam fixos)."""
    chave = id_ if isinstance(id_, str) else json.dumps(id_)
    tabela = {
        ('dataset', 'data'): {'anos': c['anos']},
        ('select_fonte', 'value'): c['fonte'],
        ('select_ano', 'value'): c['ano'],
        ('select_regiao', 'value'): c['regiao'],
        ('select_estados0', 'value'): c['estados'],
        ('select_freq', 'value'): c['freq'],
        ('select_estado1', 'value'): c['uf1'],
        ('select_estado2', 'value'): c['uf2'],
        ('rangeslider', 'value'): c['anos'],
    }
    if (chave, prop) in tabela:
        return tabela[(chave, prop)]
    if 'theme' in chave or 'tema' in chave:
        return True
    if (chave, prop) == ('serie_cores', 'data'):
        return {}
    raise KeyError(f'entrada sem valor no cenário: {chave}.{prop}')


def _kpi_html(no):
    """Cartão de KPI em HTML: valor e referência gravados em data-valor / data-referencia."""
    if isinstance(no, list):
        for x in no:
            r = _kpi_html(x)
            if r:
                return r
    elif isinstance(no, dict):
        props = no.get('props', {})
        if 'data-valor' in props:
            return [round(float(props['data-valor']), 4), round(float(props['data-referencia']), 4)]
        return _kpi_html(props.get('children'))
    return None


def _categoria(k):
    """Normaliza a categoria: datas viram AAAA-MM-DD (independe de como o Plotly serializa); texto, 20 caracteres."""
    k = str(k)
    if re.match(r'^\d{4}-\d{2}-\d{2}', k):
        return k[:10]
    return k[:20]


def reduzir(fig):
    """Saída de um visual -> conjunto de números exibidos.

    Figura: união de todos os pares (categoria[:20], valor) de todos os traços, de modo que
    dividir os mesmos valores em traços diferentes (ex.: positivos/negativos) não conta como
    mudança. Indicador (go.Indicator ou cartão HTML): [valor, referência].
    """
    if not isinstance(fig, dict) or 'data' not in fig:
        kpi = _kpi_html(fig)
        return {'indicador': kpi} if kpi else {}
    pares_todos = set()
    for t in fig.get('data', []):
        if t.get('type') == 'indicator':
            return {'indicador': [round(float(t['value']), 4),
                                  round(float(t.get('delta', {}).get('reference', 0)), 4)]}
        horizontal = t.get('orientation') == 'h'
        cats = t.get('y' if horizontal else 'x') or []
        vals = t.get('x' if horizontal else 'y') or []
        if isinstance(vals, dict):  # numpy serializado (bdata)
            import base64
            import numpy as np
            vals = np.frombuffer(base64.b64decode(vals['bdata']), dtype=vals['dtype']).tolist()
        if isinstance(cats, dict):
            import base64
            import numpy as np
            cats = np.frombuffer(base64.b64decode(cats['bdata']), dtype=cats['dtype']).tolist()
        cd = t.get('customdata')
        if horizontal and cd:  # nome completo guardado em customdata, quando o rótulo do eixo é abreviado
            cats = [x[0] if isinstance(x, list) else x for x in cd]
        pares = sorted(
            (_categoria(k), None if v is None or v != v else round(float(v), 4))
            for k, v in zip(cats, vals)
        )
        pares_todos.update(p for p in pares if p[1] is not None)
    return {'pares': sorted(pares_todos)}


def capturar():
    cliente = index.app.server.test_client()
    cliente.get('/')  # o primeiro acesso termina de registrar os callbacks
    callbacks = list(index.app.callback_map.items())
    resultado = {}
    for i, c in enumerate(CENARIOS):
        for chave_cb, cb in callbacks:
            saidas = chave_cb[2:-2].split('...') if chave_cb.startswith('..') else [chave_cb]
            ids = [s.rsplit('.', 1) for s in saidas]
            if not any(id_ in FIGURAS for id_, _ in ids):
                continue
            entradas = [{'id': e['id'] if not e['id'].startswith('{') else json.loads(e['id']),
                         'property': e['property']} for e in cb['inputs']]
            estados = [{'id': e['id'], 'property': e['property']} for e in cb.get('state', [])]
            for e in entradas + estados:
                e['value'] = valor_entrada(e['id'], e['property'], c)
            corpo = {'output': chave_cb,
                     'outputs': [{'id': id_, 'property': p} for id_, p in ids] if len(ids) > 1
                     else {'id': ids[0][0], 'property': ids[0][1]},
                     'inputs': entradas, 'state': estados,
                     'changedPropIds': [f"{json.dumps(entradas[0]['id']) if isinstance(entradas[0]['id'], dict) else entradas[0]['id']}.{entradas[0]['property']}"]}
            r = cliente.post('/_dash-update-component', json=corpo)
            if r.status_code == 204:
                continue
            assert r.status_code == 200, (chave_cb, r.status_code, r.data[:300])
            resposta = r.get_json()['response']
            for id_, p in ids:
                if id_ in FIGURAS:
                    resultado[f'{i}:{id_}'] = reduzir(resposta[id_][p])
    return resultado


def main():
    modo, caminho = sys.argv[1], sys.argv[2]
    atual = capturar()
    if modo == 'salvar':
        Path(caminho).write_text(json.dumps(atual, ensure_ascii=False), encoding='utf-8')
        print(f'{len(atual)} figuras salvas em {caminho} ({len(CENARIOS)} cenários)')
        return
    base = json.loads(Path(caminho).read_text(encoding='utf-8'))
    faltando = sorted(set(base) - set(atual))
    diferentes = sorted(k for k in base if k in atual and base[k] != json.loads(json.dumps(atual[k])))
    print(f'{len(base)} figuras na base; {len(faltando)} ausentes; {len(diferentes)} com números diferentes')
    for k in (faltando + diferentes)[:15]:
        print('  ', k)
    sys.exit(1 if faltando or diferentes else 0)


if __name__ == '__main__':
    main()
