"""Aba "Recuperação pós-pandemia": uma seção por pergunta de ../analise.ipynb (principal + 8 de apoio)."""
from dash import html

import componentes as ui
import dados_recuperacao as r

G = ui.grafico


def _filtros():
    return ui.barra_filtros([
        ui.controle('Ano de comparação', ui.dropdown('ano_comparacao', [{'label': str(a), 'value': a} for a in r.ANOS_COMPARACAO],
                                                    r.ANO_COMPARACAO_PADRAO), 'ano_comparacao',
                    ajuda=f'Comparado sempre com {r.ANO_BASE}, o último ano antes da pandemia'),
    ], rotulo='Filtro da aba', nota='Cada pergunta usa uma fonte fixa, indicada no gráfico: distribuidoras para séries longas e '
                                    'filmes; exibidoras (2017 em diante) para tudo que é por sessão. As fontes nunca são somadas.')


def _principal():
    return ui.secao(
        'O público voltou ao nível de antes da pandemia?',
        f'A pergunta principal: o público de cada ano comparado com o de {r.ANO_BASE}.',
        html.Div([
            ui.grade([(ui.kpi(k), {'lg': 4, 'md': 4}) for k in ('kpi_rec_ano', 'kpi_rec_2026', 'kpi_por_sessao')]),
            ui.grade([(ui.cartao('Público de janeiro a setembro, por ano', G('g_jan_set', 'padrao'),
                                 subtitulo='Os mesmos meses em todos os anos, porque 2026 vai só até setembro · fonte distribuidoras'),
                       {'lg': 12})]),
        ], className='ds-pilha'),
    )


def _oferta():
    return ui.secao(
        '3. A oferta encolheu ou foi o público que sumiu?',
        'Salas e sessões (oferta) contra o público que cada sessão atrai (demanda).',
        html.Div([
            ui.grade([
                (ui.cartao(f'Salas, sessões e público, como % de {r.ANO_BASE}', G('g_indice_oferta', 'padrao'),
                           subtitulo='100% = nível de 2019 · fonte exibidoras'), {'lg': 6}),
                (ui.cartao('Público médio por sessão', G('g_por_sessao', 'padrao'),
                           subtitulo='Espectadores por sessão · fonte exibidoras'), {'lg': 6}),
            ]),
            ui.grade([
                (ui.cartao('Sessões sem nenhum espectador', G('g_vazias_ano', 'padrao'),
                           subtitulo='% das sessões do ano · fonte exibidoras'), {'lg': 6}),
                (ui.cartao('Sessões vazias por faixa horária', G('g_vazias_faixa', 'padrao'),
                           id_subtitulo='sub_vazias_faixa'), {'lg': 6}),
            ]),
        ], className='ds-pilha'),
    )


def _sucessos():
    return ui.secao(
        '1. A recuperação depende de poucos sucessos?',
        'Quantos filmes passam de 1 milhão de espectadores, e quanto público ficou com os 10 maiores.',
        html.Div([
            ui.grade([
                (ui.cartao('Filmes com mais de 1 milhão de espectadores', G('g_filmes_grandes', 'padrao'),
                           subtitulo='Por ano · fonte distribuidoras'), {'lg': 6}),
                (ui.cartao('Público dos 10 maiores filmes e dos demais', G('g_top10_demais', 'padrao'),
                           subtitulo='Por ano · fonte distribuidoras'), {'lg': 6}),
            ]),
            ui.grade([
                (ui.cartao(f'Os 10 maiores filmes de {r.ANO_BASE}', G('g_maiores_base', 'alto'),
                           subtitulo='Público no ano · fonte distribuidoras'), {'lg': 6}),
                (ui.cartao('Os 10 maiores filmes do ano de comparação', G('g_maiores_ano', 'alto'),
                           id_subtitulo='sub_maiores_ano'), {'lg': 6}),
            ]),
        ], className='ds-pilha'),
    )


def _brasileiro():
    return ui.secao(
        '2. Quanto do público vai para filmes brasileiros?',
        'Obras com CPB (brasileiras) no público de filmes; o tooltip mostra o maior filme brasileiro do ano.',
        ui.grade([
            (ui.cartao('Participação do filme brasileiro no público', G('g_br_pct', 'padrao'),
                       subtitulo='% do público de filmes · fonte distribuidoras'), {'lg': 6}),
            (ui.cartao('Público dos filmes brasileiros', G('g_br_publico', 'padrao'),
                       subtitulo='Espectadores por ano · fonte distribuidoras'), {'lg': 6}),
        ]),
    )


