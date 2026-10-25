-- =====================================================================
-- Bilheteria diária de cinema (ANCINE) – schema PostgreSQL (>= 15)
-- Derivado de dados/bilheteria_unificada.csv.gz (ver DICIONARIO_DADOS.md,
-- PERFIL_DADOS.md e DECISOES.md).
--
-- Modelo estrela com dois fatos, um por fonte, de granularidades diferentes:
--   fato_bilheteria_distribuidora    dia × obra × sala × distribuidora
--   fato_bilheteria_sessao_exibidora sessão × obra × sala
-- As duas fontes descrevem as MESMAS exibições: nunca some o público das duas.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS bilheteria;
SET search_path TO bilheteria;

-- ---------------------------------------------------------------------
-- Dimensões
-- ---------------------------------------------------------------------

CREATE TABLE dim_data (
    data            date        PRIMARY KEY,
    ano             smallint    NOT NULL,
    mes             smallint    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    dia             smallint    NOT NULL CHECK (dia BETWEEN 1 AND 31),
    dia_semana_iso  smallint    NOT NULL CHECK (dia_semana_iso BETWEEN 1 AND 7),
    semana_iso      smallint    NOT NULL CHECK (semana_iso BETWEEN 1 AND 53)
);
COMMENT ON TABLE  dim_data IS 'Calendário dos dias de exibição (2014-01-01 a 2026-10-18 nos dados atuais).';
COMMENT ON COLUMN dim_data.data IS 'Dia de exibição (data_exibicao). Sessões após a meia-noite pertencem ao dia de exibição anterior.';
COMMENT ON COLUMN dim_data.ano IS 'Ano civil do dia de exibição.';
COMMENT ON COLUMN dim_data.mes IS 'Mês (1–12).';
COMMENT ON COLUMN dim_data.dia IS 'Dia do mês.';
COMMENT ON COLUMN dim_data.dia_semana_iso IS 'Dia da semana ISO: 1 = segunda … 7 = domingo.';
COMMENT ON COLUMN dim_data.semana_iso IS 'Semana ISO 8601 do ano.';

CREATE TABLE dim_uf (
    uf      char(2)     PRIMARY KEY CHECK (uf ~ '^[A-Z]{2}$'),
    regiao  varchar(12) NOT NULL CHECK (regiao IN ('NORTE','NORDESTE','CENTRO-OESTE','SUDESTE','SUL'))
);
COMMENT ON TABLE  dim_uf IS 'Unidades da federação presentes em uf_sala_complexo, com a região do IBGE (mapeamento fixo, derivado).';
COMMENT ON COLUMN dim_uf.uf IS 'Sigla da UF (uf_sala_complexo).';
COMMENT ON COLUMN dim_uf.regiao IS 'Região geográfica do IBGE. Não existe nos dados de origem; é derivada da UF.';

CREATE TABLE dim_obra (
    id_obra          integer      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpb_roe          varchar(14),
    titulo_original  varchar(150),
    titulo_brasil    varchar(150),
    pais_obra        varchar(60),
    CONSTRAINT uq_obra UNIQUE NULLS NOT DISTINCT (cpb_roe, titulo_original, titulo_brasil, pais_obra),
    CONSTRAINT ck_cpb_formato CHECK (cpb_roe ~ '^[A-Z][0-9]{12,13}$')
);
CREATE INDEX ix_obra_cpb ON dim_obra (cpb_roe);
COMMENT ON TABLE  dim_obra IS 'Obras audiovisuais. Uma linha por combinação distinta de CPB/ROE, títulos e país: o CPB não é único (o código genérico E1300000100000 cobre vários filmes antigos), e 35 linhas não têm CPB.';
COMMENT ON COLUMN dim_obra.id_obra IS 'Chave substituta.';
COMMENT ON COLUMN dim_obra.cpb_roe IS 'Certificado de Produto Brasileiro (B…) ou Registro de Obra Estrangeira (E…) na ANCINE. Normalmente 14 caracteres; 3 linhas têm 13.';
COMMENT ON COLUMN dim_obra.titulo_original IS 'Título original da obra, como informado.';
COMMENT ON COLUMN dim_obra.titulo_brasil IS 'Título de lançamento no Brasil. Nulo quando igual ao original.';
COMMENT ON COLUMN dim_obra.pais_obra IS 'País (ou países) de produção, como informado.';

