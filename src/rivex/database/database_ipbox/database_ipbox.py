from src.rivex.database.config_database import DatabaseBase

class DatabaseIpbox:
    def __init__(self):
        self.query_criar_tabela_chamadas = """
                                           CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente_ipbox \
                                           ( \
                                               tech_cliente \
                                               INTEGER \
                                               NOT \
                                               NULL, \
                                               cliente_nome \
                                               TEXT \
                                               NOT \
                                               NULL, \
                                               data \
                                               DATE \
                                               NOT \
                                               NULL, \
                                               chamadas \
                                               INTEGER \
                                               NOT \
                                               NULL, \
                                               completas \
                                               INTEGER \
                                               NOT \
                                               NULL, \
                                               recusadas \
                                               INTEGER \
                                               NOT \
                                               NULL, \
                                               abandonadas \
                                               INTEGER \
                                               NOT \
                                               NULL, \
                                               agressividade \
                                               FLOAT \
                                               NOT \
                                               NULL, \
                                               PRIMARY \
                                               KEY \
                                           ( \
                                               tech_cliente, \
                                               data \
                                           )
                                               ); \
                                           """
        self.query_criar_tabela_agentes = """
                                          CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente_ipbox \
                                          ( \
                                              tech \
                                              INTEGER \
                                              NOT \
                                              NULL, \
                                              cliente_nome \
                                              TEXT \
                                              NOT \
                                              NULL, \
                                              data \
                                              DATE \
                                              NOT \
                                              NULL, \
                                              nome_agente \
                                              TEXT \
                                              NOT \
                                              NULL, \
                                              chamadas_agente \
                                              INTEGER \
                                              NOT \
                                              NULL, \
                                              PRIMARY \
                                              KEY \
                                          ( \
                                              tech, \
                                              data, \
                                              nome_agente \
                                          )
                                              ); \
                                          """
        self.query_chamadas = """
                              INSERT INTO dados_discador.chamadas_cliente_ipbox
                              (tech_cliente, \
                               cliente_nome, \
                               data, \
                               chamadas, \
                               completas, \
                               recusadas, \
                               abandonadas, \
                               agressividade)
                              VALUES (%(tech)s,
                                      %(cliente_nome)s,
                                      %(data)s,
                                      %(chamadas)s,
                                      %(completas)s,
                                      %(recusadas)s,
                                      %(abandonadas)s,
                                      %(agressividade)s) ON CONFLICT (tech_cliente, data)
    DO \
                              UPDATE SET
                                  chamadas = EXCLUDED.chamadas, \
                                  completas = EXCLUDED.completas, \
                                  recusadas = EXCLUDED.recusadas, \
                                  abandonadas = EXCLUDED.abandonadas, \
                                  agressividade = EXCLUDED.agressividade;"""
        self.query_agentes = """
                             INSERT INTO dados_discador.chamadas_agente_ipbox
                             (tech, \
                              cliente_nome, \
                              data, \
                              nome_agente, \
                              chamadas_agente)
                             VALUES (%(tech)s,
                                     %(cliente_nome)s,
                                     %(data)s,
                                     %(nome_agente)s,
                                     %(chamadas_agente)s) ON CONFLICT (tech, data, nome_agente)
DO \
                             UPDATE SET
                                 chamadas_agente = EXCLUDED.chamadas_agente; \
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