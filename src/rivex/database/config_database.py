from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

from src.rivex.config.settings import DatabaseSettings
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro
from src.rivex.utils.logging_config import LoadLogger, SystemLogger


class ConexaoDatabaseRivex:
    def __init__(self, db_settings: Optional[DatabaseSettings] = None):
        self.system_log = SystemLogger("database")
        self._config = self._carregar_banco(db_settings)
        self.cursor, self.conexao = self.abrir_banco()

    def _carregar_banco(self, db_settings: Optional[DatabaseSettings]) -> dict:
        if db_settings is not None:
            return {
                "host": db_settings.host,
                "database": db_settings.database,
                "user": db_settings.user,
                "password": db_settings.password,
                "port": db_settings.port,
            }
        load_dotenv()
        return {
            "host": os.getenv("HOST_DB"),
            "database": os.getenv("DATABASE_CONTECH"),
            "user": os.getenv("USER_DB"),
            "password": os.getenv("SENHA_DB"),
            "port": os.getenv("PORT_DB") or 5432,
        }

    def abrir_banco(self):
        try:
            self.connection = psycopg2.connect(**self._config)
            self.system_log.info(
                "Conexão com banco de dados estabelecida",
                host=self._config.get("host"),
                database=self._config.get("database"),
            )
            return self.connection.cursor(), self.connection
        except OperationalError as erro_abrir_banco:
            self.system_log.erro("Falha operacional ao abrir banco de dados", erro=erro_abrir_banco)
            raise
        except UnicodeDecodeError as erro_decode:
            self.system_log.erro("Erro de decode nas variáveis de ambiente do banco", erro=erro_decode)
            raise

    def fechar_db(self, cursor=None, conexao=None):
        cur = cursor if cursor is not None else getattr(self, "cursor", None)
        conn = conexao if conexao is not None else getattr(self, "conexao", None)
        if cur:
            cur.close()
        if conn:
            conn.close()
            self.system_log.info("Conexão com banco de dados encerrada")

    def __enter__(self) -> "ConexaoDatabaseRivex":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.fechar_db()


@contextmanager
def conexao_rivex(db_settings: Optional[DatabaseSettings] = None) -> Iterator[ConexaoDatabaseRivex]:
    db = ConexaoDatabaseRivex(db_settings=db_settings)
    try:
        yield db
    finally:
        db.fechar_db()


class DatabaseBase:
    def __init__(
        self,
        query_insert_chamada: str,
        query_insert_operador: str,
        servico: str = "database",
        conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
        db_settings: Optional[DatabaseSettings] = None,
    ):
        self._possui_conexao = conexao_compartilhada is None
        self.db = conexao_compartilhada or ConexaoDatabaseRivex(db_settings=db_settings)
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao
        self.query_insert_chamada = query_insert_chamada
        self.query_insert_operador = query_insert_operador
        self.load_log = LoadLogger(servico)

    def criar_tabelas(
        self,
        query_tabela_chamadas: str,
        query_tabela_agentes: str,
        migracoes: Optional[list[str]] = None,
    ) -> None:
        try:
            self.cursor.execute(query_tabela_chamadas)
            self.cursor.execute(query_tabela_agentes)
            for sql_migracao in migracoes or []:
                self.cursor.execute(sql_migracao)
            self.conexao.commit()
        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db("criar_tabelas", erro)
            raise

    def enviar_dados(
        self,
        dados_cliente: ClienteRegistro,
        agentes: list[OperadorRegistro],
    ) -> None:
        cliente_dict = dados_cliente.model_dump()
        agentes_dicts = [agente.model_dump() for agente in agentes]
        try:
            self.cursor.execute(self.query_insert_chamada, cliente_dict)
            if agentes_dicts:
                self.cursor.executemany(self.query_insert_operador, agentes_dicts)
            self.conexao.commit()
            self.load_log.registrar_envio_db(
                "enviar_dados",
                total_agentes=len(agentes_dicts),
                cliente=dados_cliente.cliente,
            )
        except Exception as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db(
                "enviar_dados", erro, cliente=dados_cliente.cliente
            )
            raise

    def fechar_db(self) -> None:
        if self._possui_conexao:
            self.db.fechar_db(self.cursor, self.conexao)
