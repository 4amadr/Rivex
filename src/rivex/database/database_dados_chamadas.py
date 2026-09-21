import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os
from src.rivex.utils.logging_config.logging_database import logging_database
from src.rivex.database.config_database import ConexaoDatabaseRivex, DatabaseBase
from src.rivex.utils.infra_utils.date_config import *

class DatabaseClientesCallix:
    def __init__(self, query_insert_cliente):
        self.db = ConexaoDatabaseRivex()
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao
        self.query_insert_clientes_callix = query_insert_cliente

    def criar_tabela_cliente(self, query_criar_tabela):
        try:
            self.cursor.execute(query_criar_tabela)
            log.info("Tabela de informações de clientes criadas")
            self.conexao.commit()
        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao criar tabelas: %s", erro)
            raise

    def enviar_info_cliente(self, dados_cliente):
        try:
            self.cursor.execute(
                self.query_insert_clientes_callix,
                dados_cliente
            )

            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error(
                "Erro ao inserir cliente Callix: %s",
                erro
            )
            raise
