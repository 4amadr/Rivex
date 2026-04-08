import requests
from rivex.utils.requests_utils.requests import HttpRequisitions


class CAllixRequisition:
    '''
    Classe para coletar os dados que não estão disponibilizados
    pela documentação da API. 
    A classe vai coletar os dados com requests
    '''
    
    def __init__(self, login, senha, cliente, data, session, hr, id_campanha):
        self.login = login
        self.senha = senha
        self.cliente = cliente
        self.data = data
        self.session = requests.Session()
        self.id_campanha = id_campanha
        self.hr = HttpRequisitions(session=session)
        
    def url_callix(self, cliente, id_campanha):
        # vai tratar e gerar todas as URL de requisições limpas para serem usadas
         url_login = f'https://{cliente}contech.callix.com.br/login'
         url_chamadas_agentes = f'https://{cliente}contech.callix.com.br/api/v4/entities/user-performance-histories'
         url_agressividade = f'https://{cliente}contech.callix.com.br/api/v4/entities/campaigns/{id_campanha}'
         return url_login, url_chamadas_agentes, url_agressividade
    
    def login_callix(self, login, senha, url_login):
        return self.hr.requisicao_post(url=url_login)
    
    def get_chamadas_agentes(self, data, url_chamadas_agentes):
        return self.hr.requisicao_get(url_chamadas_agentes)
    
    def agressividade(self, data, url_agressividade):
        return self.hr.requisicao_get(url=url_agressividade)
    
    def requisicao_callix(self):
        url_login, url_chamadas_agentes, url_agressividade = self.url_callix(cliente, id_campanha)
        
        login = self.login_callix(login, senha, url_login)
        chamadas_por_agentes = self.get_chamadas_agentes(data, url_chamadas_agentes)
        agressividade = self.agressividade(data, url_agressividade)
        
        return chamadas_por_agentes, agressividade