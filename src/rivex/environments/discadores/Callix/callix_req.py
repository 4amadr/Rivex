import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import *
from src.rivex.utils.environments_utils.discador.callix.get_url_callix import *
import urllib.parse
import logging

log = logging.getLogger(__name__)


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
        self.token = token
        self.http_request = HttpRequisitions(session=self.session)
        self.url = UrlGetData()

        
    def url_callix(self):
        # vai tratar e gerar todas as URL de requisições limpas para serem usadas
        url_base = f'https://{self.cliente}.callix.com.br/login'
        url_login = f'https://{self.cliente}.callix.com.br/api/v4/auth/session'
        url_chamadas_agentes = f'https://{self.cliente}.callix.com.br/api/v4/entities/user-performance-histories'
        url_get_tech = f'https://{self.cliente}.callix.com.br/api/v4/entities/accounts'
        
        lista_de_urls_de_agressividade = []
        for campanha in self.id_campanha:
            url_agressividade = f'https://{self.cliente}.callix.com.br/api/v4/entities/campaigns/{campanha}'
            lista_de_urls_de_agressividade.append(url_agressividade)
        return url_login, url_chamadas_agentes, lista_de_urls_de_agressividade, url_base
    
    def login_callix(self, url_login, url_base):
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                       headers=headers_login_callix(url_base),
                                       url=url_login
                                       )
        log.info(f"Resposta do login {login.status_code}")
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
        log.info(f"Chamadas agentes {chamadas_por_agentes.status_code}")
        return chamadas_por_agentes
    
    def agressividade(self, url_agressividade, token):
        # pode haver mais de uma campanha o que gera mais de uma agressividade
        lista_json_agressividade = []
        
        for url_unico_de_agressividade in url_agressividade:
            agressividade = self.http_request.requisicao_get(headers=headers_callix(token),
                                        url=url_unico_de_agressividade,
                                        payload_get=payload_agressividade()
                                        )
            lista_json_agressividade.append(agressividade)
        log.info(f"Agressividade {agressividade.status_code}")
        return lista_json_agressividade

    def get_tech_cliente(self):
        tech = self.http_request.requisicao_get(
            headers=headers_callix(self.token),
            url=self.url.url_get_tech(self.cliente),
            payload_get=payload_get_tech()
            )
        log.info(f"Tech Cliente {tech.status_code}")

        return tech

    def get_chamadas_abandonadas(self):
        abandonadas = self.http_request.requisicao_get(
            headers=headers_callix(self.token),
            url=self.url.teste_url_agressividade(self.cliente),
            payload_get=payload_abandonadas_teste(self.data)
        )
        print(f"RESULTADO ABANDONADAS: {abandonadas}")
        print(f"RESULTADO ABANDONADAS STATUS: {abandonadas.status_code}")
        print(f"RESULTADO ABANDONADAS JSON: {abandonadas.text}")
        print(f"RESULTADO ABANDONADAS URL: {abandonadas.headers}")

    def requisicao_callix(self):
        url_login, url_chamadas_agentes, url_agressividade, url_base = self.url_callix()

        login = self.login_callix(url_login, url_base)
        url_final = self.conversor_de_url(url_chamadas_agentes)
        chamadas_por_agentes = self.get_chamadas_agentes(url_final, url_chamadas_agentes, login)
        agressividade = self.agressividade(url_agressividade, login) # lista
        agressividade = self.get_chamadas_abandonadas()
        tech = self.get_tech_cliente()
        
        return chamadas_por_agentes, agressividade, tech