CREATE TABLE dim_grupo_exibidor (
    registro_grupo_exibidor  varchar(10) PRIMARY KEY CHECK (registro_grupo_exibidor ~ '^[0-9]+$')
);
COMMENT ON TABLE  dim_grupo_exibidor IS 'Grupos exibidores (redes). A origem traz só o código de registro, sem nome.';
COMMENT ON COLUMN dim_grupo_exibidor.registro_grupo_exibidor IS 'Registro do grupo exibidor na ANCINE.';

CREATE TABLE dim_exibidora (
    registro_exibidor        varchar(10)  PRIMARY KEY CHECK (registro_exibidor ~ '^[0-9]+$'),
    cnpj_exibidora           char(18)     CHECK (cnpj_exibidora ~ '^[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}$'),
    razao_social_exibidora   varchar(120),
    registro_grupo_exibidor  varchar(10)  REFERENCES dim_grupo_exibidor
);
CREATE UNIQUE INDEX uq_exibidora_cnpj ON dim_exibidora (cnpj_exibidora);
COMMENT ON TABLE  dim_exibidora IS 'Empresas exibidoras. REGISTRO_EXIBIDOR e CNPJ são 1:1 na fonte exibidora. Exibidores vistos só na fonte distribuidor ficam com CNPJ e razão social nulos.';
COMMENT ON COLUMN dim_exibidora.registro_exibidor IS 'Registro da empresa exibidora na ANCINE.';
COMMENT ON COLUMN dim_exibidora.cnpj_exibidora IS 'CNPJ da exibidora, com máscara (fonte exibidora).';
COMMENT ON COLUMN dim_exibidora.razao_social_exibidora IS 'Razão social da exibidora (valor mais frequente para o CNPJ).';
COMMENT ON COLUMN dim_exibidora.registro_grupo_exibidor IS 'Grupo ao qual a exibidora pertence; nulo para exibidoras independentes.';

CREATE TABLE dim_complexo (
    registro_complexo        varchar(10)  PRIMARY KEY CHECK (registro_complexo ~ '^[0-9]+$'),
    registro_exibidor        varchar(10)  REFERENCES dim_exibidora,
    municipio_sala_complexo  varchar(60),
    uf                       char(2)      REFERENCES dim_uf
);
CREATE INDEX ix_complexo_uf ON dim_complexo (uf);
COMMENT ON TABLE  dim_complexo IS 'Complexos de cinema (conjunto de salas num endereço). Cada complexo tem um único exibidor e uma única UF.';
COMMENT ON COLUMN dim_complexo.registro_complexo IS 'Registro do complexo na ANCINE.';
COMMENT ON COLUMN dim_complexo.registro_exibidor IS 'Exibidora que opera o complexo.';
COMMENT ON COLUMN dim_complexo.municipio_sala_complexo IS 'Município do complexo.';
COMMENT ON COLUMN dim_complexo.uf IS 'UF do complexo.';

CREATE TABLE dim_sala (
    registro_sala      varchar(10)  PRIMARY KEY CHECK (registro_sala ~ '^[0-9]+$'),
    nome_sala          varchar(100) NOT NULL,
    registro_complexo  varchar(10)  REFERENCES dim_complexo
);
CREATE INDEX ix_sala_complexo ON dim_sala (registro_complexo);
COMMENT ON TABLE  dim_sala IS 'Salas de exibição registradas. O nome vem da fonte exibidora (1 nome por registro) ou, na falta dela, do nome mais frequente na fonte distribuidor.';
COMMENT ON COLUMN dim_sala.registro_sala IS 'Registro da sala na ANCINE.';
COMMENT ON COLUMN dim_sala.nome_sala IS 'Nome canônico da sala.';
COMMENT ON COLUMN dim_sala.registro_complexo IS 'Complexo ao qual a sala pertence.';

CREATE TABLE dim_distribuidora (
    id_distribuidora            integer      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cnpj_distribuidora          varchar(18)  NOT NULL
        CHECK (cnpj_distribuidora ~ '^[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}$' OR cnpj_distribuidora = 'PESSOA FÍSICA'),
    razao_social_distribuidora  varchar(120) NOT NULL,
    CONSTRAINT uq_distribuidora UNIQUE (cnpj_distribuidora, razao_social_distribuidora)
);
CREATE INDEX ix_distribuidora_cnpj ON dim_distribuidora (cnpj_distribuidora);
COMMENT ON TABLE  dim_distribuidora IS 'Distribuidoras. A chave é substituta porque o CNPJ não é único: o valor literal "PESSOA FÍSICA" agrupa pessoas físicas distribuidoras com razões sociais diferentes.';
COMMENT ON COLUMN dim_distribuidora.id_distribuidora IS 'Chave substituta.';
COMMENT ON COLUMN dim_distribuidora.cnpj_distribuidora IS 'CNPJ com máscara, ou o texto "PESSOA FÍSICA".';
COMMENT ON COLUMN dim_distribuidora.razao_social_distribuidora IS 'Razão social (ou nome da pessoa física) da distribuidora.';

