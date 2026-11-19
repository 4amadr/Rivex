from __future__ import annotations

from typing import Optional

from src.rivex.config.settings import DatabaseSettings
from src.rivex.database.config_database import ConexaoDatabaseRivex
from src.rivex.utils.logging_config.logging_config import LoggingDatabaseConfig


class DatabaseClientes:
    """Consulta as equipes ativas do Callix e seus tokens na base local."""

    def __init__(
        self,
        conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
        db_settings: Optional[DatabaseSettings] = None,
    ):
        self.log_db = LoggingDatabaseConfig()
        self._possui_conexao = conexao_compartilhada is None
        self.db = conexao_compartilhada or ConexaoDatabaseRivex(db_settings=db_settings)
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao

        self.query_criar_tabela_clientes = """
            CREATE TABLE IF NOT EXISTS clientes.clientes_callix (
                equipe TEXT NOT NULL,
                cliente_token TEXT,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                PRIMARY KEY (equipe)
            );
        """

        self.query_migrar_tabela_clientes = """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'clientes'
                      AND table_name = 'clientes_callix'
                      AND column_name = 'cliente_nome'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'clientes'
                      AND table_name = 'clientes_callix'
                      AND column_name = 'equipe'
                ) THEN
                    ALTER TABLE clientes.clientes_callix RENAME COLUMN cliente_nome TO equipe;
                END IF;
            END $$;
        """

        self.query_dropar_view_antiga = "DROP VIEW IF EXISTS clientes.vw_clientes_ativos;"

        self.query_criar_view_clientes_ativos = """
            CREATE OR REPLACE VIEW clientes.vw_clientes_ativos AS
            SELECT
                equipe,
                cliente_token
            FROM clientes.clientes_callix
            WHERE ativo = TRUE;
        """

        self.query_consultar_clientes_ativos = """
            SELECT equipe, cliente_token
            FROM clientes.vw_clientes_ativos
            ORDER BY equipe;
        """

        try:
            self.cursor.execute(self.query_criar_tabela_clientes)
            self.cursor.execute(self.query_migrar_tabela_clientes)
            self.cursor.execute(self.query_dropar_view_antiga)
            self.cursor.execute(self.query_criar_view_clientes_ativos)
            self.conexao.commit()
        except Exception as erro:
            self.conexao.rollback()
            self.log_db.erro_configuracao(erro)
            raise

    def consultar_view(self) -> list[dict]:
        try:
            self.cursor.execute(self.query_consultar_clientes_ativos)
            clientes_ativos = self.cursor.fetchall()
            return [
                {"cliente": equipe, "token": cliente_token}
                for equipe, cliente_token in clientes_ativos
            ]
        except Exception as erro:
            self.conexao.rollback()
            self.log_db.erro_consulta(self.query_consultar_clientes_ativos, erro)
            raise

    def fechar(self) -> None:
        if self._possui_conexao:
            self.db.fechar_db(self.cursor, self.conexao)
