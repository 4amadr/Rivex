from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *
from src.rivex.data_processing.IPBox.limpeza_ipbox import *
import requests
import logging
from typing import Dict, Any, Tuple
from collections import namedtuple
from requests.models import Response

# Configuração de log
logger = logging.getLogger(__name__)

class IpboxInit:
    def __init__(self, url, login, senha, data):
        self.url = url
        self.login = login
        self.senha = senha
        self.data = data
        self.http_client = HttpRequisitions(session=requests.session())
        
    def _gerar_url_login(self):
        return f'{self.url}/contech/autenticacao.php'

    def _gerar_url_clientes(self):
        return f'{self.url}/contech/viewRelatTelefoniaAtivo.php'
        
    def login_ipbox(self) -> requests.Session:
        '''
        Autenticação e retorna a sessão logada
        '''
        logger.info("Iniciando login no ipbox...")
        url_login = self._gerar_url_login()
        try:
            self.http_client.requisicao_post(payload_post=payload_login_ipbox(self.login, self.senha),
                                            headers=headers_ipbox(),
                                            url=url_login)
            logger.info("Autenticação no ipbox feita com sucesso")

            return self.http_client.session
        except Exception as e:
            logger.error("Falha no login no ipbox", exc_info=True)
            raise ConnectionError(f"Erro de conexão no login: {e}")
    
    def buscar_lista_clientes(self) -> Dict[str, Any]:
        '''
        Faz a coleta e o parse da lista de clientes
        presente no discador
        '''
        url_get_clientes = self._gerar_url_clientes()
        try:
            cliente_ipbox = self.http_client.requisicao_get(payload_get=payload_get_clientes,
                                                headers=headers_ipbox(),
                                                url=url_get_clientes)
            return parse_id_clientes(cliente_ipbox) 
        except Exception as e:
            logger.error("Falha ao tentar coletar clientes do IPBOX", exc_info=True)
            raise ConnectionError(f"Erro ao buscar clientes: {e}")
    
    def execucao_base_ipbox(self):
        """
        Orquestrador publico da classe
        """
        sessao_logada = self.login()
        clientes_ativos = self.buscar_lista_clientes()
        
        logger.info("Base IPBOX finalizada e pronta para uso.")
        
        # Retorna os dados agrupados de forma segura e limpa
        return sessao_logada, clientes_ativos


class IpboxClientConfig:
    IpboxColectData = namedtuple("IpboxColectData", [
        ("agressividade_html", str),
        ("chamadas", Response),
        ("agentes", Response)
    ])

    def __init__(self, url, login, senha, data, data_agentes, sessao_anterior, token):
        self.url = url.rstrip('/')
        self.login = login
        self.senha = senha
        self.data = data
        self.data_agentes = data_agentes
        self.session = sessao_anterior
        self.http_client = HttpRequisitions(session=sessao_anterior)
        self.token = token

    def gerador_de_url_configs(self):
        url_agressividade = f'{self.url}/contech/editFila.php?act=alter&obj_fila_id={self.id_cliente}'
        url_relatorio_chamadas = f'{self.url}ipbox/api/getTA1'
        url_relatorio_agentes = f'{self.url}ipbox/api/getPA1'

        return url_agressividade, url_relatorio_chamadas, url_relatorio_agentes

    def get_agressividade(self, url_agressividade):
        '''
        Vai ser executado em loop de iteração para retornar um cliente de cada vez
        o retorno esperado é o HTML da página de configuração de clientes onde o valor desejado
        é o valor de overdial
        '''
        return self.http_client.requisicao_get(headers=headers_ipbox(),
                                               url=url_agressividade,
                                               payload_get={})

    def get_relatorio_chamadas(self, url_relatorio_chamadas, nome_cliente): # coleta feita com API disponibilizada na documentação do ambiente
        return self.hr.requisicao_post(headers=headers_api_telefonia(self.token),
                                          payload_post=payload_api_telefonia(self.data, nome_cliente),
                                          url=url_relatorio_chamadas)

    def get_relatorio_agente(self, url_relatorio_agentes):
        return self.hr.requisicao_post(headers=headers_api_telefonia(self.token),
                                         payload_post=self.data_agentes,
                                         url=url_relatorio_agentes)

    def execucao_ipbox(self, nome_cliente):
        url_agressividade, url_relatorio_chamadas, url_relatorio_agentes = self.gerador_de_url_configs()


        agressividade = self.get_agressividade(url_agressividade)
        chamadas = self.get_relatorio_chamadas(nome_cliente, url_relatorio_chamadas)
        agentes = self.get_relatorio_agente(url_relatorio_agentes)

        return IpboxColectData(
            agressividade_html=agressividade.text,
            chamadas=chamadas,
            agentes=agentes
        )