-- ---------------------------------------------------------------------
-- Fatos
-- ---------------------------------------------------------------------

CREATE TABLE fato_bilheteria_distribuidora (
    id                         bigint       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_exibicao              date         NOT NULL REFERENCES dim_data,
    id_obra                    integer      NOT NULL REFERENCES dim_obra,
    registro_sala              varchar(10)  REFERENCES dim_sala,
    nome_sala                  varchar(100),
    registro_exibidor          varchar(10)  REFERENCES dim_exibidora,
    registro_grupo_exibidor    varchar(10)  REFERENCES dim_grupo_exibidor,
    registro_complexo          varchar(10)  REFERENCES dim_complexo,
    municipio_sala_complexo    varchar(60),
    uf                         char(2)      REFERENCES dim_uf,
    id_distribuidora           integer      NOT NULL REFERENCES dim_distribuidora,
    publico                    integer      NOT NULL CHECK (publico >= 0),
    nr_protocolo_envio         varchar(20)  NOT NULL CHECK (nr_protocolo_envio ~ '^[0-9]+$'),
    data_hora_envio_protocolo  timestamp,
    arquivo_origem             varchar(80)  NOT NULL
);
CREATE INDEX ix_fd_data            ON fato_bilheteria_distribuidora (data_exibicao);
CREATE INDEX ix_fd_obra_data       ON fato_bilheteria_distribuidora (id_obra, data_exibicao);
CREATE INDEX ix_fd_distrib_data    ON fato_bilheteria_distribuidora (id_distribuidora, data_exibicao);
CREATE INDEX ix_fd_uf_data         ON fato_bilheteria_distribuidora (uf, data_exibicao);
CREATE INDEX ix_fd_exibicao        ON fato_bilheteria_distribuidora (data_exibicao, registro_sala, id_obra);
COMMENT ON TABLE  fato_bilheteria_distribuidora IS 'Público por dia × obra × sala × distribuidora, informado pelas distribuidoras (21.655.622 linhas; 2014-01-01 a 2026-09-30). Em co-distribuição, a mesma exibição aparece uma vez por distribuidora: para total de público, deduplique por (data_exibicao, registro_sala, nome_sala, id_obra).';
COMMENT ON COLUMN fato_bilheteria_distribuidora.id IS 'Chave substituta (não há chave natural única: 96 repetições por reenvio de protocolo).';
COMMENT ON COLUMN fato_bilheteria_distribuidora.data_exibicao IS 'Dia de exibição.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.id_obra IS 'Obra exibida.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.registro_sala IS 'Sala; nula em 568.397 linhas, sobretudo de 2014–2015.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.nome_sala IS 'Nome da sala como informado pela distribuidora; é o único identificador quando registro_sala é nulo.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.registro_exibidor IS 'Exibidora da sala, como informado (desnormalizado, pois a sala pode faltar).';
COMMENT ON COLUMN fato_bilheteria_distribuidora.registro_grupo_exibidor IS 'Grupo exibidor, como informado.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.registro_complexo IS 'Complexo, como informado.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.municipio_sala_complexo IS 'Município, como informado (mantido porque a sala pode faltar).';
COMMENT ON COLUMN fato_bilheteria_distribuidora.uf IS 'UF, como informada; nula em 521.800 linhas.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.id_distribuidora IS 'Distribuidora que informou a linha.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.publico IS 'Número de espectadores no dia, na sala, para a obra.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.nr_protocolo_envio IS 'Protocolo de envio do relatório à ANCINE.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.data_hora_envio_protocolo IS 'Data e hora do envio do protocolo; nula em protocolos antigos.';
COMMENT ON COLUMN fato_bilheteria_distribuidora.arquivo_origem IS 'Nome do CSV mensal de origem.';

