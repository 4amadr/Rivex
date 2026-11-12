import psycopg2
from src.rivex.database.config_database import ConexaoDatabaseRivex, DatabaseBase
from src.rivex.utils.logging_config.logging_config import LoggingDatabaseConfig

class DatabaseClientesCallix:
    def __init__(self, query_insert_cliente):
        self.db = ConexaoDatabaseRivex()
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao
        self.query_insert_clientes_callix = query_insert_cliente
        self.log = LoggingDatabaseConfig()

    def criar_tabela_cliente(self, query_criar_tabela):
        try:
            self.cursor.execute(query_criar_tabela)
            self.conexao.commit()
        except psycopg2.Error as erro:
            self.conexao.rollback()
            self.log.erro_db(query_criar_tabela, erro)
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
            self.log.erro_db_comentado(
                "Erro ao inserir cliente Callix: %s",
                erro
            )
            raise


class DatabaseTelefonia:
    def __init__(self, query_insert_telefonia):
         self.db = ConexaoDatabaseRivex()
         self.cursor = self.db.cursor
         self.conexao = self.db.conexao
         self.query_insert_telefonia = query_insert_telefonia
         self.log = LoggingDatabaseConfig()

    def criar_objeto_db(self, query_tabela_telefonia):
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
            self.log.registro_erro_envio(erro)
            raise

    def fechar_db(self):
        self.db.fechar_db(
            self.cursor,
            self.conexao
        )



