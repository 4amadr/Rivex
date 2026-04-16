from src.rivex.utils.database_utils.database_config import DatabaseConfig


class DatabaseRivex:
    def __init__(self):
        pass
    
    @staticmethod
    def coleta_chamadas(conexao, dados_equipe: dict):
        dc = DatabaseConfig()

        
        if conexao is None:
            return
        try:
            dc.inserir_dicionario_no_banco_de_dados(conexao=conexao, dados_equipe=dados_equipe)
        finally:
            print("Tentativa finalizada de inserir dados no banco de chamadas")
        return conexao
        
    def coleta_agentes(conexao, cliente, data, dados_agentes: dict):
        dc = DatabaseConfig()

        if conexao is not None:
            try:
                dc.inserir_chamadas_e_agentes_db(cliente, data, conexao, dados_agentes)
            finally:
                print('Tentativa finalizada no banco de agentes e chamadas')
        return conexao
        
    @staticmethod  
    def coleta_callix(data, cliente, chamadas: dict, agressividade: dict, dados_agentes: dict):
        dc = DatabaseConfig()
        conexao = dc.conect_database()
        
        if conexao is None:
            return
        try:
            dc.chamadas_callix(data, cliente, conexao, chamadas, agressividade)
            dc.dados_agentes_callix(cliente, data, conexao, dados_agentes)
        finally:
            dc.fechar_conexao(conexao)
            
    @staticmethod            
    def fechar_conexao_vonix(conexao):
        # fechar a conexão do banco Vonix
        if conexao:
            conexao.close()
            print("Conexão fechada NO VONIX") 