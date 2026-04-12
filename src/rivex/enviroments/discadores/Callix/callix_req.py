import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.Callix.payloads_callix import *


class CAllixRequisition:
    '''
    Classe para coletar os dados que não estão disponibilizados
    pela documentação da API. 
    A classe vai coletar os dados com requests
    '''
    
    def __init__(self, login, senha, cliente, data, id_campanha, token):
        self.login = login
        self.senha = senha
        self.cliente = cliente
        self.data = data
        self.session = requests.Session()
        self.id_campanha = id_campanha
        self.hr = HttpRequisitions(session=self.session)
        self.token = token
        
    def url_callix(self):
        # vai tratar e gerar todas as URL de requisições limpas para serem usadas
        url_base = f'https://{self.cliente}contech.callix.com.br/login'
        url_login = f'https://{self.cliente}contech.callix.com.br/api/v4/auth/session'
        url_chamadas_agentes = f'https://{self.cliente}contech.callix.com.br/api/v4/entities/user-performance-histories'
        url_agressividade = f'https://{self.cliente}contech.callix.com.br/api/v4/entities/campaigns/{self.id_campanha}'
        return url_login, url_chamadas_agentes, url_agressividade, url_base
    
    def login_callix(self, url_login, url_base):
        login = self.hr.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                       headers=headers_login_callix(url_base),
                                       url=url_login
                                       )
        print('Resultado da tentativa de login: ',login.status_code)
        token = login.json()["token"]
        return token
        
        
    
    def get_chamadas_agentes(self, url_chamadas_agentes, token_login):
        print('chegando nas chamadas')
        
        print(f"Token recebido: {token_login[:50]}...")  # mostra só o início
        print(f"Headers montados: {get_performance_headers(token=token_login, url=url_chamadas_agentes)}")
        chamadas_por_agentes = self.hr.requisicao_get(headers=get_performance_headers(token=token_login, url=url_chamadas_agentes),
                                      url=url_chamadas_agentes,
                                      payload_get=payload_de_requisicao_de_chamadas(self.data)
                                      )
        print(chamadas_por_agentes.status_code)
        print(chamadas_por_agentes.text)
        return chamadas_por_agentes
    
    def agressividade(self, url_agressividade):
        return self.hr.requisicao_get(headers=headers_callix(),
                                      url=url_agressividade
                                      )
    
    def requisicao_callix(self):
        url_login, url_chamadas_agentes, url_agressividade, url_base = self.url_callix()
        
        print('Logando...')
        login = self.login_callix(url_login, url_base)
        chamadas_por_agentes = self.get_chamadas_agentes(url_chamadas_agentes, login)
        agressividade = self.agressividade(url_agressividade)
        
        return chamadas_por_agentes, agressividade