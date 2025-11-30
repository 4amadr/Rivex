import os

import psycopg2
import dotenv
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

    def get_token_and_client_from_db(self):
        """Coleta token e cliente da tabela callix_tokens."""
        if not self.cursor:
            raise RuntimeError("Cursor não inicializado (falha na conexão).")

        try:
            self.cursor.execute("SELECT token, cliente FROM callix_tokens;")
            resultado = self.cursor.fetchall()
            if resultado:
                token = []
                cliente = []
                for row in resultado:
                    token.append(row[0])
                    cliente.append(row[1])
                return token, cliente
            else:
                print('Sem clientes no banco')
                return [], []
        except Exception as e:
            print("Erro ao buscar dados:", e)
            return [], []

    def close(self):
        """Fecha cursor e conexão."""
        if self.cursor:
            self.cursor.close()
        print("Banco de dados fechado")

cd = CallixDB()

token, clientes = cd.get_token_and_client_from_db()
cd.close()
