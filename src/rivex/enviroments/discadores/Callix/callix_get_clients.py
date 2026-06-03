import requests
import os
from dotenv import load_dotenv
from src.rivex.enviroments.discadores.Callix.callix_req import *
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.Callix.payloads_callix import *
from src.rivex.enviroments.discadores.Callix.callix_req import *

load_dotenv()

class CallixGetClients:
    def __init__(self):
        self.url_geral = os.getenv('URL_CALLIX_GERAL')
        self.http_requisition = HttpRequisitions(session=requests.Session())
        self.usuario = os.getenv('USUARIO_CALLIX_GERAL')
        self.senha = os.getenv('SENHA_CALLIX_GERAL')

    def login_ambiente_padrao(self):
        '''Loga no ambiente padrão e retorna a sessão'''
        url_login = f"{self.url_geral}/api/v4/auth/session"
        print("URL DE LOGIN: ", url_login)
        login = self.http_requisition.requisicao_post_json(url=url_login,
                                              payload_post=payload_login_callix(login_ambiente=self.usuario, password=self.senha),
                                              headers=headers_servidor_callix()
                                              )
        return self.http_requisition.session

    def get_client_url(self):
        '''Função para retornar a url dos ambientes'''
        url_callix = f'{self.url_geral}/api/v4/tenants/sub-accounts'
        print("URL PARA COLETAR AS URL: ",url_callix)
        url_clientes = self.http_requisition.requisicao_get(headers=headers_servidor_callix(),
                                                            url=url_callix,
                                                            payload_get=payload_servidor_callix())
        print("Resposta da requisição de url de clientes no callix: ", url_clientes.status_code)
        return url_clientes
    
    def login_callix(self, cliente):
        url_base = f'https://{cliente}contech.callix.com.br/login'
        url_login = f'https://{cliente}contech.callix.com.br/api/v4/auth/session'
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                        headers=headers_login_callix(url_base),
                                        url=url_login
                                        )
        token = login.json()["token"]
        return token
    
    def get_token(self, cliente):
        '''Retorna o token do cliente usado em requisições de API'''

        url_tokens = f'https://{cliente}contech.callix.com.br/api/v4/entities/api-tokens'
        tokens_api = self.http_request.requisicao_get(url=url_tokens,
                                                      payload_get=payload_get_tokens(),
                                                      headers=headers_callix())
        print("RESULTADO DA REQUISIÇÃO DE TOKENS DO AMBIENTE CALLIX: ", tokens_api.status_code)
        print("TOKENS: ", tokens_api)
        return tokens_api
    
    def get_infos_callix(self):
        self.login_ambiente_padrao()
        url_clientes = self.get_client_url()
        return url_clientes  
    

class GetTokenCallix:
    def __init__(self, cliente):
        self.login = os.getenv('USUARIO_CALLIX_GERAL')
        self.senha = os.getenv('SENHA_CALLIX_GERAL')
        self.http_request = HttpRequisitions(session=requests.Session())
        self.cliente = cliente

    def login_callix(self):
        url_base = f'https://{self.cliente}.callix.com.br/login'
        url_login = f'https://{self.cliente}.callix.com.br/api/v4/auth/session'
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                        headers=headers_login_callix(url_base),
                                        url=url_login
                                        )

        token = login.json()['token']
        return token

    def get_token(self, token):
        '''Retorna o token do cliente usado em requisições de API'''

        url_tokens = f'https://{self.cliente}.callix.com.br/api/v4/entities/api-tokens'
        tokens_api = self.http_request.requisicao_get(url=url_tokens,
                                                        payload_get=payload_get_tokens(),
                                                        headers=gerar_headers_para_tokens(token, self.cliente))
        print(url_tokens)
        print(tokens_api.request.headers)
        print(tokens_api.request.body)
        print(tokens_api.json())
        return tokens_api.json()

    def fluxo_de_tokens(self):
        print("LOGANDO PARA PEGAR OS TOKENS")
        token_login = self.login_callix()
        print("LOGADO")
        tokens_api = self.get_token(token_login)
        print("COLETA DE TOKENS FINALIZADA")
        
        return {
            "Cliente": self.cliente,
            "Token do cliente": tokens_api
        }
