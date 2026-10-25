"""Gera o CSV unificado (distribuidoras + exibidoras) e a conferência de contagens.

Uso: python -I pipeline/unificar.py <dir_staging> <perfil_json> <saida_csv_gz> <saida_json>

Lê o staging Parquet gerado por perfil.py (cópia textual, sem perda, dos CSVs originais,
já conferida linha a linha contra a varredura dos arquivos), padroniza nomes em snake_case,
datas em ISO 8601 e público como inteiro, e grava um único CSV UTF-8 compactado (gzip).
Nenhuma linha é descartada, deduplicada ou agregada.
"""
import json
import sys
from pathlib import Path

import duckdb

# Ordem final das colunas: controle, comuns às duas fontes, exclusivas de cada fonte.
COLUNAS = [
    "fonte", "arquivo_origem", "data_exibicao", "sessao",
    "titulo_original", "titulo_brasil", "cpb_roe", "pais_obra",
    "audio", "legendada",
    "registro_sala", "nome_sala", "publico",
    "registro_grupo_exibidor", "registro_exibidor", "registro_complexo",
    "municipio_sala_complexo", "uf_sala_complexo",
    "razao_social_distribuidora", "cnpj_distribuidora", "nr_protocolo_envio", "data_hora_envio_protocolo",
    "razao_social_exibidora", "cnpj_exibidora",
]
CONVERSOES = {
    "data_exibicao": ("DATA_EXIBICAO", "try_strptime(DATA_EXIBICAO, '%d/%m/%Y')::DATE"),
    "sessao": ("SESSAO", "try_strptime(SESSAO, '%d/%m/%Y %H:%M:%S')"),
    "data_hora_envio_protocolo": ("DATA_HORA_ENVIO_PROTOCOLO", "try_strptime(DATA_HORA_ENVIO_PROTOCOLO, '%d/%m/%Y %H:%M:%S')"),
    "publico": ("PUBLICO", "try_cast(PUBLICO AS BIGINT)"),
}


def select_fonte(con, parquet: Path, fonte: str) -> str:
    origem = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet}')").fetchall()}
    partes = []
    for col in COLUNAS:
        if col == "fonte":
            partes.append(f"'{fonte}' AS fonte")
        elif col == "arquivo_origem":
            partes.append("filename AS arquivo_origem")
        elif col.upper() not in origem:
            tipo = "TIMESTAMP" if col == "sessao" or col.startswith("data_hora") else "VARCHAR"
            partes.append(f"NULL::{tipo} AS {col}")
        elif col in CONVERSOES:
            partes.append(f"{CONVERSOES[col][1]} AS {col}")
        else:
            # texto preservado como veio; só a string vazia vira nulo
            partes.append(f"NULLIF(\"{col.upper()}\", '') AS {col}")
    return f"SELECT {', '.join(partes)} FROM read_parquet('{parquet}')"


def main(dir_staging: str, perfil_json: str, saida_csv: str, saida_json: str) -> None:
    staging = Path(dir_staging)
    perfil = json.loads(Path(perfil_json).read_text(encoding="utf-8"))
    con = duckdb.connect()
    con.execute("SET memory_limit='10GB'; SET preserve_insertion_order=false;")
    con.execute(f"SET temp_directory='{staging / 'tmp'}'")

    selects = {f: select_fonte(con, staging / f"bruto_{f}.parquet", f) for f in perfil["fontes"]}
    rel = {"conversoes_falhas": {}, "contagens": {}}

    # Valores não vazios que não converteram: o campo vira nulo, a linha é mantida.
    for fonte in perfil["fontes"]:
        p = f"read_parquet('{staging / f'bruto_{fonte}.parquet'}')"
        origem = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {p}").fetchall()}
        for col, (bruta, expr) in CONVERSOES.items():
            if bruta not in origem:
                continue
            n, ex = con.execute(f"""
                SELECT count(*), list(DISTINCT {bruta})[1:5] FROM {p}
                WHERE NULLIF({bruta}, '') IS NOT NULL AND ({expr}) IS NULL""").fetchone()
            rel["conversoes_falhas"][f"{fonte}.{col}"] = {"linhas": n, "exemplos": ex}

    consulta = " UNION ALL ".join(f"({s})" for s in selects.values())
    con.execute(f"""
        COPY ({consulta}) TO '{saida_csv}'
        (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', COMPRESSION gzip,
         DATEFORMAT '%Y-%m-%d', TIMESTAMPFORMAT '%Y-%m-%dT%H:%M:%S')
    """)

    # Conferência: relê o CSV gerado (não o staging) e conta por fonte e arquivo.
    lido = f"""read_csv('{saida_csv}', header=true, all_varchar=true, delim=',', quote='"', escape='"',
                         compression='gzip', strict_mode=true)"""
    depois = con.execute(f"SELECT fonte, arquivo_origem, count(*) FROM {lido} GROUP BY ALL").fetchall()
    cab = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {lido}").fetchall()]
    amostra = con.execute(f"""
        SELECT count(*) FILTER (WHERE NOT regexp_full_match(data_exibicao, '\\d{{4}}-\\d{{2}}-\\d{{2}}')),
               count(*) FILTER (WHERE sessao IS NOT NULL AND NOT regexp_full_match(sessao, '\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}')),
               count(*) FILTER (WHERE publico IS NOT NULL AND NOT regexp_full_match(publico, '\\d+'))
        FROM {lido}""").fetchone()
    depois_arq = {(f, a): n for f, a, n in depois}
    for fonte, info in perfil["fontes"].items():
        antes = {x["arquivo"]: x["linhas_dados"] for x in info["por_arquivo"]}
        dif = [(a, n, depois_arq.get((fonte, a), 0)) for a, n in antes.items() if n != depois_arq.get((fonte, a), 0)]
        rel["contagens"][fonte] = {
            "arquivos": len(antes), "antes": sum(antes.values()),
            "depois": sum(n for (f, _), n in depois_arq.items() if f == fonte),
            "arquivos_divergentes": dif,
        }
    rel["colunas_csv"] = cab
    rel["formato_invalido_no_csv"] = {"data_exibicao": amostra[0], "sessao": amostra[1], "publico": amostra[2]}
    rel["bytes_csv_gz"] = Path(saida_csv).stat().st_size
    Path(saida_json).write_text(json.dumps(rel, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(rel["contagens"], ensure_ascii=False), rel["formato_invalido_no_csv"])


if __name__ == "__main__":
    main(*sys.argv[1:5])
