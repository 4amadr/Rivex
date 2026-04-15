from src.rivex.utils.database_utils.database_config import DatabaseConfig


class DatabaseRivex:
    def __init__(self):
        pass
    
    @staticmethod
    def coleta_chamadas(dados_equipe: dict, dados_agentes: dict):
        dc = DatabaseConfig()
        conexao = dc.conect_database()
        
        if conexao is None:
            return
        try:
            dc.inserir_dicionario_no_banco_de_dados(conexao=conexao, dados_equipe=dados_equipe)
            dc.inserir_chamadas_e_agentes_db(conexao, dados_agentes)
        finally:
            dc.fechar_conexao(conexao)
        
    @staticmethod  
    def coleta_callix(self, data, cliente, chamadas: dict, agressividade: dict, dados_agentes: dict):
        dc = DatabaseConfig()
        conexao = dc.conect_database()
        
        if conexao is None:
            return
        try:
            dc.chamadas_callix(cliente, conexao, chamadas, agressividade)
            dc.dados_agentes_callix(data, conexao, dados_agentes)
        finally:
            dc.fechar_conexao(conexao)
            