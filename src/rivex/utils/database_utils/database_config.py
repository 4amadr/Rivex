import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

class DatabaseConfig:
    def conect_database(self):
        '''Função para realizar a conexão com o banco de dados'''
        try:
            conect = psycopg2.connect(
                dbname = os.getenv('database_tokens'),
                user = os.getenv('user_database_tokens'),
                port = os.getenv('port_database_tokens'),
                host = os.getenv('host_datanase_tokens'),
            )
            print('Conectado no banco de dados!')
            
            return conect
        except Exception as erro_banco:
            print(f"Erro {erro_banco} durante a conexão com o banco de dados")
            return None
    
    def inserir_dicionario_no_banco_de_dados(self, conexao, tabela: str, dados_equipe: dict):
        '''Todos os dados devem ser retornados em formato de dicionário para serem inseridos no 
        banco de dados'''
        cursor = None
        try:
            cursor = conexao.cursor()
            
                
            cursor.execute(
                "INSERT INTO dados_chamadas (discador, fila, data, chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, agentes_online, agressividade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (dados_equipe['discador'], dados_equipe['fila'], dados_equipe['data'], dados_equipe['chamadas_totais'],
                 dados_equipe['chamadas_completas'], dados_equipe['chamadas_recusadas'], dados_equipe['chamadas_abandonadas'], dados_equipe['agentes_online'],
                 dados_equipe['agressividade'],
                 )
            )
            conexao.commit()
            
            print('Dados inseridos com sucesso')
            
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir os dados no banco de dados")
        
                
    def inserir_chamadas_e_agentes_db(self, conexao, dados_agente: dict):
        cursor = None
        try:
            cursor = conexao.cursor()
            
            cursor.execute(
                "INSERT INTO agentes_dia (cliente, data, agente, chamadas) VALUES (%s, %s, %s, %s)",
                (dados_agente['fila'], dados_agente['data'], dados_agente['agente'], dados_agente['chamadas'])
            )
            conexao.commit()
            
            print("Dados de agentes inseridos")
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir dados de agentes no banco de dados")
            
    def fechar_conexao(self, conexao):
        # fechar a conexão do banco
        
        if conexao:
            conexao.close()
            print("Conexão fechada")   
        