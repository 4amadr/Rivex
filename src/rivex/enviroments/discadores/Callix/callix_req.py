import requests

class CAllixRequisition:
    '''
    Classe para coletar os dados que não estão disponibilizados
    pela documentação da API. 
    A classe vai coletar os dados com requests
    '''
    
    def __init__(self, login, senha, cliente, data):
        self.login = login
        self.senha = senha
        self.cliente = cliente
        self.data = data
        
    def url_callix(cliente):
        # vai tratar e gerar todas as URL de requisições limpas para serem usadas
         