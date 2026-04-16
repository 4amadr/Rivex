import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

class DatabaseConfig:
    def __init__(self):
        load_dotenv()
    
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
    
    def inserir_dicionario_no_banco_de_dados(self, conexao, dados_equipe: dict):
        '''Todos os dados devem ser retornados em formato de dicionário para serem inseridos no 
        banco de dados'''
        if conexao is None:
            print("Conexão inválida no banco")
            return
        
        cursor = None
        try:
            cursor = conexao.cursor()
            
                
            cursor.execute(
                "INSERT INTO dados_chamadas (discador, fila, data, chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, agentes_online, agressividade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (dados_equipe['discador'],
                 dados_equipe['fila'], 
                 dados_equipe['data'], 
                 dados_equipe['chamadas_totais'],
                 dados_equipe['chamadas_completas'],
                 dados_equipe['chamadas_recusadas'], 
                 dados_equipe['chamadas_abandonadas'],
                 dados_equipe['agentes_online'],
                 dados_equipe['agressividade'],
                 )
            )
            conexao.commit()
            print('Dados inseridos com sucesso')
            
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir os dados no banco de dados")
            
        finally:
            if cursor is not None:
                cursor.close()
             
    def chamadas_callix(self,data, cliente, conexao, chamadas: dict, agressividade: dict):
        # logica diferente do discador vonix para inserir os dados no banco
        if conexao is None:
            print("Conexão inválida. Inserção cancelada.")
            return
        
        cursor = None
        try:
            cursor = conexao.cursor()
            
                
            cursor.execute(
                "INSERT INTO dados_chamadas (discador, fila, data, chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, agressividade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                 'Callix',
                 cliente["Cliente"],
                 data,
                 chamadas['Chamadas totais'],
                 chamadas['Chamadas aceitas'], 
                 chamadas['Chamadas recusadas'], 
                 chamadas['Chamadas abandonadas'],
                 agressividade['agressividade'],
                 )
            )
            
            conexao.commit()
            print('Dados do discador callix inseridos com sucesso')
            
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir os dados no banco de dados")
        
        finally:
            if cursor is not None:
                cursor.close()
         
    def dados_agentes_callix(self, cliente, data, conexao, dados_agente: dict):
        if conexao is None:
            print("Conexão inválida(callix). Inserção cancelada.")
            return
        
        cursor = None
        try:
            cursor = conexao.cursor()
            for agente in dados_agente:
                cursor.execute(
                    "INSERT INTO agentes_dia (cliente, data, agente, chamadas) VALUES (%s, %s, %s, %s)",
                    (
                    cliente["Cliente"],
                    data,
                    agente['agente'], 
                    agente['chamadas_atendidas'])
                )
            
            conexao.commit()
            print("Dados de agentes inseridos")
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir dados de agentes no banco de dados")
        finally:
            if cursor is not None:
                cursor.close()
                
    def inserir_chamadas_e_agentes_db(self, conexao, dados_agente: dict):
        if conexao is None:
            print("Conexão inválida. Inserção cancelada.")
            return
        
        cursor = None
        try:
            cursor = conexao.cursor()
            
            cursor.execute(
                "INSERT INTO agentes_dia (cliente, data, agente, chamadas) VALUES (%s, %s, %s, %s)",
                (
                 dados_agente['fila'],
                 dados_agente['data'],
                 dados_agente['agente'],
                 dados_agente['chamadas']
                 )
            )
            
            conexao.commit()
            print("Dados de agentes inseridos")
            
        except Exception as e:
            conexao.rollback()
            print(f"Erro {e} ao inserir dados de agentes no banco de dados")
            
        finally:
            if cursor is not None:
                cursor.close()
                
    def fechar_conexao(self, conexao):
        # fechar a conexão do banco
        if conexao:
            conexao.close()
            print("Conexão fechada")   
        
        
