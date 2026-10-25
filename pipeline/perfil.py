"""Perfil dos CSVs de bilheteria diária (ANCINE).

Uso: python -I pipeline/perfil.py <dir_extraido> <dir_staging> - <saida_json>
(o terceiro argumento é reservado; PERFIL_DADOS.md foi redigido a partir do JSON)

1. Varre cada arquivo em Python: codificação (UTF-8 estrito, BOM), cabeçalho, linhas.
2. Carrega cada fonte (todas as colunas como texto) em Parquet de staging via DuckDB,
   com o nome do arquivo de origem; confere a contagem contra a varredura.
3. Calcula nulos, formatos, duplicatas, variantes de nomes e sobreposição entre fontes.
"""
import json
import sys
from pathlib import Path

import duckdb

FONTES = {"distribuidor": "distribuidoras", "exibidora": "exibidoras"}


def varrer_arquivo(caminho: Path) -> dict:
    dados = caminho.read_bytes()
    info = {"arquivo": caminho.name, "bytes": len(dados), "bom": dados.startswith(b"\xef\xbb\xbf")}
    try:
        texto = dados.decode("utf-8")
        info["codificacao"] = "utf-8"
    except UnicodeDecodeError as e:
        texto = dados.decode("latin-1")
        info["codificacao"] = f"latin-1 (UTF-8 inválido no byte {e.start})"
    linhas = texto.splitlines()
    info["cabecalho"] = linhas[0].lstrip("﻿") if linhas else ""
    info["linhas_dados"] = sum(1 for l in linhas[1:] if l.strip())
    info["linhas_vazias"] = sum(1 for l in linhas[1:] if not l.strip())
    info["crlf"] = b"\r\n" in dados[:10000]
    return info


