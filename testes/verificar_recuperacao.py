"""Confere os números da aba "Recuperação pós-pandemia" contra os resultados de ../analise.ipynb.

Uso (de dentro de projeto_completo/): python ../testes/verificar_recuperacao.py
Cada valor esperado foi lido nas saídas do notebook executado em 23/10/2026.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import dados_recuperacao as r  # noqa: E402

a = r.anual()
o, indice = r.oferta_demanda()
c = r.concentracao()
b = r.brasileiro()
uf = r.recuperacao_local(2025, 'UF')
reg = r.recuperacao_local(2025, 'REGIÃO')
lugar = r.recuperacao_local(2025, 'LUGAR')
top5, _, _ = r.distribuidoras()
redes = r.recuperacao_redes(2025).set_index('NOME')
vida = r.vida()
semana = r.dia_da_semana(2025)
dub = r.dublado()
dub_reg = r.dublado_regiao(2025)
faixa = r.faixas(2025)

ESPERADO = [
    ('público 2025 / 2019', a.loc[2025, 'pct_ano'], 0.649),
    ('jan–set 2026 / 2019', a.loc[2026, 'pct_jan_set'], 0.768),
    ('público 2019', a.loc[2019, 'publico'], 177_585_628),
    ('público 2025', a.loc[2025, 'publico'], 115_250_037),
    ('salas 2025 (exibidoras)', o.loc[2025, 'SALAS'], 3595),
    ('sessões 2025', o.loc[2025, 'REGISTROS'], 4_394_220),
    ('público por sessão 2019', o.loc[2019, 'por_sessao'], 39.7),
    ('público por sessão 2025', o.loc[2025, 'por_sessao'], 26.0),
    ('% sessões vazias 2025', o.loc[2025, 'pct_vazias'], 0.092),
    ('filmes com 1 mi+ 2019', c.loc[2019, 'grandes'], 36),
    ('filmes com 1 mi+ 2025', c.loc[2025, 'grandes'], 27),
    ('10 maiores 2019', c.loc[2019, 'top10'], 90_312_348),
    ('10 maiores 2025', c.loc[2025, 'top10'], 50_500_763),
    ('% brasileiro 2019', b.loc[2019, 'pct'], 0.136),
    ('% brasileiro 2025', b.loc[2025, 'pct'], 0.100),
    ('SP 2025 / 2019', uf.loc['SP', 'pct'], 0.623),
    ('RJ 2025 / 2019', uf.loc['RJ', 'pct'], 0.568),
    ('Sudeste 2025 / 2019', reg.loc['SUDESTE', 'pct'], 0.610),
    ('Nordeste 2025 / 2019', reg.loc['NORDESTE', 'pct'], 0.768),
    ('capitais 2025 / 2019', lugar.loc['capital', 'pct'], 0.626),
    ('interior 2025 / 2019', lugar.loc['interior', 'pct'], 0.674),
    ('5 maiores distribuidoras 2019', top5.loc[2019], 0.814),
    ('5 maiores distribuidoras 2025', top5.loc[2025], 0.898),
    ('Cinemark 2025 / 2019', redes.loc['CINEMARK BRASIL S.A', 'pct'], 0.631),
    ('independentes 2025 / 2019', redes.loc['INDEPENDENTES (SEM GRUPO)', 'pct'], 0.791),
    ('1ª semana 2019 (mediana)', vida.loc[2019, 'semana1'], 0.463),
    ('1ª semana 2025 (mediana)', vida.loc[2025, 'semana1'], 0.473),
    ('salas no pico 2025 (mediana)', vida.loc[2025, 'pico'], 769.5),
    ('sábado (índice)', semana.loc['sáb', 'indice'], 160),
    ('terça (índice)', semana.loc['ter', 'indice'], 75),
    ('público por sessão 18h–21h', faixa.loc['4. 18h–21h', 'por_sessao'], 34.3),
    ('% dublado 2017', dub.loc[2017, 'pct_publico'], 0.740),
    ('% dublado 2025', dub.loc[2025, 'pct_publico'], 0.855),
    ('% dublado Norte 2025', dub_reg.loc['NORTE'], 0.934),
]

falhas = 0
for nome, valor, esperado in ESPERADO:
    casas = len(repr(esperado).split('.')[1]) if isinstance(esperado, float) else 0
    tolerancia = 0.5 * 10 ** -casas + 1e-9   # o notebook mostra o valor arredondado nessas casas
    ok = abs(float(valor) - esperado) <= tolerancia
    falhas += not ok
    print(f"{'ok ' if ok else 'ERRO'} {nome}: {valor:.4f} (notebook: {esperado})")
print(f'{len(ESPERADO) - falhas}/{len(ESPERADO)} valores iguais aos do notebook')
sys.exit(1 if falhas else 0)
