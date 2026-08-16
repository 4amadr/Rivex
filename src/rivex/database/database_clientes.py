import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
from src.rivex.database.config_database import DatabaseBase, ConexaoDatabaseRivex
from src.rivex.database.database_dados_chamadas import DatabaseClientesCallix, DatabaseTelefonia
import logging

log = logging.Logger(__name__)

class DatabaseClientes:
    def __init__(self):
        self.db = ConexaoDatabaseRivex()
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao
        self.query_criar_tabela_clientes = """
        CREATE TABLE IF NOT EXISTS clientes.clientes_callix (
            cliente_nome TEXT NOT NULL,
            cliente_token TEXT NOT NULL,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            PRIMARY KEY (cliente_nome)
            );
            """
        self.query_remover_clientes_inativos = """
        UPDATE clientes.clientes_callix
        SET ativo = FALSE
        WHERE cliente_nome = %s 
                                               """
        self.query_enviar_clientes_db = """
    INSERT INTO clientes.clientes_callix (
        cliente_nome,
        cliente_token,
        ativo
    )
    VALUES (
        %(cliente)s,
        %(token)s,
        TRUE
    )
    ON CONFLICT (cliente_nome)
    DO NOTHING;
"""
        self.query_verificar_clientes = """
        SELECT cliente_nome, cliente_token, ativo
        FROM clientes.clientes_callix;
        """
        self.query_reativar_clientes = """
    UPDATE clientes.clientes_callix
    SET ativo = TRUE
    WHERE cliente_nome = %s
      AND ativo = FALSE;
"""
        self.db_clientes = DatabaseClientesCallix(self.query_enviar_clientes_db)
        self.db_telefonia = DatabaseTelefonia(self.query_enviar_clientes_db)
        self.db_telefonia.criar_tabelas(self.query_criar_tabela_clientes)
        
    def db_clientes_callix(self, dict_clientes):
        self.db_clientes.enviar_info_cliente(dict_clientes)
    
    def inativar_cliente(self):
        try:
            self.cursor.execute(self.query_remover_clientes_inativos)
            clientes = self.cursor.fetchall()

            return {
                cliente_nome : cliente_token
                for cliente_nome, cliente_token in clientes
            }
        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao remover o cliente: %s", erro)
            raise

    def sincronizar_clientes(self):
        try:
            self.cursor.execute(self.query_verificar_clientes)
            self.conexao.commit()

            resultado = self.cursor.fetchall()

            clientes_db = {
                cliente_nome: {
                    "token": cliente_token,
                    "ativo": ativo
                }
                for cliente_nome, cliente_token, ativo in resultado
            }
            return clientes_db


        except psycopg2.Error as erro:
            log.error(f"Erro na verificação de clietnes: {erro}")
        
    def reativar_clientes(self, cliente):
        try:
            self.cursor.execute(
                self.query_reativar_clientes,
                (cliente,)
            )
            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao reativar clietne: %s", cliente, erro)
            raise