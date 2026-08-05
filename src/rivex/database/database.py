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


class DatabaseTelefonia:
    def __init__(self, query_insert_telefonia):
         self.db = ConexaoDatabaseRivex()
         self.cursor = self.db.cursor
         self.conexao = self.db.conexao
         self.query_insert_telefonia = query_insert_telefonia

    def criar_tabelas(self, query_tabela_telefonia):
        try:
            self.cursor.execute(query_tabela_telefonia)
            self.conexao.commit()

            log.info("Tabela de telefpmoa verificada/criada com sucesso.")

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao criar tabela: %s", erro)
            raise

    def enviar_dados_telefonia(self, dados):
        try:
            self.cursor.execute(self.query_insert_telefonia, dados)
            self.conexao.commit()
            log.info("Dados enviados com sucesso.")

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao enviar dados: %s", erro)
            raise

    def fechar_db(self):
        self.db.fechar_db(
            self.cursor,
            self.conexao
        )


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

            log.info("Tabelas verificadas/criadas com sucesso.")

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao criar tabelas: %s", erro)
            raise

    def enviar_cliente(self, dados_cliente):
        self.cursor.execute(self.query_insert_chamada, dados_cliente)

    def enviar_operador(self, dados_operador):
        self.cursor.execute(self.query_insert_operador, dados_operador)

    def enviar_dados(self, dados_cliente, agentes):
        try:
            self.enviar_cliente(dados_cliente)

            for agente in agentes:
                self.enviar_operador(agente)

            self.conexao.commit()

            log.info("Dados enviados com sucesso.")

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao enviar dados para o banco: %s", erro)
            raise

    def fechar_db(self):
        self.db.fechar_db(
            self.cursor,
            self.conexao
        )

class DatabaseCallix:
    def __init__(self):
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

        self.db = DatabaseBase(
            query_insert_chamada=self.query_chamadas,
            query_insert_operador=self.query_agentes
        )

        self.db.criar_tabelas(
            query_tabela_chamadas=self.query_criar_tabela_chamadas,
            query_tabela_agentes=self.query_criar_tabela_agentes
        )

    def db_callix(self, dados_chamadas, agentes):
        self.db.enviar_dados(dados_chamadas, agentes)

    def fechar(self):
        self.db.fechar_db()

class DatabaseVonix:
    def __init__(self):
        self.query_criar_tabela_chamadas = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente_vonix (
            id SERIAL PRIMARY KEY,
            tech_cliente INTEGER NOT NULL,
            cliente_nome TEXT NOT NULL,
            fila TEXT NOT NULL,
            data DATE NOT NULL,
            chamadas INTEGER NOT NULL,
            completas INTEGER NOT NULL,
            recusadas INTEGER NOT NULL,
            abandonadas INTEGER NOT NULL,
            agressividade FLOAT NOT NULL
        );
        """

        self.query_criar_tabela_agentes = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente_vonix (
            id SERIAL PRIMARY KEY,
            tech INTEGER NOT NULL,
            cliente_nome TEXT NOT NULL,
            fila TEXT NOT NULL,
            data DATE NOT NULL,
            nome_agente TEXT NOT NULL,
            chamadas_agente INTEGER NOT NULL
        );
        """

        self.query_chamadas = """
        INSERT INTO dados_discador.chamadas_cliente_vonix
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
            %(cliente)s,
            %(data)s,
            %(chamadas)s,
            %(completas)s,
            %(recusadas)s,
            %(abandonadas)s,
            %(agressividade)s
        );
        """

        self.query_agentes = """
        INSERT INTO dados_discador.chamadas_agente_vonix
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
            %(cliente_nome)s,
            %(data)s,
            %(agente)s,
            %(chamadas)s
        );
        """

        self.db = DatabaseBase(
            query_insert_chamada=self.query_chamadas,
            query_insert_operador=self.query_agentes
        )

        self.db.criar_tabelas(
            self.query_criar_tabela_chamadas,
            self.query_criar_tabela_agentes
        )

    def db_vonix(self, dados_chamadas, agentes):
            self.db.enviar_dados(dados_chamadas, agentes)
            
    def fechar_db_vonix(self):
            self.db.fechar_db()

