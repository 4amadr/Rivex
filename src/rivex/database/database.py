from src.rivex.utils.database_utils.database_config import DatabaseConfig
import psycopg2

class DatabaseRivex:
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "database": "meu_banco",
            "user": "nome_usuario",
            "password": "senha",
            "port": "5432"
        }
        self.query_chamadas = {
            """
            INSERT INTO chamadas_cliente (tech, cliente_nome, data, chamadas, completas, recusadas, abandonadas, agressividade)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

"""
        }
        self.query_agentes = {
            """
            INSERT INTO chamadas_agente (tech, cliente_nome, data, nome_agente, chamadas_agente)
            VALUES (%s, %s, %s, %s, %s)

"""
        }

    def abrir_banco(self):
        connection = psycopg2.connect(**self.db_config)
        print("Conectado ao banco de dados")
        cursor = connection.cursor
        return cursor
    
    def envio_banco(self, chamadas: dict, desempenho_do_agente: list, cursor):
        try:
            print("Enviando dados de chamadas para o banco de dados")
            cursor.execute(self.query_chamadas, chamadas)
            print("Chamadas enviadas para o banco de dados!")
        except psycopg2.Error as erro_de_envio_de_chamadas:
            print(f"Erro ao enviar chamadas para o banco de dados! {erro_de_envio_de_chamadas}")
        
        try:
            print("Enviando dados de desempenho dos agentes para o banco de dados")
            for desempenho in desempenho_do_agente:
                cursor.execute(self.query_agentes, desempenho)
                print("Dados de agentes enviados para o banco de dados!")
        except psycopg2.Error as erro_envio_dados_agentes:
            print(f"Erro ao enviar dados de agentes para o banco de dados {erro_envio_dados_agentes}")
        return True
    
    def fechar_db(self, cursor, conexao):
        if conexao:
            cursor.close()
            conexao.close()
            print("Conexão fechada com o DB")
    


            
            
