from __future__ import annotations

import re
from datetime import date
from typing import Mapping, Optional

import psycopg2
from psycopg2 import sql

from src.rivex.config.settings import DatabaseSettings
from src.rivex.database.config_database import ConexaoDatabaseRivex, conexao_rivex
from src.rivex.utils.logging_config import LoadLogger

SCHEMA_INDICADORES = "indicadores"
TABELA_DESEMPENHO = "desempenho_pipeline"
COLUNAS_RESERVADAS = frozenset({"data", "total"})


def normalizar_coluna_pipeline(nome_pipeline: str) -> str:
    """Normaliza o nome de uma pipeline para um identificador SQL seguro."""
    bruto = (nome_pipeline or "").strip().lower()
    normalizado = re.sub(r"[^a-z0-9_]", "_", bruto)
    normalizado = re.sub(r"_+", "_", normalizado).strip("_")
    if not normalizado:
        raise ValueError(f"Nome de pipeline inválido para coluna SQL: {nome_pipeline!r}")
    if normalizado[0].isdigit():
        normalizado = f"p_{normalizado}"
    if normalizado in COLUNAS_RESERVADAS:
        raise ValueError(
            f"Nome de pipeline {nome_pipeline!r} conflita com coluna reservada ({sorted(COLUNAS_RESERVADAS)})."
        )
    return normalizado


class DatabaseDesempenhoPipeline:
    """Persiste os tempos de execução das pipelines em ``indicadores.desempenho_pipeline``.

    Expande automaticamente o schema da tabela adicionando novas colunas sempre que
    uma nova pipeline for registrada.
    """

    def __init__(
        self,
        conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
        db_settings: Optional[DatabaseSettings] = None,
    ):
        self._possui_conexao = conexao_compartilhada is None
        self.db = conexao_compartilhada or ConexaoDatabaseRivex(db_settings=db_settings)
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao
        self.load_log = LoadLogger("database")

    def garantir_estrutura(self, colunas_pipelines: list[str]) -> None:
        """Garante schema, tabela, colunas base (data, total) e colunas dinâmicas por pipeline."""
        tabela = sql.Identifier(SCHEMA_INDICADORES, TABELA_DESEMPENHO)
        try:
            self.cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(
                    sql.Identifier(SCHEMA_INDICADORES)
                )
            )
            self.cursor.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {} (
                        data DATE PRIMARY KEY,
                        total DOUBLE PRECISION NOT NULL DEFAULT 0
                    );
                    """
                ).format(tabela)
            )
            self.cursor.execute(
                sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS data DATE;").format(tabela)
            )
            self.cursor.execute(
                sql.SQL(
                    "ALTER TABLE {} ADD COLUMN IF NOT EXISTS total DOUBLE PRECISION NOT NULL DEFAULT 0;"
                ).format(tabela)
            )
            self.cursor.execute(
                sql.SQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_desempenho_pipeline_data ON {} (data);"
                ).format(tabela)
            )
            for coluna in colunas_pipelines:
                self.cursor.execute(
                    sql.SQL(
                        "ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} DOUBLE PRECISION;"
                    ).format(tabela, sql.Identifier(coluna))
                )
            self.conexao.commit()
        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db("garantir_estrutura_desempenho", erro)
            raise

    def _listar_colunas_pipelines_existentes(self) -> list[str]:
        self.cursor.execute(
            """
            SELECT a.attname
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s
              AND c.relname = %s
              AND a.attnum > 0
              AND NOT a.attisdropped
            ORDER BY a.attnum;
            """,
            (SCHEMA_INDICADORES, TABELA_DESEMPENHO),
        )
        return [
            row[0]
            for row in self.cursor.fetchall()
            if row[0] not in COLUNAS_RESERVADAS
        ]

    def enviar_desempenho(
        self,
        data_ref: date,
        tempos_pipelines: Mapping[str, float],
        total: Optional[float] = None,
    ) -> None:
        """Insere ou atualiza o desempenho das pipelines para ``data_ref``.

        Quando executado para um subconjunto de pipelines na mesma data, preserva as
        colunas das demais pipelines já gravadas e recalcula ``total`` como a soma de
        todas as colunas de pipeline naquela linha.
        """
        tempos_norm: dict[str, float] = {
            normalizar_coluna_pipeline(nome): round(float(duracao), 2)
            for nome, duracao in tempos_pipelines.items()
        }
        if not tempos_norm:
            return

        colunas_novas = list(tempos_norm.keys())
        self.garantir_estrutura(colunas_novas)

        colunas_todas = self._listar_colunas_pipelines_existentes()
        for col in colunas_novas:
            if col not in colunas_todas:
                colunas_todas.append(col)

        total_insert = (
            round(float(total), 2)
            if total is not None
            else round(sum(tempos_norm.values()), 2)
        )

        tabela = sql.Identifier(SCHEMA_INDICADORES, TABELA_DESEMPENHO)
        colunas_insert = ["data", *colunas_novas, "total"]
        valores_insert = [data_ref, *(tempos_norm[c] for c in colunas_novas), total_insert]

        set_clauses = [
            sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
            for col in colunas_novas
        ]

        termos_soma_total = [
            (
                sql.SQL("COALESCE(EXCLUDED.{col}, 0)").format(col=sql.Identifier(col))
                if col in tempos_norm
                else sql.SQL("COALESCE({tabela}.{col}, 0)").format(
                    tabela=tabela, col=sql.Identifier(col)
                )
            )
            for col in colunas_todas
        ]
        expressao_total = sql.SQL("ROUND(({soma})::numeric, 2)::double precision").format(
            soma=sql.SQL(" + ").join(termos_soma_total)
        )
        set_clauses.append(sql.SQL("total = {expr}").format(expr=expressao_total))

        query = sql.SQL(
            """
            INSERT INTO {tabela} ({colunas})
            VALUES ({placeholders})
            ON CONFLICT (data) DO UPDATE SET
                {updates};
            """
        ).format(
            tabela=tabela,
            colunas=sql.SQL(", ").join(sql.Identifier(c) for c in colunas_insert),
            placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in colunas_insert),
            updates=sql.SQL(", ").join(set_clauses),
        )

        try:
            self.cursor.execute(query, valores_insert)
            self.conexao.commit()
            self.load_log.registrar_envio_db(
                "enviar_desempenho_pipeline",
                total_agentes=len(colunas_novas),
                cliente=f"data={data_ref} total={total_insert}s",
            )
        except Exception as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db(
                "enviar_desempenho_pipeline", erro, cliente=f"data={data_ref}"
            )
            raise

    def fechar_db(self) -> None:
        if self._possui_conexao:
            self.db.fechar_db(self.cursor, self.conexao)


def enviar_desempenho_pipeline(
    data_ref: date,
    tempos_pipelines: Mapping[str, float],
    total: Optional[float] = None,
    db_settings: Optional[DatabaseSettings] = None,
    conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
) -> None:
    """Função de envio dos dados de tempo de execução para ``indicadores.desempenho_pipeline``."""
    if not tempos_pipelines:
        return
    if conexao_compartilhada is not None:
        db = DatabaseDesempenhoPipeline(conexao_compartilhada=conexao_compartilhada)
        db.enviar_desempenho(data_ref=data_ref, tempos_pipelines=tempos_pipelines, total=total)
        return

    with conexao_rivex(db_settings) as conn:
        db = DatabaseDesempenhoPipeline(conexao_compartilhada=conn)
        db.enviar_desempenho(data_ref=data_ref, tempos_pipelines=tempos_pipelines, total=total)
