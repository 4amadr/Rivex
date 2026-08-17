from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.environments.discadores.IPBox.payloads_ipbox import *
from src.rivex.data_processing.IPBox.limpeza_ipbox import *
from src.rivex.utils.utils_system.server_retry import *
import requests
import logging
from typing import Dict, Any, NamedTuple
from collections import namedtuple
from requests.models import Response

# Configuração de log
logger = logging.getLogger(__name__)

class UrlIpbox:
    def __init__(self, url):
        self.url = url

    def _gerar_url_login(self):
        return f'{self.url}/contech/autenticacao.php'
    
    def _gerar_url_clientes(self):
        return f'{self.url}/contech/listFila.php'
    
    def _gerar_url_agressividade(self):
        return f'{self.url}/contech/editFila.php?act=alter&obj_fila_id=' # carece do id do cliente
    
    def _gerar_url_relatorio_chamadas(self):
        return f'{self.url}/ipbox/api/getTA1'
    
    def _gerar_url_relatorio_agentes(self):
        return f'{self.url}/ipbox/api/getPA1'
    
class IpboxInit:
    def __init__(self, login, senha, data, url):
        self.url = UrlIpbox(url)
        self.login = login
        self.senha = senha
        self.data = data
        self.http_client = HttpRequisitions(session=requests.session())
        
        
    def login_ipbox(self) -> requests.Session:
        '''
        Autenticação e retorna a sessão logada
        '''
        login = self.http_client.requisicao_post(payload_post=payload_login_ipbox(self.login, self.senha),
                                            headers=headers_ipbox(),
                                            url=self.url._gerar_url_login())

        return self.http_client.session

    
    @tentar_novamente()
    def buscar_lista_clientes(self) -> Dict[str, Any]:
        '''
        Faz a coleta e o parse da lista de clientes
        presente no discador
        '''
        return self.http_client.requisicao_get(payload_get=payload_get_clientes,
                                                headers=headers_ipbox(),
                                                url=self.url._gerar_url_clientes())
    
    def execucao_base_ipbox(self):
        """
        Orquestrador publico da classe
        """
        return self.login_ipbox(), self.buscar_lista_clientes().text # type: ignore


class IpboxClientConfig:

    def __init__(self, url, login, senha, data, data_agentes, sessao_anterior, token):
        self.url = UrlIpbox(url)
        self.login = login
        self.senha = senha
        self.data = data
        self.data_agentes = data_agentes
        self.session = sessao_anterior
        self.http_client = HttpRequisitions(session=sessao_anterior)
        self.token = token

    def get_agressividade(self, id_cliente):
        '''
        Vai ser executado em loop de iteração para retornar um cliente de cada vez
        o retorno esperado é o HTML da página de configuração de clientes onde o valor desejado
        é o valor de overdial
        '''
        return self.http_client.requisicao_get(headers=headers_ipbox(),
                                               url=f"{self.url._gerar_url_agressividade()}{id_cliente}",
                                               payload_get={})

    def get_relatorio_chamadas(self, nome_cliente): # coleta feita com API disponibilizada na documentação do ambiente
        return self.http_client.requisicao_post(headers=headers_api_telefonia(self.token),
                                          payload_post=payload_api_telefonia(self.data, nome_cliente),
                                          url=self.url._gerar_url_relatorio_chamadas())


    def get_relatorio_agente(self):
        return self.http_client.requisicao_post(headers=headers_api_telefonia(self.token),
                                         payload_post=self.data_agentes,
                                         url=self.url._gerar_url_relatorio_agentes())

    def execucao_ipbox(self, nome_cliente, id_cliente):
        return self.get_agressividade(id_cliente).text, self.get_relatorio_chamadas(nome_cliente).json()