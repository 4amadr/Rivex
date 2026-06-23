from src.rivex.utils.database_utils.database_config import DatabaseConfig
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os
import logging

log = logging.getLogger(__name__)



class DatabaseRivex:
    def __init__(self):
        load_dotenv()
        self._config = self._carrecar_banco()
        self.criar_tabela_chamadas = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente (
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
        self.criar_tabela_agentes = """
        CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente (
            tech INTEGER NOT NULL,
            cliente_nome TEXT NOT NULL,
            data DATE NOT NULL,
            nome_agente TEXT NOT NULL,
            chamadas_agente INTEGER NOT NULL,
            PRIMARY KEY (tech, data, nome_agente)
        );
        """
        self.query_chamadas = """
            INSERT INTO dados_discador.chamadas_cliente (tech_cliente, cliente_nome, data, chamadas, completas, recusadas, abandonadas, agressividade)
            VALUES (%(tech)s, %(Cliente)s, %(Data)s, %(Chamadas totais)s, %(Chamadas aceitas)s, %(Chamadas recusadas)s, %(Chamadas abandonadas)s, %(Agressividade)s)
            ON CONFLICT (tech_cliente, data)
            DO UPDATE SET
            chamadas = EXCLUDED.chamadas,
            completas = EXCLUDED.completas,
            recusadas = EXCLUDED.recusadas,
            abandonadas = EXCLUDED.abandonadas,
            agressividade = EXCLUDED.agressividade;
            """
        self.query_agentes = """
            INSERT INTO dados_discador.chamadas_agente (tech, cliente_nome, data, nome_agente, chamadas_agente)
            SELECT %(tech)s, %(Cliente)s ,%(Data)s, %(Nome do agente)s, %(Chamadas aceitas do agente)s
            ON CONFLICT (tech, data, nome_agente)
            DO UPDATE SET
            chamadas_agente = EXCLUDED.chamadas_agente;
            """
        self.criar_tabela_operadora = """
        CREATE TABLE IF NOT EXISTS dados_operadora.consumo_clientes (
            tech INTEGER NOT NULL,
            cliente TEXT NOT NULL,
            operadora TEXT NOT NULL,
            data DATE NOT NULL,
            custo DECIMAL NOT NULL,
            minutagem DECIMAL NOT NULL,
            chamadas_tarifadas INTEGER NOT NULL,
            PRIMARY KEY (tech, data)
            );
        """
        self.inserir_consumo = """
INSERT INTO dados_operadora.consumo_clientes
(
    tech,
    cliente,
    operadora,
    data,
    custo,
    minutagem,
    chamadas_tarifadas
)
VALUES
(
    %(tech)s,
    %(cliente)s,
    %(operadora)s,
    %(data)s,
    %(custo)s,
    %(minutagem)s,
    %(chamadas_tarifadas)s
)
ON CONFLICT (tech, data)
DO UPDATE SET
    cliente = EXCLUDED.cliente,
    operadora = EXCLUDED.operadora,
    custo = EXCLUDED.custo,
    minutagem = EXCLUDED.minutagem,
    chamadas_tarifadas = EXCLUDED.chamadas_tarifadas;
"""
    def _carrecar_banco(self) -> dict:
        return {
            "host": os.getenv("HOST_DB"),
            "database": os.getenv("DATABASE_CONTECH"),
            "user": os.getenv("USER_DB"),
            "password": os.getenv("SENHA_DB"),
            "port": os.getenv("PORT_DB")
        }

    def abrir_banco(self):
        try:
            self.connection = psycopg2.connect(**self._config)
            print("Conectado ao banco de dados")
            return self.connection.cursor(), self.connection
        except OperationalError as erro_banco:
            log.error(f"Erro {erro_banco} ao conectar com o banco de dados, verifique as suas credenciais.")
        except UnicodeDecodeError as erro_decode:
            log.error(f"Erro de encoding nas variaveis de ambiente: {erro_decode}")
            raise
        except psycopg2.OperationalError as erro_operacao:
            log.error(f"Erro ao se conectar com o banco de dados: {erro_operacao}")
            raise
    
    def envio_banco(self, chamadas: dict, desempenho_do_agente: list, cursor):
        try:
            cursor.execute(self.criar_tabela_chamadas)
            cursor.execute(self.criar_tabela_agentes)
            self.connection.commit()
        except psycopg2.Error as erro_criacao_tabela:
            log.error(f"Erro ao criar tabelas: {erro_criacao_tabela}")
            
            
        try:
            print("Enviando dados de chamadas para o banco de dados")
            cursor.execute(self.query_chamadas, chamadas)
            print("Chamadas enviadas para o banco de dados!")
            self.connection.commit()
        except psycopg2.Error as erro_de_envio_de_chamadas:
            print(f"Erro ao enviar chamadas para o banco de dados! {erro_de_envio_de_chamadas}")
        
        try:
            for agente in desempenho_do_agente:
                cursor.execute(self.query_agentes, agente)
            print("Dados de agentes enviados para o banco de dados!")
            self.connection.commit()
        except psycopg2.Error as erro_envio_dados_agentes:
            print(f"Erro ao enviar dados de agentes para o banco de dados {erro_envio_dados_agentes}")
        return True
    
    def enviar_banco_operadoras(self, consumo, cursor):
        try:
            cursor.execute(self.criar_tabela_operadora)
            self.connection.commit()
        except psycopg2.Error as erro_banco:
            log.error(f"ERRO! ao criar banco de dados das discadoras! {erro_banco}")
        try:
            print("Enviando dados de consumo de clientes para o banco de dados")
            cursor.execute(self.inserir_consumo, consumo)
            self.connection.commit()
        except Exception as erro_envio:
            log.error(f"Erro ao enviar o consumo para o banco de dados: {erro_envio}")
        return True
            
    
    def fechar_db(self, cursor, conexao):
        if conexao:
            cursor.close()
            conexao.close()
            print("Conexão fechada com o DB")
    


            
            
