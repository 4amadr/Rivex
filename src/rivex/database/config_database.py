import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os
import logging
from src.rivex.utils.logging_config.logging_database

log = logging.getLogger(__name__)


class ConexaoDatabaseRivex:
    def __init__(self):
        load_dotenv()
        self._config = self.carregar_banco()
        self.cursor, self.conexao = self.abrir_banco()
        
        
    def carregar_banco(self):
        return {
        "host": os.getenv("HOST_DB"),
        "database": os.getenv("DATABASE_CONTECH"),
        "user": os.getenv("USER_DB"),
        "password": os.getenv("SENHA_DB"),
        "port": os.getenv("PORT_DB"),
    }
    
    def abrir_banco(self):
        try:
            self.connection = psycopg2.connect(**self._config)
            return self.connection.cursor(), self.connection
        
        except OperationalError as erro_abrir_banco:
            log.error(f"Ocorreu um erro ao tentar abrir o banco de dados {erro_abrir_banco}")
            raise
        except UnicodeDecodeError as erro_decode:
            log.error(f"Erro de decode nas variaveis de ambiente: {erro_decode}")
            raise
    
    def fechar_db(self, cursor, conexao):
        if conexao:
            cursor.close()
            conexao.close()
            print("Conexão com o DB fechada!")


class DatabaseBase:
    def __init__(self, query_insert_chamada, query_insert_operador):
        self.db = ConexaoDatabaseRivex()
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao

        self.query_insert_chamada = query_insert_chamada
        self.query_insert_operador = query_insert_operador

    def criar_tabelas(self, query_tabela_chamadas, query_tabela_agentes):
        try:
            self.cursor.execute(query_tabela_chamadas)
            self.cursor.execute(query_tabela_agentes)
            self.conexao.commit()


        except psycopg2.Error as erro:
            self.conexao.rollback()
            raise

    def enviar_cliente(self, dados_cliente):
        self.cursor.execute(
            self.query_insert_chamada,
            dados_cliente
        )

    def enviar_operador(self, dados_operador):
        self.cursor.execute(self.query_insert_operador, dados_operador)

    def enviar_dados(self, dados_cliente, agentes):
        cliente = dados_cliente.get("Cliente")
        tech = dados_cliente.get("tech")
        data = dados_cliente.get("Data")

        try:
            log.info(
                "[DB] Iniciando cliente=%s, tech=%s, data=%s",
                cliente,
                tech,
                data
            )

            self.enviar_cliente(dados_cliente)

            log.info(
                "[DB] Cliente inserido/atualizado: %s",
                cliente
            )

            for agente in agentes:
                self.enviar_operador(agente)

            self.conexao.commit()

            log.info(
                "[DB] commit feito: cliente=%s, tech=%s, agentes=%s",
                cliente,
                tech,
                len(agentes)
            )

        except Exception as erro:
            self.conexao.rollback()

            log.error(
                "[DB] erro no cliente=%s, tech=%s, erro=%s ",
                cliente,
                tech,
                data,
                erro,
                exc_info=True
            )

            raise

    def fechar_db(self):
        self.db.fechar_db(
            self.cursor,
            self.conexao
        )
        
