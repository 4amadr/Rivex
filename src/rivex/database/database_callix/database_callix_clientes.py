import psycopg2
from src.rivex.database.config_database import ConexaoDatabaseRivex
from src.rivex.utils.database_utils.database_telefonia import DatabaseTelefonia, DatabaseClientesCallix
from src.rivex.utils.logging_config.logging_config import LoggingDatabaseConfig, LoadLogger


class DatabaseClientes:
    
    def __init__(self):
        self.log_db = LoggingDatabaseConfig()
        self.load_log = LoadLogger()
        self.db = ConexaoDatabaseRivex()
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao

        self.query_criar_tabela_clientes = """
            CREATE TABLE IF NOT EXISTS clientes.clientes_callix (
                cliente TEXT NOT NULL,
                token TEXT,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                PRIMARY KEY (cliente)
            );
        """

        self.query_inativar_clientes = """
            UPDATE clientes.clientes_callix
            SET ativo = FALSE
            WHERE cliente = %s
                AND ativo = TRUE
            RETURNING cliente, token;
        """

        self.query_enviar_clientes_db = """
            INSERT INTO clientes.clientes_callix (
                cliente,
                ativo
            )
            VALUES (
                %(cliente)s,
                %(ativo)s
            )
            ON CONFLICT (cliente)
            DO UPDATE SET
                ativo = EXCLUDED.ativo
            WHERE
                clientes.clientes_callix.ativo
                    IS DISTINCT FROM EXCLUDED.ativo;
        """

        self.query_buscar_clientes = """
            SELECT cliente, token, ativo
            FROM clientes.clientes_callix
            WHERE ativo = TRUE;
        """

        self.query_reativar_clientes = """
            UPDATE clientes.clientes_callix
            SET ativo = TRUE
            WHERE cliente = %s;
        """

        self.query_buscar_clientes_sem_token = """
            SELECT cliente
            FROM clientes.clientes_callix
            WHERE ativo = TRUE
                AND token IS NULL;
        """

        self.query_adicionar_token_db = """
            UPDATE clientes.clientes_callix
            SET token = %(token)s
            WHERE cliente = %(cliente)s;
        """

        self.query_criar_view_clientes_ativos = """
            CREATE OR REPLACE VIEW clientes.vw_clientes_ativos AS
            SELECT
                cliente,
                token
            FROM clientes.clientes_callix
            WHERE ativo = TRUE;
        """

        self.query_consultar_clientes_ativos = """
            SELECT cliente, token
            FROM clientes.vw_clientes_ativos;
        """
                    
                    
        self.db_clientes = DatabaseClientesCallix(self.query_enviar_clientes_db)
        self.db_telefonia = DatabaseTelefonia(self.query_enviar_clientes_db)
        self.db_telefonia.criar_objeto_db(self.query_criar_tabela_clientes)
        self.db_telefonia.criar_objeto_db(self.query_criar_view_clientes_ativos)
        
    def db_clientes_callix(self, dict_clientes):
        self.db_clientes.enviar_info_cliente(dict_clientes)
    
    def inativar_cliente(self, cliente):
        try:
            self.cursor.execute(self.query_inativar_clientes, (cliente,))
            self.conexao.commit()
            clientes = self.cursor.fetchall()

            return {
                cliente_nome : cliente_token
                for cliente_nome, cliente_token in clientes
            }
        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.log_db.erro_configuracao("Erro ao remover o cliente: %s")
            raise

    def sincronizar_clientes(self):
        try:
            self.cursor.execute(self.query_buscar_clientes)
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
            self.log_db.erro_configuracao(erro)
            return {}
        
    def reativar_clientes(self, cliente):
        try:
            self.cursor.execute(
                self.query_reativar_clientes,
                (cliente,)
            )
            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db(self.query_reativar_clientes, cliente, erro)
            raise

    def cadastrar_cliente(self, cliente):    
        envio = {
            "cliente": cliente["cliente"],
            "ativo": cliente["ativo"]
        }
        
        
        try:
            self.cursor.execute(
                self.query_enviar_clientes_db,
                envio
            )
            self.load_log.registrar_envio_db(self.query_enviar_clientes_db, envio)
            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db(self.query_enviar_clientes_db, envio, erro)
            raise

    def consultar_view(self):
        try:
            self.cursor.execute(
                self.query_consultar_clientes_ativos
            )
            clientes_ativos = self.cursor.fetchall()
            clientes_db = [
                {
                    "cliente": cliente,
                    "token": token
                }
                for cliente, token in clientes_ativos
            ]
            return clientes_db
        except Exception as erro:
            self.conexao.rollback()
            self.log_db.erro_consulta(self.query_consultar_clientes_ativos, erro)
            raise
    
    
    def buscar_clientes_sem_token(self):
        try:
            self.cursor.execute(
                self.query_buscar_clientes_sem_token
            )
            cliente_sem_token = self.cursor.fetchall()
            return [linha[0] for linha in cliente_sem_token]
        except Exception as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db(self.query_buscar_clientes_sem_token, [], erro)
            raise
    
    def adicionar_token_ao_db(self, token, cliente):
        
        envio_db = {
            "cliente": cliente,
            "token": token
        }
        
        
        try:
            self.cursor.execute(
                self.query_adicionar_token_db, envio_db
            )
            self.load_log.registrar_envio_db(self.query_adicionar_token_db, envio_db)
            self.conexao.commit()

        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.load_log.registrar_erro_db(self.query_adicionar_token_db, envio_db, erro)
            raise