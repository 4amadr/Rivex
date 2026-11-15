from src.rivex.utils.environments_utils.discador.callix.payloads_callix import payload_create_tokens
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import gerar_headers_para_tokens
import requests
import os
from dotenv import load_dotenv
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import *
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.utils.environments_utils.discador.callix.get_url_callix import UrlGetClients, UrlGetData
from src.rivex.utils.logging_config.logging_config import LoggingConfig


class CallixGetClients:
    
    def __init__(self):
        load_dotenv()
        self.url_geral = os.getenv('URL_CALLIX_GERAL')
        self.http_requisition = HttpRequisitions(session=requests.Session())
        self.usuario = os.getenv('USUARIO_CALLIX_GERAL')
        self.senha = os.getenv('SENHA_CALLIX_GERAL')
        self.token = os.getenv('TOKEN_CALLIX')
        self.url = UrlGetClients()
        self.log = LoggingConfig('get_client', 'Extract')
        
        
    def login_ambiente_padrao(self):
        """Autentica no ambiente geral do Callix."""

        resposta = self.http_requisition.requisicao_post_json(
            url=self.url.url_login_servidor_contech(),
            payload_post=payload_login_callix(
                login_ambiente=self.usuario,
                password=self.senha,
                token=self.token
            ),
            headers=headers_servidor_callix()
        )
        
        print(resposta.json())
        return resposta

    
    def get_cliente_nome(self):
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
        self.log = LoggingConfig('get_token', 'config_sys')

    def login_callix(self, cliente):
        self.log.log_info(f"Cliente logado atualmente", cliente)
        login = self.http_request.requisicao_post_json(payload_post=payload_login_callix(self.login, self.senha),
                                        headers=headers_login_callix(self.url.login_cliente_header(cliente)),
                                        url=self.url.login_cliente(cliente)
                                        )
        self.log.log_info(f"Resposta do cliente novo: {cliente}", {login.status_code})
        token = login.json()['token']
        return token

    def get_token(self, token, cliente):
        '''Retorna o token do cliente usado em requisições de API'''
        tokens_api = self.http_request.requisicao_get(
            url=self.url.url_tokens(cliente),
            payload_get=payload_get_tokens(),
            headers=gerar_headers_para_tokens(token, cliente)
            )
        return tokens_api.json()

    def create_token(self, token, cliente):
        """vai criar e retornar o token caso o cliente não tenha nenhum token ativo
        """
        return self.http_request.requisicao_post(
            url=self.url.url_create_tokens(cliente),
            headers=gerar_headers_para_tokens(token, cliente),
            payload_post=payload_create_tokens())
        


    def fluxo_de_tokens(self, clientes_ativos):
        lista_tokens = []

        for selecao_cliente in clientes_ativos:
            try:
                # Login no ambiente do cliente
                token_login = self.login_callix(selecao_cliente)

            except Exception as e:
                self.log.log_erro(
                    f"Falha no login para o cliente {selecao_cliente}",
                    e
                )
                continue

            tokens_api = self.get_token(
                token=token_login,
                cliente=selecao_cliente
            )

            dados = tokens_api.get("data") or []

            token = (
                dados[0].get("attributes", {}).get("token")
                if dados
                else None
            )

            # Se não houver token, tenta criar e consultar novamente
            if not token:
                self.create_token(token=token_login, cliente=selecao_cliente)

                tokens_novos = self.get_token(
                    token=token_login,
                    cliente=selecao_cliente
                )

                dados_novos = tokens_novos.get("data") or []

                token = (
                    dados_novos[0].get("attributes", {}).get("token")
                    if dados_novos
                    else None
                )

            if not token:
                self.log.log_erro(
                    f"Não foi possível obter o token do cliente "
                    f"{selecao_cliente}",
                    None
                )
                continue

            lista_tokens.append(token)

        return lista_tokens
