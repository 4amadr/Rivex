import os
import requests
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.vonix.payloads_vonix import *
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
from src.rivex.utils.infra_utils.vonix_processing import ClientSimulator
from src.rivex.data_processing.Vonix.cleaning_vonix import *

'''Classe feita para executar cada etapa do discador vonix contando com
Login + TOKEN -> Filtragem + TOKEN -> Chamadas + TOKEN -> Agentes online + TOKEN -> Agressividade + TOKEN'''

class GerarUrlVonix:
    def __init__(self, url_base):
        self.url_base = url_base
        
    def _url_base(self):
        return self.url_base
    
    def _url_login(self):
        return f"{self.url_base}/login/signin"
    
    def _url_filtragem(self):
        return f"{self.url_base}/login/set_show_queue"
    
    def _url_get_agentes(self):
        return f"{self.url_base}/agents/calls_overview"
    
    def _url_get_agressividade(self):
        return f"{self.url_base}/admin/queue_edit/"
    
    def _url_get_chamadas(self):
        return f"{self.url_base}/calls"
    

class ExecucaoVonix:
    def __init__(self, login, senha, data, url_base):
        self.login = login
        self.senha = senha
        self.data = data
        self.url_base = url_base
        self.session = requests.Session()
        self.url = GerarUrlVonix(url_base)
        self.http_requisitions = HttpRequisitions(self.session)
        self.real_client = ClientSimulator(self.session)

    def get_cookie(self):
        return self.session.get(self.url._url_login())


    
    def login_vonix(self, token):
        return self.http_requisitions.requisicao_post(payload_post=payload_de_login(self.login, self.senha, token), headers=headers(), url=self.url._url_login())
    

    def get_clientes_ambiente(self):
        return self.http_requisitions.requisicao_get(payload_get={},
                                                     headers={},
                                                     url=self.url.url_base)
        
    
    def get_filtragem(self, equipe, token):
        # função que executa todo o processo de filtragem do vonix
        return self.http_requisitions.requisicao_post(payload_de_filtragem(token, equipe), headers(), self.url._url_filtragem())


    def get_chamadas(self, tipo_chamada: str | None = None):
        return self.http_requisitions.requisicao_get(payload_get=payload_de_chamadas(self.data, tipo_chamada),
                                                     headers=headers(),
                                                     url=self.url._url_get_chamadas()
                                                     )

    
    def get_agentes(self):
        return self.http_requisitions.requisicao_get(payload_get=payload_de_agentes(self.data),
                                    headers=headers(),
                                    url=self.url._url_get_agentes())
    
    def coleta_de_agressividade_vonix(self, cliente, token):
        # função para coletar informações de agressividade por equipe     
        return self.http_requisitions.requisicao_get(payload_get=payload_de_agressividade(token),
                                          headers=headers(), 
                                          url=f"{self.url._url_get_agressividade()}{cliente}")

    def token_pronto(self):
        """
        FLUXO deve seguir uma ordem lógica, após o login a filtragem de clientes é fundamental
        caso contrário o ambiente retorna o HTML da página de login
        """
        tokens = self.get_cookie()
        html_token = get_html(tokens.text)
        token_vonix = get_token(html_token)
        return token_vonix
        
    def get_clientes(self, token):
        login = self.login_vonix(token)
        clientes = self.get_clientes_ambiente()
        return clientes.text
    

        
