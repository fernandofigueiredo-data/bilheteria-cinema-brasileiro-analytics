"""Gera os CSVs agregados que o dashboard lê com pd.read_csv, sem banco de dados.

Uso: python -I pipeline/agregar_dashboard.py <bilheteria_limpa.csv.gz> <dir_saida>

Saídas (aba "Visão geral"):
  data_bilheteria.csv   FONTE, DATA, ANO, REGIÃO, UF, PUBLICO, REGISTROS
  data_ranking.csv      FONTE, ANO, TIPO (FILME/DISTRIBUIDORA/EXIBIDORA), CHAVE, NOME, PUBLICO
Saídas (aba "Recuperação pós-pandemia", ver ../analise.ipynb):
  data_oferta.csv       FONTE, ANO, SALAS, REGISTROS, REGISTROS_SEM_PUBLICO, PUBLICO
  data_filmes_ano.csv   ANO, CHAVE, TIPO_OBRA (B/E), NOME, PUBLICO                      [distribuidor]
  data_local.csv        ANO, UF, REGIÃO, LUGAR (capital/interior), SALAS, PUBLICO        [distribuidor]
  data_redes.csv        ANO, CHAVE, NOME, PUBLICO                                         [exibidora, 2017+]
  data_vida_filmes.csv  CHAVE, NOME, ANO_ESTREIA, PUBLICO, SALAS_PICO, PCT_7_DIAS, DIAS_ATE_90 [distribuidor]
  data_sessoes.csv      ANO, FAIXA, AUDIO, TIPO_OBRA, REGIÃO, SESSOES, SESSOES_SEM_PUBLICO, PUBLICO [exibidora, 2017+]

As fontes nunca são somadas entre si: toda linha agregada carrega sua FONTE (ou só usa uma).
Na fonte distribuidor, uma mesma exibição (dia, sala, obra) aparece uma vez por
distribuidora em co-distribuição; para totais de público ela é contada uma única vez
(maior público informado). No ranking de distribuidoras, cada uma recebe o público
integral das exibições que informou (ver DECISOES.md). A fonte exibidora só tem cobertura
nacional a partir de 2017; as saídas por sessão começam nesse ano.
"""
import shutil
import sys
from pathlib import Path

import duckdb

# Regiões do IBGE por UF (mapeamento fixo, só para o filtro de região)
REGIAO_UF = {
    'NORTE': ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
    'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'CENTRO-OESTE': ['DF', 'GO', 'MS', 'MT'],
    'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
    'SUL': ['PR', 'RS', 'SC'],
}
# Capital de cada UF, sem acento (comparada com o município sem acento)
CAPITAL_UF = {
    'AC': 'RIO BRANCO', 'AL': 'MACEIO', 'AP': 'MACAPA', 'AM': 'MANAUS', 'BA': 'SALVADOR', 'CE': 'FORTALEZA',
    'DF': 'BRASILIA', 'ES': 'VITORIA', 'GO': 'GOIANIA', 'MA': 'SAO LUIS', 'MT': 'CUIABA', 'MS': 'CAMPO GRANDE',
    'MG': 'BELO HORIZONTE', 'PA': 'BELEM', 'PB': 'JOAO PESSOA', 'PR': 'CURITIBA', 'PE': 'RECIFE', 'PI': 'TERESINA',
    'RJ': 'RIO DE JANEIRO', 'RN': 'NATAL', 'RS': 'PORTO ALEGRE', 'RO': 'PORTO VELHO', 'RR': 'BOA VISTA',
    'SC': 'FLORIANOPOLIS', 'SP': 'SAO PAULO', 'SE': 'ARACAJU', 'TO': 'PALMAS',
}
INICIO_SESSOES = '2017-01-01'   # cobertura nacional da fonte exibidora
FILME_MINIMO = 100_000          # público mínimo para entrar no ciclo de vida
ESTREIA_FRACAO_PICO = 0.25      # estreia = 1º dia com ao menos 25% do pico de salas (ignora pré-estreias)


def _copiar(con, consulta, destino):
    con.execute(f"COPY ({consulta}) TO '{destino}' (HEADER, DELIMITER ',')")


