import requests
import os
from dotenv import load_dotenv
from src.rivex.enviroments.discadores.Callix.callix_req import *
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.Callix.payloads_callix import *
from src.rivex.enviroments.discadores.Callix.callix_req import *

load_dotenv()

class CallixGetClients:
    def __init__(self, usuario, senha):
        self.url_geral = os.getenv('URL_CALLIX_GERAL')
        self.http_requisition = HttpRequisitions(session=requests.session)
        self.usuario = usuario
        self.senha = senha

    def login_ambiente_padrao(self):
        '''Loga no ambiente padrão e retorna a sessão'''
        url_login = f"{self.url_geral}/login"
        self.http_requisition.requisicao_post(url=url_login,
                                              payload_post=payload_login_callix(login_ambiente=self.usuario, password=self.senha),
                                              headers=headers_login_callix()
                                              )
        return self.http_client.session

    def get_client_url(self):
        '''Função para retornar a url dos ambientes'''
        url_callix = f'{self.url_geral}/api/v4/tenants/sub-accounts?page[limit]=100'
        print(url_callix)
        url_clientes = self.http_requisition.requisicao_get(headers=headers_servidor_callix(),
                                                            url=url_callix,
                                                            payload_get=payload_servidor_callix())
        print("Resposta da requisição de url de clientes no callix: ", url_clientes.status_code)
        print(url_clientes.json())
        return url_clientes
    
    def get_tech(self):
        '''Função para retornar a tech dos clientes que será usada como id posteriormente'''
        url_tech = f"{self.url_geral}/api/v4/entities/outbound-routes"
        techs_clientes = self.http_requisition.requisicao_get(headers=headers_servidor_callix(),
                                                              url=url_tech,
                                                              payload_get=payload_techs_callix())
        print("Resposta da requisição de techs dos clientes no callix: ", techs_clientes.status_code)
        print(techs_clientes.json())
        return techs_clientes
    
    def get_infos_callix(self):
        url_clientes = self.get_client_url()
        tech_clientes = self.get_tech()
        return url_clientes, tech_clientes