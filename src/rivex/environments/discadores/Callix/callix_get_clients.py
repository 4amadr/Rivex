import requests
import os
from dotenv import load_dotenv
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import *
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.utils.environments_utils.discador.callix.get_url_callix import UrlGetClients, UrlGetData
import logging

load_dotenv()
log = logging.getLogger(__name__)


class CallixGetClients:
    """
    Classe que vai coletar as URLs de clientes
    que estão ativos no ambiente da empresa
    """
    
    def __init__(self):
        self.url_geral = os.getenv('URL_CALLIX_GERAL')
        self.http_requisition = HttpRequisitions(session=requests.Session())
        self.usuario = os.getenv('USUARIO_CALLIX_GERAL')
        self.senha = os.getenv('SENHA_CALLIX_GERAL')
        self.url = UrlGetClients()

        
    def login_ambiente_padrao(self):
        '''Loga no ambiente padrão e retorna a sessão'''
        login = self.http_requisition.requisicao_post_json(url=self.url.url_login_servidor_contech(),
                                              payload_post=payload_login_callix(login_ambiente=self.usuario, password=self.senha),
                                              headers=headers_servidor_callix()
                                              )
        return self.http_requisition.session
    
    def get_cliente_nome(self):
        self.login_ambiente_padrao()
        cliente_ativo = self.http_requisition.requisicao_get(headers=headers_servidor_callix(),
                                                             url=self.url.url_get_clients(),
                                                             payload_get=payload_servidor_callix())
        return cliente_ativo
    
    def get_infos_callix(self):
        self.login_ambiente_padrao()
        nome_clientes_ativos = self.get_cliente_nome()
        return nome_clientes_ativos
    
class GetTokenCallix:
    """
    Classe que vai coletar os tokens do cliente ativo 
    para realizar requisições de API 
    """
    
    def __init__(self):
        self.login = os.getenv('USUARIO_CALLIX_GERAL')
        self.senha = os.getenv('SENHA_CALLIX_GERAL')
        self.http_request = HttpRequisitions(session=requests.Session())
        self.url = UrlGetData()

    def login_callix(self, cliente):
        log.info(f"Cliente logado atualmente {cliente}")
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                        headers=headers_login_callix(self.url.login_cliente_header(cliente)),
                                        url=self.url.login_cliente(cliente)
                                        )
        log.info(f"Resposta do cliente novo: {cliente}, {login.status_code}")
        token = login.json()['token']
        return token

    def get_token(self, token, cliente):
        '''Retorna o token do cliente usado em requisições de API'''
        tokens_api = self.http_request.requisicao_get(url=self.url.url_tokens(cliente),
                                                        payload_get=payload_get_tokens(),
                                                        headers=gerar_headers_para_tokens(token, cliente))
        return tokens_api.json()

    def fluxo_de_tokens(self, clientes_ativos):
        lista_tokens = []
        
        for selecao_cliente in clientes_ativos:
            url = UrlGetData()
            
            # login no ambiente
            token_login = self.login_callix(selecao_cliente)
            
            # token
            tokens_api = self.get_token(token_login, selecao_cliente)
            token = [token_cliente['attributes']['token'] for token_cliente in tokens_api['data']]
            lista_tokens.append(token)
        return lista_tokens
