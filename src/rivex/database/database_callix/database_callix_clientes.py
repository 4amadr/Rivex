from src.rivex.database.config_database import ConexaoDatabaseRivex
from src.rivex.utils.database_utils.database_telefonia import DatabaseTelefonia
from src.rivex.utils.logging_config.logging_config import LoggingDatabaseConfig


class DatabaseClientes:
    """Consulta os clientes ativos do Callix e seus tokens na base local."""

    def __init__(self):
        self.log_db = LoggingDatabaseConfig()
        self.db = ConexaoDatabaseRivex()
        self.cursor = self.db.cursor
        self.conexao = self.db.conexao

        self.query_criar_tabela_clientes = """
            CREATE TABLE IF NOT EXISTS clientes.clientes_callix (
                cliente_nome TEXT NOT NULL,
                cliente_token TEXT,
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                PRIMARY KEY (cliente_nome)
            );
        """

        self.query_criar_view_clientes_ativos = """
            CREATE OR REPLACE VIEW clientes.vw_clientes_ativos AS
            SELECT
                cliente_nome,
                cliente_token
            FROM clientes.clientes_callix
            WHERE ativo = TRUE;
        """

        self.query_consultar_clientes_ativos = """
            SELECT cliente_nome, cliente_token
            FROM clientes.vw_clientes_ativos
            ORDER BY cliente_nome;
        """

        self.db_telefonia = DatabaseTelefonia(self.query_consultar_clientes_ativos)
        self.db_telefonia.criar_objeto_db(self.query_criar_tabela_clientes)
        self.db_telefonia.criar_objeto_db(self.query_criar_view_clientes_ativos)

    def consultar_view(self) -> list[dict]:
        try:
            self.cursor.execute(self.query_consultar_clientes_ativos)
            clientes_ativos = self.cursor.fetchall()
            return [
                {"cliente": cliente_nome, "token": cliente_token}
                for cliente_nome, cliente_token in clientes_ativos
            ]
        except Exception as erro:
            self.conexao.rollback()
            self.log_db.erro_consulta(self.query_consultar_clientes_ativos, erro)
            raise

    def fechar(self):
        self.db.fechar_db(self.cursor, self.conexao)
        self.db_telefonia.fechar_db()
