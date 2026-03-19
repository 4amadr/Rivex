from src.rivex.utils.database_utils.database_config import DatabaseConfig

class DatabaseRivex:
    def coleta_chamadas(dados_equipe: dict):
        dc = DatabaseConfig()
        conexao = dc.conect_database()
        dc.inserir_dicionario_no_banco_de_dados(conexao=conexao, tabela='dados_chamadas', dados_equipe=dados_equipe)
        dc.fechar_conexao(conexao)
        
        
    # abaixo devem ser inseridos as outras coletas -> Operadoras e definição de clientes