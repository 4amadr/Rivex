import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os
from src.rivex.utils.logging_config.logging_database import logging_database
from src.rivex.database.config_database import ConexaoDatabaseRivex, DatabaseBase



class DatabaseTelefonia:
    def __init__(self, query_insert_telefonia):
         self.db = ConexaoDatabaseRivex()
         self.cursor = self.db.cursor
         self.conexao = self.db.conexao
         self.query_insert_telefonia = query_insert_telefonia
         self.log = LoggingDatabase()

    def criar_tabelas(self, query_tabela_telefonia):
        try:
            self.cursor.execute(query_tabela_telefonia)
            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.log.erro_configuracao(erro)
            raise

    def enviar_dados_telefonia(self, dados):
        try:
            self.cursor.execute(self.query_insert_telefonia, dados)
            self.conexao.commit()
            self.log.conferencia_dados(dados)

        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.log.registro_erro_envio(dados, erro)
            raise

    def fechar_db(self):
        self.db.fechar_db(
            self.cursor,
            self.conexao
        )