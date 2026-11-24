from __future__ import annotations

from typing import Optional

from src.rivex.config.settings import DatabaseSettings
from src.rivex.database.config_database import ConexaoDatabaseRivex
from src.rivex.utils.logging_config import LoadLogger


class DatabaseClientesVonix:
    """Gerencia o vínculo imutável equipe -> tech em ``clientes.clientes_vonix``."""

    def __init__(
        self,
        conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
        db_settings: Optional[DatabaseSettings] = None,
    ):
        self.load_log = LoadLogger("vonix")
        self._possui_conexao = conexao_compartilhada is None
        self.db = conexao_compartilhada or ConexaoDatabaseRivex(db_settings=db_settings)
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao

        self.query_criar_schema = "CREATE SCHEMA IF NOT EXISTS clientes;"
        self.query_criar_tabela = """
            CREATE TABLE IF NOT EXISTS clientes.clientes_vonix (
                equipe TEXT NOT NULL,
                tech INTEGER NOT NULL CHECK (tech > 0),
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (equipe)
            );
        """
        self.query_criar_view = """
            CREATE OR REPLACE VIEW clientes.vw_clientes_vonix_ativos AS
            SELECT
                equipe,
                tech
            FROM clientes.clientes_vonix
            WHERE ativo = TRUE;
        """
        self.query_listar_todos = """
            SELECT equipe, tech
            FROM clientes.clientes_vonix
            ORDER BY equipe;
        """
        self.query_listar_ativos = """
            SELECT equipe, tech
            FROM clientes.vw_clientes_vonix_ativos
            ORDER BY equipe;
        """
        self.query_inserir_imutavel = """
            INSERT INTO clientes.clientes_vonix (equipe, tech, ativo, atualizado_em)
            VALUES (%s, %s, TRUE, NOW())
            ON CONFLICT (equipe) DO NOTHING;
        """
        self.query_buscar_por_equipe = """
            SELECT tech
            FROM clientes.clientes_vonix
            WHERE equipe = %s;
        """

        try:
            self.cursor.execute(self.query_criar_schema)
            self.cursor.execute(self.query_criar_tabela)
            self.cursor.execute(self.query_criar_view)
            self.conexao.commit()
        except Exception as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db("criar_tabela_clientes_vonix", erro)
            raise

    def carregar_mapa_techs(self, apenas_ativos: bool = False) -> dict[str, int]:
        """Retorna mapeamento ``{equipe: tech}`` persistido em ``clientes.clientes_vonix``."""
        query = self.query_listar_ativos if apenas_ativos else self.query_listar_todos
        try:
            self.cursor.execute(query)
            return {equipe: int(tech) for equipe, tech in self.cursor.fetchall()}
        except Exception as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db("carregar_mapa_techs_vonix", erro)
            raise

    def registrar_tech(self, equipe: str, tech: int) -> int:
        """Persiste ``(equipe, tech)`` sem sobrescrever vínculos já existentes."""
        equipe_norm = (equipe or "").strip()
        if not equipe_norm:
            raise ValueError("Campo 'equipe' não pode ser vazio.")
        if int(tech) <= 0:
            raise ValueError(f"Tech inválida para equipe '{equipe_norm}': {tech}")

        try:
            self.cursor.execute(self.query_inserir_imutavel, (equipe_norm, int(tech)))
            self.cursor.execute(self.query_buscar_por_equipe, (equipe_norm,))
            row = self.cursor.fetchone()
            self.conexao.commit()
            return int(row[0]) if row else int(tech)
        except Exception as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db("registrar_tech_vonix", erro, cliente=equipe_norm)
            raise

    def fechar(self) -> None:
        if self._possui_conexao:
            self.db.fechar_db(self.cursor, self.conexao)
