import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os
import logging
from src.rivex.database.config_database import ConexaoDatabaseRivex, DatabaseBase
from src.rivex.utils.infra_utils.date_config import *


class LoggingDatabase:
    def __init__(self, logger_name: str = "rivex.database"):
        # 1. Obtém e formata a data para o arquivo de log
        self.data_config = DateConfig()
        self.data_log = self.data_config.data_callix().replace("/", "-")
        
        # 2. Define e cria a estrutura de diretórios se não existir
        self.diretorio = os.path.join("Log", "database-log")
        os.makedirs(self.diretorio, exist_ok=True)
        
        # 3. Define o caminho do arquivo de log
        self.caminho = os.path.join(self.diretorio, f"database-day{self.data_log}.log")
        
        # 4. Instancia e configura o logger
        self.log = logging.getLogger(logger_name)
        self.log.setLevel(logging.INFO)
        
        # 5. Adiciona os handlers apenas se ainda não foram configurados (evita duplicação)
        if not self.log.handlers:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Handler para gravar em arquivo
            file_handler = logging.FileHandler(self.caminho, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.log.addHandler(file_handler)
            
            # Handler para exibir também no console/terminal (opcional)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.log.addHandler(console_handler)

    def conferencia_dados(self, dados):
        # Interpolação tardia (%s) em vez de f-string
        self.log.info("Dados enviados ao banco: %s", dados)

    def registro_erro_envio(self, dados, erro):
        # exc_info=True inclui a pilha de erro (traceback) no log
        self.log.error("Erro ao enviar os dados %s ao banco de dados. Erro: %s", dados, erro, exc_info=True)

    def erro_configuracao(self, erro):
        self.log.error("Erro de configuração do banco: %s", erro, exc_info=True)


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
        self.db = DatabaseTelefonia(self.query_inserir_dados_telefonia)
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
        custo = EXCLUDED.custo,
        minutagem = EXCLUDED.minutagem,
        chamadas_tarifadas = EXCLUDED.chamadas_tarifadas;
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
        
           
class DatabaseAgitel():
    def __init__(self):
        self.query_criar_tabela_telefonia = """
    CREATE TABLE IF NOT EXISTS dados_operadora.dados_operadora_agitel
    (
            tech INTEGER NOT NULL,
            data DATE NOT NULL,
            custo NUMERIC(12,2) NOT NULL,
            minutagem NUMERIC(10,2) NOT NULL,
            PRIMARY KEY (tech, data)
        );
        """
        self.query_inserir_dados_telefonia = """
        INSERT INTO dados_operadora.dados_operadora_agitel
        (
            tech,
            data,
            custo,
            minutagem
        )
        VALUES
        (
            %(tech)s,
            %(data)s,
            %(custo)s,
            %(minutagem)s
        )
        ON CONFLICT (tech, data)
        DO UPDATE SET
            custo = EXCLUDED.custo,
            minutagem = EXCLUDED.minutagem;
        """
        self.db = DatabaseTelefonia(self.query_inserir_dados_telefonia)
        self.db.criar_tabelas(query_tabela_telefonia=self.query_criar_tabela_telefonia)

    def enviar_dados_db_agitel(self, dados):
        self.db.enviar_dados_telefonia(dados)

    def fechar_db_telefonia(self):
        self.db.fechar_db()