class DatabaseIpbox:
    def __init__(self):
       self.query_criar_tabela_chamadas = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente_ipbox (
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
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente_ipbox (
            tech INTEGER NOT NULL,
            cliente_nome TEXT NOT NULL,
            data DATE NOT NULL,
            nome_agente TEXT NOT NULL,
            chamadas_agente INTEGER NOT NULL,
            PRIMARY KEY (tech, data, nome_agente)
        );
        """
       self.query_chamadas = """
       INSERT INTO dados_discador.chamadas_cliente_ipbox
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
        %(cliente_nome)s,
        %(data)s,
        %(chamadas)s,
        %(completas)s,
        %(recusadas)s,
        %(abandonadas)s,
        %(agressividade)s
    )
    ON CONFLICT (tech_cliente, data)
    DO UPDATE SET
        chamadas = EXCLUDED.chamadas,
        completas = EXCLUDED.completas,
        recusadas = EXCLUDED.recusadas,
        abandonadas = EXCLUDED.abandonadas,
        agressividade = EXCLUDED.agressividade;"""
        
       self.query_agentes = """
        INSERT INTO dados_discador.chamadas_agente_ipbox
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
    %(cliente_nome)s,
    %(data)s,
    %(nome_agente)s,
    %(chamadas_agente)s
)
ON CONFLICT (tech, data, nome_agente)
DO UPDATE SET
    chamadas_agente = EXCLUDED.chamadas_agente;
        """
       
       self.db = DatabaseBase(
            query_insert_chamada=self.query_chamadas,
            query_insert_operador=self.query_agentes
        )
       
       self.db.criar_tabelas(
            query_tabela_chamadas=self.query_criar_tabela_chamadas,
            query_tabela_agentes=self.query_criar_tabela_agentes
        )

    def db_ipbox(self, dados_chamadas, agentes):
            self.db.enviar_dados(dados_chamadas, agentes)
            
    def fechar_db_ipbox(self):
            self.db.fechar_db()

class DatabasePentagono():
    def __init__(self):
        self.query_criar_tabela_telefonia = """
    CREATE TABLE IF NOT EXISTS dados_operadora.dados_operadora_pentagono
    (
            tech INTEGER NOT NULL,
            data DATE NOT NULL,
            custo NUMERIC(12,2) NOT NULL,
            minutagem NUMERIC(10,2) NOT NULL,
            chamadas_tarifadas INTEGER NOT NULL,
            PRIMARY KEY (tech, data)
        );
        """
        self.query_inserir_dados_telefonia = """
INSERT INTO dados_operadora.dados_operadora_pentagono
        (
            tech,
            data,
            custo,
            minutagem,
            chamadas_tarifadas
        )
        VALUES
        (
            %(tech)s,
            %(data)s,
            %(custo)s,
            %(minutagem)s,
            %(chamadas_tarifadas)s
        )
        ON CONFLICT (tech, data)
        DO UPDATE SET
    custo = EXCLUDED.custo,
    minutagem = EXCLUDED.minutagem,
    chamadas_tarifadas = EXCLUDED.chamadas_tarifadas;       
"""
        self.db = DatabaseTelefonia(self.query_criar_tabela_telefonia)
        self.db.criar_tabelas(query_tabela_telefonia=self.query_criar_tabela_telefonia)

    def enviar_dados_db_pentagono(self, dados):
        self.db.enviar_dados_telefonia(dados)

    def fechar_db_telefonia(self):
        self.db.fechar_db()
            
class DatabaseGerax():
    def __init__(self):
        self.query_criar_tabela_telefonia = """
    CREATE TABLE IF NOT EXISTS dados_operadora.dados_operadora_gerax
    (
            tech INTEGER NOT NULL,
            data DATE NOT NULL,
            custo NUMERIC(12,2) NOT NULL,
            minutagem NUMERIC(10,2) NOT NULL,
            chamadas_tarifadas INTEGER NOT NULL,
            PRIMARY KEY (tech, data)
        );
        """
        self.query_inserir_dados_telefonia = """
INSERT INTO dados_operadora.dados_operadora_gerax
        (
            tech
            data,
            custo,
            minutagem,
            chamadas_tarifadas
        )
        VALUES
        (
            %(tech)s,
            %(data)s,
            %(custo)s,
            %(minutagem)s,
            %(chamadas_tarifadas)s
        )
        ON CONFLICT (tech, data)
        DO UPDATE SET
            dados_operadora_gerax = EXCLUDED.dados_operadora_gerax;
"""
        self.db = DatabaseTelefonia(self.query_criar_tabela_telefonia)
        self.db.criar_tabelas(query_tabela_telefonia=self.query_criar_tabela_telefonia)

    def enviar_dados_db_gerax(self, dados):
        self.db.enviar_dados_telefonia(dados)

    def fechar_db_telefonia(self):
        self.db.fechar_db()

class DatabaseUltracom:
    def __init__(self):
        self.query_criar_tabela_telefonia = """
            CREATE TABLE IF NOT EXISTS dados_operadora.dados_operadora_ultracom
            (
                    data DATE NOT NULL,
                    custo NUMERIC(12,2) NOT NULL,
                    minutagem NUMERIC(10,2) NOT NULL,
                    chamadas_tarifadas INTEGER NOT NULL,
                    PRIMARY KEY (data)
                );
                """
        self.query_inserir_dados_telefonia = """
        INSERT INTO dados_operadora.dados_operadora_ultracom
                (
                    data,
                    custo,
                    minutagem,
                    chamadas_tarifadas
                )
                VALUES
                (
                    %(data)s,
                    %(custo)s,
                    %(minutagem)s,
                    %(chamadas_tarifadas)s
                )
                ON CONFLICT (data)
                DO UPDATE SET
                    custo = EXCLUDED.custo,
                    minutagem = EXCLUDED.minutagem,
                    chamadas_tarifadas = EXCLUDED.chamadas_tarifadas;
"""
        self.db = DatabaseTelefonia(self.query_inserir_dados_telefonia)
        self.db.criar_tabelas(query_tabela_telefonia=self.query_criar_tabela_telefonia)

    def enviar_dados_db_ultracon(self, dados):
        self.db.enviar_dados_telefonia(dados)

    def fechar_db_telefonia(self):
        self.db.fechar_db()
