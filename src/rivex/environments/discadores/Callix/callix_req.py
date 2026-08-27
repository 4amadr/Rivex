import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import *
from src.rivex.utils.environments_utils.discador.callix.get_url_callix import UrlGetClients, UrlGetData
import urllib.parse
import logging

log = logging.getLogger(__name__)
logging.basicConfig(
    filename='callix-exec.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


class CAllixRequisition:
    '''
    Classe para coletar os dados que não estão disponibilizados
    pela documentação da API. 
    A classe vai coletar os dados com requests
    '''
    
    def __init__(self, login, senha, data):
        self.login = login
        self.senha = senha
        self.data = data
        self.session = requests.Session()
        self.http_request = HttpRequisitions(session=self.session)
        self.url = UrlGetData()

        
    def url_callix(self, cliente):
        # vai tratar e gerar todas as URL de requisições limpas para serem usadas
        url_login = f'https://{cliente}.callix.com.br/api/v4/auth/session'
        url_chamadas_agentes = f'https://{cliente}.callix.com.br/api/v4/entities/user-performance-histories'
        url_get_tech = f'https://{cliente}.callix.com.br/api/v4/entities/accounts'
        return url_login, url_chamadas_agentes
    
    def login_callix(self, cliente):
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                       headers=headers_login_callix(self.url.login_cliente_header(cliente)),
                                       url=self.url.login_cliente(cliente)
                                       )
        token = login.json()["token"]
        return token
    
    def conversor_de_url(self, url_chamadas_agentes):
        '''
        Tratamento para a requisição de chamadas dos agentes
        pede um tratamento mais complexo pois o payload pede conversão manual
        '''
        
        params = payload_de_requisicao_de_chamadas(self.data)
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url_final = f"{url_chamadas_agentes}?{query_string}"
        return url_final 
    
    def get_chamadas_agentes(self, url_final, url_chamadas_agentes, token_login):
        chamadas_por_agentes = self.http_request.requisicao_get(headers=get_performance_headers(token=token_login, url=url_chamadas_agentes),
                                      url=url_final,
                                      payload_get=None
                                      )
        return chamadas_por_agentes
    
    def agressividade(self, token, cliente, campanhas):
        # pode haver mais de uma campanha o que gera mais de uma agressividade
        lista_json_agressividade = []
        
        for url_unico_de_agressividade in self.url.url_agressividade(cliente, campanhas):
            agressividade = self.http_request.requisicao_get(headers=headers_callix(token),
                                        url=url_unico_de_agressividade,
                                        payload_get=payload_agressividade()
                                        )
            lista_json_agressividade.append(agressividade)
        return lista_json_agressividade

    def get_tech_cliente(self, cliente, token):
        tech = self.http_request.requisicao_get(
            headers=headers_callix(token),
            url=self.url.url_get_tech(cliente),
            payload_get=payload_get_tech()
            )

        return tech

    def requisicao_callix(self, id_campanha, cliente, token):
        url_login, url_chamadas_agentes = self.url_callix(cliente)

        login = self.login_callix(cliente)
        url_final = self.conversor_de_url(url_chamadas_agentes)
        chamadas_por_agentes = self.get_chamadas_agentes(url_final, url_chamadas_agentes, login)
        agressividade = self.agressividade(login, cliente, id_campanha) # lista
        tech = self.get_tech_cliente(cliente, login)
        
        return {
            "chamadas por agentes brutas":chamadas_por_agentes, 
            "agressividade bruta": agressividade, 
            "tech bruta": tech
            }