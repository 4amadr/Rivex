import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

class DatabaseConfig:
    def conect_database(self):
        '''Função para realizar a conexão com o banco de dados'''
        try:
            conect = psycopg2.connect(
                nome_banco_de_dados = os.getenv('database_tokens'),
                usuario = os.getenv('user_database_tokens'),
                porta = os.getenv('port_database_tokens'),
                host = os.getenv('host_datanase_tokens'),
            )
            print('Conectado no banco de dados!')
            
            return conect
        except Exception as erro_banco:
            print(f"Erro {e} durante a conexão com o banco de dados")
            return None
    
    def inserir_dicionario_no_banco_de_dados(self, conexao, tabela: str, dados_equipe: dict):
        '''Todos os dados devem ser retornados em formato de dicionário para serem inseridos no 
        banco de dados'''
        try:
            cursor = conexao.cursor()
            
            coluna = dados_equipe.keys()
            valores = dados_equipe.values()
            
            query = sql.SQL("""
                INSERT INTO {} ({})
                VALUES ({})""
                """).format(
                    sql.Identifier(tabela),
                    sql.SQL(', ').join(map(sql.Identifier, coluna)),
                    sql.SQL(', ').join(sql.Placeholder() * len(coluna))
                )
                
            cursor.execute(query, list(valores))
            conexao.commit()
            
            print('Dados inseridos com sucesso')
            
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir os dados no banco de dados")
        finally: 
            cursor.close()
            
    def fechar_conexao(conexao):
        # fechar a conexão do banco
        
        if conn:
            conn.close()
            print("Conexão fechada")   
        