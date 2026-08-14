import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
from src.rivex.database.config_database import DatabaseBase, ConexaoDatabaseRivex
from src.rivex.database.database_dados_chamadas import DatabaseClientesCallix

class DatabaseClientes:
    def __init__(self):
        self.db = ConexaoDatabaseRivex()
        self.cursor = seld.db.cursor
        self.conexao = self.db.conexao
        self.query_criar_tabela_clientes = """
        CREATE TABLE IF NOT EXISTS clientes_contech.clientes_ativos_callix (
            cliente_nome TEXT NOT NULL,
            cliente_token TEXT NOT NULL,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            PRIMARY KEY (cliente_nome)
            );
            """
            
        self.query_remover_clientes_inativos = """
        DELETE FROM clientes_contech.clientes_ativos_callix 
        WHERE cliente_nome = %s"""
        
        self.query_enviar_clientes_db = """
        INSERT INTO clientes_contech.clientes_ativos_callix (
            cliente_nome,
            cliente_token,
            ativo
            )
            VALUES
            (
                %(cliente)s,
                %(token)s,
                %(estado)s,
                TRUE
                ON CONFLIT (cliente_nome)
                DO UPDATE SET
                cliente = EXCLUDED.cliente,
                token = EXCLUDED.token,
                ativo = TRUE;
                """
                
        self.db = DatabaseClientesCallix(
            query_insert_cliente=self.query_enviar_clientes_db,
        )

        self.db.criar_tabela_cliente(
            query_criar_tabela=self.query_criar_tabela_clientes,
        )
        
    def db_clientes_callix(self, dict_clientes):
        self.db.enviar_info_cliente(dict_clientes)
    
    def inativar_cliente(self, dict_clientes):
        try:
            self.cursor.execute(self.query_remover_clientes_inativos)
            self.conexao.commit()
        except psycopg2.Error as erro:
            self.conexao.rollback()
            log.error("Erro ao remover o cliente: %s", erro)
            raise
        
    
            
        
    
       