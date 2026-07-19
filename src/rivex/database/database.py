import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os
import logging

log = logging.getLogger(__name__)



class ConexaoDatabaseRivex:
    def __init__(self):
        load_dotenv()
        self._config = self.carregar_banco()
        
        
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
            print("Estabelecendo conexão com o banco de dados...")
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
        
class DatabaseCallix:

    def __init__(self):
        self.db = ConexaoDatabaseRivex()
        self.cursor, self.conexao = self.db.abrir_banco()

        self.query_criar_tabela_chamadas = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente_callix (
            tech_cliente INTEGER NOT NULL,
            cliente_nome TEXT NOT NULL,
            data DATE NOT NULL,
            chamadas INTEGER NOT NULL,
            completas INTEGER NOT NULL,
            recusadas INTEGER NOT NULL,
            abandonadas INTEGER NOT NULL,
            agressividade FLOAT NOT NULL,
            PRIMARY KEY (tech_cliente, data)
        );
        """

        self.query_criar_tabela_agentes = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente_callix (
            tech INTEGER NOT NULL,
            cliente_nome TEXT NOT NULL,
            data DATE NOT NULL,
            nome_agente TEXT NOT NULL,
            chamadas_agente INTEGER NOT NULL,
            PRIMARY KEY (tech, data, nome_agente)
        );
        """

        self.query_chamadas = """
        INSERT INTO dados_discador.chamadas_cliente_callix
        (
            tech_cliente,
            cliente_nome,
            data,
            chamadas,
            completas,
            recusadas,
            abandonadas,
            agressividade
        )
        VALUES
        (
            %(tech)s,
            %(Cliente)s,
            %(Data)s,
            %(Chamadas totais)s,
            %(Chamadas aceitas)s,
            %(Chamadas recusadas)s,
            %(Chamadas abandonadas)s,
            %(Agressividade)s
        )
        ON CONFLICT (tech_cliente, data)
        DO UPDATE SET
            chamadas = EXCLUDED.chamadas,
            completas = EXCLUDED.completas,
            recusadas = EXCLUDED.recusadas,
            abandonadas = EXCLUDED.abandonadas,
            agressividade = EXCLUDED.agressividade;
        """

        self.query_agentes = """
        INSERT INTO dados_discador.chamadas_agente_callix
        (
            tech,
            cliente_nome,
            data,
            nome_agente,
            chamadas_agente
        )
        VALUES
        (
            %(tech)s,
            %(Cliente)s,
            %(Data)s,
            %(Nome do agente)s,
            %(Chamadas aceitas do agente)s
        )
        ON CONFLICT (tech, data, nome_agente)
        DO UPDATE SET
            chamadas_agente = EXCLUDED.chamadas_agente;
        """

        self.criar_tabelas()

    def criar_tabelas(self):
        try:
            self.cursor.execute(self.query_criar_tabela_chamadas)
            self.cursor.execute(self.query_criar_tabela_agentes)
            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error(f"Erro ao criar tabelas: {erro}")
            raise

    def envio_banco_chamadas(self, dados_cliente):

        for cliente in dados_cliente:

            try:
                self.cursor.execute(self.query_chamadas, cliente)
                self.conexao.commit()

                log.info(
                    "Cliente %s enviado.",
                    cliente["Cliente"]
                )

            except psycopg2.Error as erro:

                self.conexao.rollback()

                log.error(
                    "Erro ao enviar cliente %s: %s",
                    cliente["Cliente"],
                    erro
                )

    def envio_banco_agentes(self, dados_operador):

        for operador in dados_operador:

            try:
                self.cursor.execute(self.query_agentes, operador)
                self.conexao.commit()

            except psycopg2.Error as erro:

                self.conexao.rollback()

                log.error(
                    "Erro ao enviar operador %s: %s",
                    operador["Nome do agente"],
                    erro
                )

    def db_callix(self, dados_cliente, dados_operador):

        self.envio_banco_chamadas(dados_cliente)
        self.envio_banco_agentes(dados_operador)

    def fechar_db_callix(self):

        self.db.fechar_db(
            self.cursor,
            self.conexao
        )
class DatabaseVonix:
    def __init__(self):
        self.db = ConexaoDatabaseRivex()
        self.cursor, self.conexao = self.db.abrir_banco()
        
        