import requests
import os
from dotenv import load_dotenv


from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.enviroments_utils.discador.callix.payloads_callix import *
from src.rivex.enviroments.discadores.Callix.callix_req import *
from src.rivex.utils.enviroments_utils.discador.callix.get_url_callix import *

load_dotenv()

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
    
    def get_tech_clientes_callix(self):
        self.login_ambiente_padrao()
        techs_clientes = self.http_requisition.requisicao_get(headers=headers_servidor_callix(),
                                                          url=self.url.url_get_tech(),
                                                          payload_get={})

        return techs_clientes.json()
    
    def get_cliente_nome(self):
        self.login_ambiente_padrao()
        cliente_ativo = self.http_requisition.requisicao_get(headers=headers_servidor_callix(),
                                                             url=self.url.url_get_clients(),
                                                             payload_get=payload_servidor_callix())
        return cliente_ativo
    
    def get_infos_callix(self):
        self.login_ambiente_padrao()
        url_clientes = self.get_tech_clientes_callix()
        clientes_ativos = self.get_cliente_nome()
        return url_clientes, clientes_ativos
    
class GetTokenCallix:
    """
    Classe que vai coletar os tokens do cliente ativo 
    para realizar requisições de API 
    """
    
    def __init__(self, cliente_lista):
        self.login = os.getenv('USUARIO_CALLIX_GERAL')
        self.senha = os.getenv('SENHA_CALLIX_GERAL')
        self.http_request = HttpRequisitions(session=requests.Session())
        self.cliente_lista = cliente_lista

    def login_callix(self, url):
        print("[DEBUG LOGIN CALLIX]")
        print(f"url_cliente: {self.url.login_cliente()}")
        print(f"header: {self.url.login_cliente_header()}")
        print(f"payload: {payload_login_callix(self.login, self.senha)}")
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                        headers=headers_login_callix(self.url.login_cliente_header()),
                                        url=self.url.login_cliente()
                                        )
        print(f"Resposta do login para coletar os tokens: {login.status_code}")


        token = login.json()['token']
        return token

    def get_token(self, token):
        '''Retorna o token do cliente usado em requisições de API'''
        tokens_api = self.http_request.requisicao_get(url=self.url.url_tokens(),
                                                        payload_get=payload_get_tokens(),
                                                        headers=gerar_headers_para_tokens(token, self.cliente))
        return tokens_api.json()

    def fluxo_de_tokens(self):
        lista_tokens = []
        
        for selecao_cliente in self.cliente_lista:
            url = UrlGetData(selecao_cliente)
            
            # login no ambiente
            token_login = self.login_callix()
            
            # token
            tokens_api = self.get_token(token_login)
            token = [token_cliente['attributes']['token'] for token_cliente in tokens_api['data']]
            
            dict_infos_cliente = {
                "Cliente": selecao_cliente.replace("contech", ""),
                "Token": token
            }
            lista_tokens.append(dict_infos_cliente)
        return lista_tokens
