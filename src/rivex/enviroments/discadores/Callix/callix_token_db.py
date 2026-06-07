import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class CallixDB:
    def __init__(self):
        """Abre a conexão ao instanciar a classe."""
        try:
            self.conexao = psycopg2.connect(
                database=os.getenv('database_tokens'),
                user=os.getenv('user_database_tokens'),
                host=os.getenv('host_database_tokens'),
                port=os.getenv('port_database_tokens')
            )
            self.cursor = self.conexao.cursor()
            print("Conectado ao banco de dados!")
        except Exception as e:
            print("Erro durante a conexão com o banco de dados:", e)
            self.conexao = None
            self.cursor = None
            
    def insert_token_in_db(self, cliente_callix_ativo, token_callix_ativo):
        '''
        Função para inserir os clientes e os tokens no banco de dados callix
        '''
        try:
            sql = "INSERT INTO callix_tokens (cliente, token) VALUES (%s, %s)"
            dados = (cliente_callix_ativo, token_callix_ativo)
            self.cursor.execute(sql, dados)
            self.conexao.commit()
            print("Clientes e tokens inseridos no banco de dados callix_tokens")
        except psycopg2.Error as e:
            print(f"Erro {e} ao tentar inserir os clientes/tokens no banco de dados")

    def get_token_and_client_from_db(self):
        """Coleta token e cliente da tabela callix_tokens."""
        if not self.cursor:
            raise RuntimeError("Cursor não inicializado (falha na conexão).")

        self.cursor.execute("SELECT cliente, token FROM callix_tokens")
        return {cliente: token for cliente, token in self.cursor.fetchall()}

    def close(self):
        """Fecha cursor e conexão."""
        if self.cursor:
            self.cursor.close()
        if self.conexao:
            self.conexao.close()
        print("Banco de dados fechado")