def main(csv_gz: str, dir_saida: str) -> None:
    saida = Path(dir_saida)
    temporario = Path(csv_gz).resolve().parent / '.duckdb_tmp'
    con = duckdb.connect()
    con.execute(f"SET memory_limit='10GB'; SET preserve_insertion_order=false; SET temp_directory='{temporario}'")
    con.execute("CREATE TEMP TABLE regiao (uf VARCHAR, regiao VARCHAR, capital VARCHAR)")
    con.executemany("INSERT INTO regiao VALUES (?, ?, ?)",
                    [(u, r, CAPITAL_UF[u]) for r, ufs in REGIAO_UF.items() for u in ufs])
    con.execute(f"""
        CREATE TEMP TABLE base AS
        SELECT fonte, data_exibicao, sessao, uf_sala_complexo uf, municipio_sala_complexo municipio, registro_sala,
               nome_sala, cpb_roe, left(cpb_roe, 1) tipo_obra, coalesce(titulo_brasil, titulo_original) titulo, audio,
               cnpj_distribuidora, razao_social_distribuidora, cnpj_exibidora, razao_social_exibidora,
               registro_grupo_exibidor grupo, publico
        FROM read_csv('{csv_gz}', header=true, compression='gzip',
                      types={{'data_exibicao': 'DATE', 'sessao': 'TIMESTAMP', 'publico': 'BIGINT', 'cpb_roe': 'VARCHAR',
                              'registro_sala': 'VARCHAR', 'registro_grupo_exibidor': 'VARCHAR',
                              'cnpj_distribuidora': 'VARCHAR', 'cnpj_exibidora': 'VARCHAR'}})
    """)
    # Fonte distribuidor com uma linha por exibição (co-distribuição deduplicada)
    con.execute("""
        CREATE TEMP TABLE exib_d AS
        SELECT data_exibicao, registro_sala, nome_sala, cpb_roe, any_value(tipo_obra) tipo_obra, any_value(uf) uf,
               any_value(municipio) municipio, mode(titulo) titulo, max(publico) publico
        FROM base WHERE fonte = 'distribuidor'
        GROUP BY data_exibicao, registro_sala, nome_sala, cpb_roe
    """)
    # Uma linha por exibição: exibidora já é uma linha por sessão
    con.execute("""
        CREATE TEMP TABLE exibicao AS
        SELECT fonte, data_exibicao, uf, cpb_roe, titulo, publico, 1 AS registros FROM base WHERE fonte = 'exibidora'
        UNION ALL
        SELECT 'distribuidor', data_exibicao, uf, cpb_roe, titulo, publico, 1 FROM exib_d
    """)
    con.execute(f"CREATE TEMP TABLE sessoes AS SELECT * FROM base WHERE fonte = 'exibidora' AND data_exibicao >= DATE '{INICIO_SESSOES}'")

    # ---------------------------------------------------------------- aba "Visão geral"
    _copiar(con, """
        SELECT upper(e.fonte) "FONTE", data_exibicao "DATA", year(data_exibicao) "ANO",
               coalesce(r.regiao, 'SEM UF') "REGIÃO", coalesce(e.uf, 'ND') "UF",
               sum(publico) "PUBLICO", sum(registros) "REGISTROS"
        FROM exibicao e LEFT JOIN regiao r ON r.uf = e.uf
        GROUP BY ALL ORDER BY 2, 1, 5""", saida / 'data_bilheteria.csv')
    _copiar(con, """
        SELECT upper(fonte) "FONTE", year(data_exibicao) "ANO", 'FILME' "TIPO", cpb_roe "CHAVE",
               mode(titulo) "NOME", sum(publico) "PUBLICO"
        FROM exibicao GROUP BY 1, 2, 4
        UNION ALL
        SELECT 'DISTRIBUIDOR', year(data_exibicao), 'DISTRIBUIDORA', cnpj_distribuidora,
               mode(razao_social_distribuidora), sum(publico)
        FROM base WHERE fonte = 'distribuidor' GROUP BY 2, 4
        UNION ALL
        SELECT 'EXIBIDORA', year(data_exibicao), 'EXIBIDORA', cnpj_exibidora,
               mode(razao_social_exibidora), sum(publico)
        FROM base WHERE fonte = 'exibidora' GROUP BY 2, 4
        ORDER BY 1, 2, 3, 6 DESC""", saida / 'data_ranking.csv')

    # ---------------------------------------------------------------- aba "Recuperação pós-pandemia"
    # Oferta × demanda: salas ativas, registros (exibições ou sessões), registros sem público, público
    _copiar(con, f"""
        SELECT 'DISTRIBUIDOR' "FONTE", year(data_exibicao) "ANO", count(DISTINCT registro_sala) "SALAS", count(*) "REGISTROS",
               count(*) FILTER (WHERE publico = 0) "REGISTROS_SEM_PUBLICO", sum(publico) "PUBLICO" FROM exib_d GROUP BY 2
        UNION ALL
        SELECT 'EXIBIDORA', year(data_exibicao), count(DISTINCT registro_sala), count(*),
               count(*) FILTER (WHERE publico = 0), sum(publico) FROM sessoes GROUP BY 2
        ORDER BY 1, 2""", saida / 'data_oferta.csv')
    # Público por filme e ano (só obras com CPB/ROE: B = brasileira, E = estrangeira)
    _copiar(con, """
        SELECT year(data_exibicao) "ANO", cpb_roe "CHAVE", any_value(tipo_obra) "TIPO_OBRA", mode(titulo) "NOME",
               sum(publico) "PUBLICO"
        FROM exib_d WHERE tipo_obra IN ('B', 'E') GROUP BY 1, 2 ORDER BY 1, 5 DESC""", saida / 'data_filmes_ano.csv')
    # Público e salas por UF e por capital × interior
    _copiar(con, """
        SELECT year(data_exibicao) "ANO", e.uf "UF", r.regiao "REGIÃO",
               CASE WHEN strip_accents(e.municipio) = r.capital THEN 'capital' ELSE 'interior' END "LUGAR",
               count(DISTINCT registro_sala) "SALAS", sum(publico) "PUBLICO"
        FROM exib_d e JOIN regiao r ON r.uf = e.uf GROUP BY ALL ORDER BY 1, 2, 4""", saida / 'data_local.csv')
    # Grupos exibidores (nome = razão social mais frequente do grupo; sem grupo = independentes)
    _copiar(con, """
        WITH nomes AS (SELECT grupo, mode(razao_social_exibidora) nome FROM sessoes WHERE grupo IS NOT NULL GROUP BY 1)
        SELECT year(data_exibicao) "ANO", coalesce(s.grupo, 'SEM GRUPO') "CHAVE",
               coalesce(any_value(n.nome), 'INDEPENDENTES (SEM GRUPO)') "NOME", sum(publico) "PUBLICO"
        FROM sessoes s LEFT JOIN nomes n USING (grupo) GROUP BY 1, 2 ORDER BY 1, 4 DESC""", saida / 'data_redes.csv')
    # Ciclo de vida dos filmes com ao menos FILME_MINIMO de público
    _copiar(con, f"""
        WITH dia AS (SELECT cpb_roe, data_exibicao dia, count(*) salas, sum(publico) p FROM exib_d
                     WHERE tipo_obra IN ('B', 'E') GROUP BY 1, 2),
             filme AS (SELECT cpb_roe, max(salas) pico, sum(p) total FROM dia GROUP BY 1 HAVING sum(p) >= {FILME_MINIMO}),
             estreia AS (SELECT cpb_roe, min(dia) estreia FROM dia JOIN filme USING (cpb_roe)
                         WHERE salas >= {ESTREIA_FRACAO_PICO} * pico GROUP BY 1),
             acum AS (SELECT dia.*, estreia, total, pico, sum(p) OVER (PARTITION BY cpb_roe ORDER BY dia) ac
                      FROM dia JOIN estreia USING (cpb_roe) JOIN filme USING (cpb_roe)),
             nomes AS (SELECT cpb_roe, mode(titulo) nome FROM exib_d GROUP BY 1)
        SELECT cpb_roe "CHAVE", any_value(nome) "NOME", year(any_value(estreia)) "ANO_ESTREIA", any_value(total) "PUBLICO",
               any_value(pico) "SALAS_PICO",
               sum(p) FILTER (WHERE dia BETWEEN estreia AND estreia + 6) / any_value(total) "PCT_7_DIAS",
               min(dia - estreia) FILTER (WHERE ac >= 0.9 * total) "DIAS_ATE_90"
        FROM acum JOIN nomes USING (cpb_roe) GROUP BY 1 ORDER BY 3, 4 DESC""", saida / 'data_vida_filmes.csv')
    # Perfil das sessões: faixa horária, áudio, tipo de obra e região
    _copiar(con, """
        SELECT year(data_exibicao) "ANO",
               CASE WHEN hour(sessao) < 12 THEN '1. até 12h' WHEN hour(sessao) < 15 THEN '2. 12h–15h'
                    WHEN hour(sessao) < 18 THEN '3. 15h–18h' WHEN hour(sessao) < 21 THEN '4. 18h–21h'
                    ELSE '5. 21h ou mais' END "FAIXA",
               audio "AUDIO", coalesce(tipo_obra, '?') "TIPO_OBRA", coalesce(r.regiao, 'SEM UF') "REGIÃO",
               count(*) "SESSOES", count(*) FILTER (WHERE publico = 0) "SESSOES_SEM_PUBLICO", sum(publico) "PUBLICO"
        FROM sessoes s LEFT JOIN regiao r ON r.uf = s.uf GROUP BY ALL ORDER BY ALL""", saida / 'data_sessoes.csv')

    for nome in ('data_bilheteria.csv', 'data_ranking.csv', 'data_oferta.csv', 'data_filmes_ano.csv',
                 'data_local.csv', 'data_redes.csv', 'data_vida_filmes.csv', 'data_sessoes.csv'):
        n = con.execute(f"SELECT count(*) FROM read_csv('{saida / nome}')").fetchone()[0]
        print(nome, n, 'linhas')
    print(con.execute(f"""SELECT "FONTE", sum("PUBLICO"), sum("REGISTROS")
                          FROM read_csv('{saida / 'data_bilheteria.csv'}') GROUP BY 1""").fetchall())
    print('oferta:', con.execute(f"""SELECT "FONTE", sum("PUBLICO"), sum("REGISTROS")
                                     FROM read_csv('{saida / 'data_oferta.csv'}') GROUP BY 1""").fetchall())
    print('sessões:', con.execute(f"""SELECT sum("PUBLICO"), sum("SESSOES") FROM read_csv('{saida / 'data_sessoes.csv'}')""").fetchall())
    con.close()
    shutil.rmtree(temporario, ignore_errors=True)


if __name__ == "__main__":
    main(*sys.argv[1:3])
