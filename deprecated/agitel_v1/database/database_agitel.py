from src.rivex.utils.database_utils.database_telefonia import DatabaseTelefonia


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