def _geografia():
    return ui.secao(
        '4. Onde está o público, e onde ele não voltou?',
        f'Público do ano de comparação como % do de {r.ANO_BASE}; a linha pontilhada é a média nacional.',
        ui.grade([
            (ui.cartao('Recuperação por UF', G('g_rec_uf', 'longo'), id_subtitulo='sub_rec_uf',
                       nota='Por habitante exigiria a população do IBGE, que não está nos dados.'), {'lg': 6}),
            (html.Div([
                ui.cartao('Recuperação por região', G('g_rec_regiao', 'compacto'), subtitulo='Fonte distribuidoras'),
                ui.cartao('Capitais × interior', G('g_rec_lugar', 'compacto'), id_subtitulo='sub_rec_lugar'),
            ], className='ds-pilha'), {'lg': 6}),
        ]),
    )


def _empresas():
    return ui.secao(
        '5. Quem ganhou e quem perdeu espaço?',
        'Concentração da distribuição e recuperação das grandes redes de cinema.',
        html.Div([
            ui.grade([
                (ui.cartao('Fatia das 5 maiores distribuidoras', G('g_top5', 'padrao'),
                           subtitulo='% do público · fonte distribuidoras'), {'lg': 5}),
                (ui.cartao('Fatia das líderes de 2019 e 2025', G('g_lideres', 'padrao'),
                           subtitulo='% do público · na co-distribuição, cada uma recebe o público integral',
                           nota='Fox (incorporada pela Disney) e Universal não aparecem com público em 2025.'), {'lg': 7}),
            ]),
            ui.grade([(ui.cartao('Recuperação das maiores redes de cinema', G('g_redes', 'alto'), id_subtitulo='sub_redes',
                                 nota='Redes = grupos exibidores, pela razão social mais frequente; sem grupo = independentes.'),
                       {'lg': 12})]),
        ], className='ds-pilha'),
    )


def _vida():
    return ui.secao(
        '6. Como é a vida de um filme em cartaz?',
        'Filmes com 100 mil espectadores ou mais, pelo ano de estreia (valores medianos).',
        ui.grade([
            (ui.cartao('Público nos 7 primeiros dias', G('g_semana1', 'padrao'),
                       subtitulo='% do público total do filme · fonte distribuidoras',
                       nota='Estreia = 1º dia em ao menos 25% do pico de salas (ignora pré-estreias).'), {'lg': 6}),
            (ui.cartao('Salas no pico do filme', G('g_pico', 'padrao'), subtitulo='Fonte distribuidoras'), {'lg': 6}),
        ]),
    )


def _quando():
    return ui.secao(
        '7. Quando o público vai ao cinema?',
        'Dia da semana, mês e horário da sessão.',
        html.Div([
            ui.grade([
                (ui.cartao('Público por dia da semana', G('g_dia_semana', 'padrao'), id_subtitulo='sub_dia_semana'), {'lg': 6}),
                (ui.cartao('Público por sessão, por faixa horária', G('g_faixa', 'padrao'), id_subtitulo='sub_faixa'), {'lg': 6}),
            ]),
            ui.grade([(ui.cartao('Público por dia de cada mês, em relação à média do ano', G('g_sazonal', 'alto'),
                                 subtitulo='1 = média do ano; acima de 1, mês mais forte · por dia, porque os meses têm '
                                           'tamanhos diferentes · anos fora da pandemia · fonte distribuidoras'),
                       {'lg': 12})]),
        ], className='ds-pilha'),
    )


def _dublado():
    return ui.secao(
        '8. Dublado ou legendado?',
        'Filmes estrangeiros: quanto do público e das sessões foi em cópia dublada.',
        ui.grade([
            (ui.cartao('Cópias dubladas nos filmes estrangeiros', G('g_dub_ano', 'padrao'),
                       subtitulo='% do total, por ano · fonte exibidoras'), {'lg': 6}),
            (ui.cartao('Público em cópias dubladas, por região', G('g_dub_regiao', 'padrao'), id_subtitulo='sub_dub_regiao'),
             {'lg': 6}),
        ]),
    )


def montar():
    return [
        _filtros(),
        html.Main(className='ds-pagina', children=[
            _principal(), _sucessos(), _brasileiro(), _oferta(), _geografia(), _empresas(), _vida(), _quando(), _dublado(),
        ]),
    ]