CREATE TABLE fato_bilheteria_sessao_exibidora (
    id                 bigint       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_exibicao      date         NOT NULL REFERENCES dim_data,
    sessao             timestamp    NOT NULL,
    id_obra            integer      NOT NULL REFERENCES dim_obra,
    registro_sala      varchar(10)  NOT NULL REFERENCES dim_sala,
    registro_exibidor  varchar(10)  NOT NULL REFERENCES dim_exibidora,
    audio              varchar(8)   NOT NULL CHECK (audio IN ('DUBLADO','ORIGINAL')),
    legendada          boolean      NOT NULL,
    publico            integer      NOT NULL CHECK (publico >= 0),
    arquivo_origem     varchar(80)  NOT NULL,
    CONSTRAINT ck_sessao_no_dia CHECK (sessao::date BETWEEN data_exibicao AND data_exibicao + 1)
);
CREATE INDEX ix_fe_data           ON fato_bilheteria_sessao_exibidora (data_exibicao);
CREATE INDEX ix_fe_obra_data      ON fato_bilheteria_sessao_exibidora (id_obra, data_exibicao);
CREATE INDEX ix_fe_exibidor_data  ON fato_bilheteria_sessao_exibidora (registro_exibidor, data_exibicao);
CREATE INDEX ix_fe_sala_data      ON fato_bilheteria_sessao_exibidora (registro_sala, data_exibicao);
COMMENT ON TABLE  fato_bilheteria_sessao_exibidora IS 'Público por sessão, informado pelas exibidoras (38.401.117 linhas; 2014-06-01 a 2026-10-18, cobertura quase nula até meados de 2016). UF, município e grupo vêm por dim_sala → dim_complexo → dim_exibidora.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.id IS 'Chave substituta (sessão + sala + obra se repete em 605 linhas).';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.data_exibicao IS 'Dia de exibição.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.sessao IS 'Data e hora de início da sessão; pode cair no dia seguinte (sessões após a meia-noite).';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.id_obra IS 'Obra exibida.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.registro_sala IS 'Sala da sessão.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.registro_exibidor IS 'Exibidora que informou a sessão.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.audio IS 'Áudio da cópia: DUBLADO ou ORIGINAL.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.legendada IS 'Sessão legendada (origem: SIM/NÃO).';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.publico IS 'Número de espectadores na sessão.';
COMMENT ON COLUMN fato_bilheteria_sessao_exibidora.arquivo_origem IS 'Nome do CSV semanal de origem.';

-- ---------------------------------------------------------------------
-- Vista para o dashboard: público diário por UF, sem somar fontes
-- ---------------------------------------------------------------------
CREATE VIEW vw_publico_diario_uf AS
SELECT 'DISTRIBUIDOR'::text AS fonte, data_exibicao, uf, sum(publico) AS publico, count(*) AS registros
FROM (
    SELECT data_exibicao, max(uf) AS uf, max(publico) AS publico
    FROM fato_bilheteria_distribuidora
    GROUP BY data_exibicao, registro_sala, nome_sala, id_obra      -- deduplica co-distribuição
) d
GROUP BY data_exibicao, uf
UNION ALL
SELECT 'EXIBIDORA', f.data_exibicao, c.uf, sum(f.publico), count(*)
FROM fato_bilheteria_sessao_exibidora f
JOIN dim_sala s USING (registro_sala)
JOIN dim_complexo c USING (registro_complexo)
GROUP BY f.data_exibicao, c.uf;
COMMENT ON VIEW vw_publico_diario_uf IS 'Equivalente SQL de projeto_completo/data_bilheteria.csv: público diário por UF e fonte, com co-distribuição deduplicada. Não some as duas fontes.';

-- ---------------------------------------------------------------------
-- Carga (não executada neste projeto; ver DECISOES.md). Roteiro em psql:
--   CREATE TEMP TABLE stg (fonte text, arquivo_origem text, data_exibicao date, sessao timestamp,
--     titulo_original text, titulo_brasil text, cpb_roe text, pais_obra text, audio text, legendada text,
--     registro_sala text, nome_sala text, publico integer, registro_grupo_exibidor text,
--     registro_exibidor text, registro_complexo text, municipio_sala_complexo text, uf_sala_complexo text,
--     razao_social_distribuidora text, cnpj_distribuidora text, nr_protocolo_envio text,
--     data_hora_envio_protocolo timestamp, razao_social_exibidora text, cnpj_exibidora text);
--   \copy stg FROM PROGRAM 'gunzip -c dados/bilheteria_unificada.csv.gz' WITH (FORMAT csv, HEADER true)
--   -- depois: INSERT nas dimensões com SELECT DISTINCT (nomes pelo valor mais frequente)
--   -- e nos fatos com JOIN nas dimensões, filtrando stg.fonte.
--   -- Conferência: SELECT fonte, count(*) FROM stg GROUP BY 1;  -- 21.655.622 / 38.401.117
-- ---------------------------------------------------------------------