def main(dir_extraido: str, dir_staging: str, saida_md: str, saida_json: str) -> None:
    base = Path(dir_extraido)
    staging = Path(dir_staging)
    staging.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='10GB'; SET preserve_insertion_order=false;")
    con.execute(f"SET temp_directory='{staging / 'tmp'}'")
    rel = {"fontes": {}}

    for fonte, pasta in FONTES.items():
        arquivos = sorted((base / pasta).glob("*.csv"))
        varredura = [varrer_arquivo(a) for a in arquivos]
        cabecalhos = sorted({v["cabecalho"] for v in varredura})
        codificacoes = sorted({v["codificacao"] for v in varredura})
        if len(cabecalhos) != 1:
            raise SystemExit(f"{fonte}: cabeçalhos divergentes entre arquivos: {cabecalhos}")
        parquet = staging / f"bruto_{fonte}.parquet"
        con.execute(f"""
            COPY (
              SELECT * REPLACE (parse_filename(filename) AS filename)
              FROM read_csv('{base / pasta}/*.csv', delim=';', header=true, all_varchar=true,
                            filename=true, quote='"', escape='"',
                            store_rejects=true, rejects_table='rej_{fonte}', rejects_scan='scan_{fonte}')
            ) TO '{parquet}' (FORMAT parquet, COMPRESSION zstd)
        """)
        rejeitadas = con.execute(f"SELECT count(*) FROM rej_{fonte}").fetchone()[0]
        rejeicoes_ex = con.execute(
            f"SELECT file_id, line, error_type, left(csv_line, 200) FROM rej_{fonte} LIMIT 10"
        ).fetchall()
        v = f"read_parquet('{parquet}')"
        cont_arq = dict(con.execute(f"SELECT filename, count(*) FROM {v} GROUP BY 1").fetchall())
        divergentes = [
            (x["arquivo"], x["linhas_dados"], cont_arq.get(x["arquivo"], 0))
            for x in varredura if x["linhas_dados"] != cont_arq.get(x["arquivo"], 0)
        ]
        colunas = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {v}").fetchall() if r[0] != "filename"]
        total = con.execute(f"SELECT count(*) FROM {v}").fetchone()[0]
        nulos = con.execute(
            "SELECT " + ", ".join(f"count(*) - count(NULLIF(trim(\"{c}\"), ''))" for c in colunas) + f" FROM {v}"
        ).fetchone()
        distintos = con.execute(
            "SELECT " + ", ".join(f"approx_count_distinct(\"{c}\")" for c in colunas) + f" FROM {v}"
        ).fetchone()
        datas = con.execute(f"""
            SELECT min(try_strptime(DATA_EXIBICAO, '%d/%m/%Y'))::DATE,
                   max(try_strptime(DATA_EXIBICAO, '%d/%m/%Y'))::DATE,
                   count(*) FILTER (WHERE try_strptime(DATA_EXIBICAO, '%d/%m/%Y') IS NULL),
                   count(DISTINCT DATA_EXIBICAO)
            FROM {v}""").fetchone()
        publico = con.execute(f"""
            SELECT count(*) FILTER (WHERE NOT regexp_full_match(PUBLICO, '[0-9]+')),
                   min(try_cast(PUBLICO AS BIGINT)), max(try_cast(PUBLICO AS BIGINT)),
                   sum(try_cast(PUBLICO AS BIGINT)),
                   count(*) FILTER (WHERE try_cast(PUBLICO AS BIGINT) = 0)
            FROM {v}""").fetchone()
        publico_fora = con.execute(
            f"SELECT PUBLICO, count(*) FROM {v} WHERE NOT regexp_full_match(PUBLICO, '[0-9]+') GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
        ).fetchall()
        hash_cols = ", ".join(f'"{c}"' for c in colunas)
        dup_exatas = con.execute(
            f"SELECT count(*) - count(DISTINCT hash({hash_cols})) FROM {v}"
        ).fetchone()[0]
        titulos_cpb = con.execute(f"""
            SELECT count(*) FROM (SELECT CPB_ROE FROM {v} WHERE CPB_ROE IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT TITULO_ORIGINAL) > 1)""").fetchone()[0]
        titulos_cpb_ex = con.execute(f"""
            SELECT CPB_ROE, list(DISTINCT TITULO_ORIGINAL)[1:4] FROM {v} WHERE CPB_ROE IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT TITULO_ORIGINAL) > 1 ORDER BY count(DISTINCT TITULO_ORIGINAL) DESC LIMIT 5""").fetchall()
        cpb_formato = con.execute(
            f"SELECT count(*) FILTER (WHERE NOT regexp_full_match(CPB_ROE, '[A-Z][0-9]{{13}}')) FROM {v}"
        ).fetchone()[0]
        uf_valores = [r[0] for r in con.execute(f"SELECT DISTINCT UF_SALA_COMPLEXO FROM {v} ORDER BY 1").fetchall()]
        empresa = "DISTRIBUIDORA" if fonte == "distribuidor" else "EXIBIDORA"
        cnpj_col, rs_col = f"CNPJ_{empresa}", f"RAZAO_SOCIAL_{empresa}"
        cnpj_variantes = con.execute(f"""
            SELECT count(*) FROM (SELECT "{cnpj_col}" FROM {v} WHERE "{cnpj_col}" IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT "{rs_col}") > 1)""").fetchone()[0]
        cnpj_variantes_ex = con.execute(f"""
            SELECT "{cnpj_col}", list(DISTINCT "{rs_col}")[1:4] FROM {v} WHERE "{cnpj_col}" IS NOT NULL
            GROUP BY 1 HAVING count(DISTINCT "{rs_col}") > 1 LIMIT 5""").fetchall()
        cnpj_formato = con.execute(
            f"SELECT count(*) FILTER (WHERE NOT regexp_full_match(\"{cnpj_col}\", '[0-9]{{2}}\\.[0-9]{{3}}\\.[0-9]{{3}}/[0-9]{{4}}-[0-9]{{2}}')) FROM {v}"
        ).fetchone()[0]
        extra = {}
        if fonte == "distribuidor":
            extra["data_hora_envio_fora_formato"] = con.execute(f"""
                SELECT count(*) FILTER (WHERE DATA_HORA_ENVIO_PROTOCOLO IS NOT NULL
                  AND try_strptime(DATA_HORA_ENVIO_PROTOCOLO, '%d/%m/%Y %H:%M:%S') IS NULL) FROM {v}""").fetchone()[0]
            extra["chave_dia_sala_obra_distrib_repetida"] = con.execute(f"""
                SELECT count(*) - count(DISTINCT (DATA_EXIBICAO, REGISTRO_SALA, NOME_SALA, CPB_ROE, CNPJ_DISTRIBUIDORA)) FROM {v}""").fetchone()[0]
            extra["grupos_codistribuicao"] = con.execute(f"""
                SELECT count(*) FROM (SELECT 1 FROM {v} GROUP BY DATA_EXIBICAO, REGISTRO_SALA, NOME_SALA, CPB_ROE
                HAVING count(DISTINCT CNPJ_DISTRIBUIDORA) > 1)""").fetchone()[0]
            extra["linhas_em_codistribuicao"] = con.execute(f"""
                SELECT coalesce(sum(n),0) FROM (SELECT count(*) n FROM {v} GROUP BY DATA_EXIBICAO, REGISTRO_SALA, NOME_SALA, CPB_ROE
                HAVING count(DISTINCT CNPJ_DISTRIBUIDORA) > 1)""").fetchone()[0]
        else:
            extra["sessao_fora_formato"] = con.execute(f"""
                SELECT count(*) FILTER (WHERE try_strptime(SESSAO, '%d/%m/%Y %H:%M:%S') IS NULL) FROM {v}""").fetchone()[0]
            extra["sessao_data_diferente_da_exibicao"] = con.execute(f"""
                SELECT count(*) FILTER (WHERE try_strptime(SESSAO, '%d/%m/%Y %H:%M:%S')::DATE
                  <> try_strptime(DATA_EXIBICAO, '%d/%m/%Y')::DATE) FROM {v}""").fetchone()[0]
            extra["chave_sessao_sala_obra_repetida"] = con.execute(f"""
                SELECT count(*) - count(DISTINCT (SESSAO, REGISTRO_SALA, CPB_ROE)) FROM {v}""").fetchone()[0]
            extra["valores_audio"] = con.execute(f"SELECT AUDIO, count(*) FROM {v} GROUP BY 1 ORDER BY 2 DESC").fetchall()
            extra["valores_legendada"] = con.execute(f"SELECT LEGENDADA, count(*) FROM {v} GROUP BY 1 ORDER BY 2 DESC").fetchall()
            extra["arquivos_semana_s_sobrepostos"] = con.execute(f"""
                SELECT count(*) FROM (SELECT DATA_EXIBICAO FROM {v} GROUP BY 1 HAVING count(DISTINCT filename) > 1)""").fetchone()[0]

        rel["fontes"][fonte] = {
            "arquivos": len(arquivos), "bytes": sum(x["bytes"] for x in varredura),
            "codificacoes": codificacoes, "com_bom": sum(x["bom"] for x in varredura),
            "crlf": sum(x["crlf"] for x in varredura),
            "cabecalhos_distintos": cabecalhos, "linhas_varredura": sum(x["linhas_dados"] for x in varredura),
            "linhas_vazias": sum(x["linhas_vazias"] for x in varredura),
            "linhas_duckdb": total, "rejeitadas": rejeitadas, "rejeicoes_exemplo": rejeicoes_ex,
            "arquivos_divergentes": divergentes,
            "colunas": {c: {"nulos": n, "distintos_aprox": d} for c, n, d in zip(colunas, nulos, distintos)},
            "data_min": str(datas[0]), "data_max": str(datas[1]), "datas_invalidas": datas[2], "dias_distintos": datas[3],
            "publico_nao_inteiro": publico[0], "publico_min": publico[1], "publico_max": publico[2],
            "publico_soma": publico[3], "publico_zero": publico[4], "publico_fora_exemplo": publico_fora,
            "duplicatas_exatas": dup_exatas, "cpb_com_varios_titulos": titulos_cpb, "cpb_varios_titulos_ex": titulos_cpb_ex,
            "cpb_fora_formato": cpb_formato, "ufs": uf_valores,
            "cnpj_com_varias_razoes": cnpj_variantes, "cnpj_varias_razoes_ex": cnpj_variantes_ex,
            "cnpj_fora_formato": cnpj_formato, **extra,
            "por_arquivo": varredura,
        }
        print(fonte, total, "linhas;", rejeitadas, "rejeitadas;", len(divergentes), "arquivos divergentes", flush=True)

    # Sobreposição entre fontes: mesma exibição (dia, sala, obra)
    d = f"read_parquet('{staging / 'bruto_distribuidor.parquet'}')"
    e = f"read_parquet('{staging / 'bruto_exibidora.parquet'}')"
    rel["sobreposicao"] = con.execute(f"""
        WITH dd AS (SELECT DATA_EXIBICAO, REGISTRO_SALA, CPB_ROE, max(try_cast(PUBLICO AS BIGINT)) pub
                    FROM {d} WHERE REGISTRO_SALA IS NOT NULL GROUP BY ALL),
             ee AS (SELECT DATA_EXIBICAO, REGISTRO_SALA, CPB_ROE, sum(try_cast(PUBLICO AS BIGINT)) pub
                    FROM {e} GROUP BY ALL),
             j AS (SELECT dd.pub pd, ee.pub pe, dd.CPB_ROE IS NOT NULL in_d, ee.CPB_ROE IS NOT NULL in_e
                   FROM dd FULL JOIN ee USING (DATA_EXIBICAO, REGISTRO_SALA, CPB_ROE))
        SELECT count(*) FILTER (WHERE in_d AND in_e), count(*) FILTER (WHERE in_d AND NOT in_e),
               count(*) FILTER (WHERE in_e AND NOT in_d),
               count(*) FILTER (WHERE in_d AND in_e AND pd = pe),
               sum(pd) FILTER (WHERE in_d AND in_e), sum(pe) FILTER (WHERE in_d AND in_e)
        FROM j""").fetchone()
    rel["publico_ano"] = con.execute(f"""
        SELECT ano, sum(pd), sum(pe) FROM (
          SELECT year(strptime(DATA_EXIBICAO,'%d/%m/%Y')) ano, try_cast(PUBLICO AS BIGINT) pd, NULL::BIGINT pe FROM {d}
          UNION ALL
          SELECT year(strptime(DATA_EXIBICAO,'%d/%m/%Y')), NULL, try_cast(PUBLICO AS BIGINT) FROM {e})
        GROUP BY 1 ORDER BY 1""").fetchall()
    rel["registro_sala_vazio_por_ano_distrib"] = con.execute(f"""
        SELECT year(strptime(DATA_EXIBICAO,'%d/%m/%Y')) ano, count(*) FILTER (WHERE REGISTRO_SALA IS NULL), count(*)
        FROM {d} GROUP BY 1 ORDER BY 1""").fetchall()

    Path(saida_json).write_text(json.dumps(rel, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("ok", saida_json)


if __name__ == "__main__":
    main(*sys.argv[1:5])
