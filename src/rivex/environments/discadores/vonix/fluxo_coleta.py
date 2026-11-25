from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from src.rivex.environments.discadores.vonix.payloads_vonix import (
    headers,
    headers_operadores_cliente,
    payload_de_agentes,
    payload_de_agressividade,
    payload_de_chamadas,
    payload_de_filtragem,
    payload_de_login,
    payload_de_operadores_cliente,
)
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.beautiful_soup_utils.login_parser import get_token_login_vonix



class GerarUrlVonix:
    def __init__(self, url_base: str):
        self.url_base = (url_base or "").rstrip("/")

    def _url_login(self) -> str:
        return f"{self.url_base}/login/signin"

    def _url_filtragem(self) -> str:
        return f"{self.url_base}/login/set_show_queue"

    def _url_get_agentes(self) -> str:
        return f"{self.url_base}/agents/calls_overview"

    def _url_get_agressividade(self) -> str:
        return f"{self.url_base}/admin/queue_edit/"

    def _url_get_chamadas(self) -> str:
        return f"{self.url_base}/overview/calls"

    def _url_get_filas(self):
        return f"{self.url_base}/admin/queues"

    def _url_operadores_cliente(self) -> str:
        return f"{self.url_base}/admin/agent_list"

    def _url_get_agentes_ativos(self):
        return f"{self.url_base}/admin/agents"

    def _url_get_desempenho(self, equipe: str):
        return f"{self.url_base}/admin/queue_edit/{equipe}"

    def _url_get_opradores(self):
        return f"{self.url_base}/agents/calls_overview"


class ExecucaoVonix:
    def __init__(self, login: str, senha: str, data: str, url_base: str):
        self.login = login
        self.senha = senha
        self.data = data
        self.url_base = (url_base or "").rstrip("/")
        self.session = requests.Session()
        self.url = GerarUrlVonix(self.url_base)
        self.http_requisitions = HttpRequisitions(self.session, servico="vonix")

    def _get_token(self):
        return self.http_requisitions.req_get(
            url=self.url._url_login(),
            headers=headers,
            payload={}
        )

    def _login(self, token):
        return self.http_requisitions.req_post(
            url=self.url._url_login(),
            headers=headers,
            payload=payload_de_login(token=token)
        )

    def _get_filas(self):
        return self.http_requisitions.req_get(
            url=self.url._url_get_filas(),
            headers=headers,
            payload={}
        )

    def _get_agentes_ativos(self):
        return self.http_requisitions.req_get(
            url=self.url._url_get_agentes_ativos(),
            headers=headers,
            payload={}
        )

    def _get_desempenho(self, equipe):
        return self.http_requisitions.req_get(
                url=self.url._url_get_desempenho(equipe),
                headers=headers,
                payload={}
        )

    def _get_chamadas(self):
        return self.http_requisitions.req_get(
            url=self.url._url_get_chamadas(),
            headers=headers,
            payload={}
        )


    def execucao(self):

        token = self._get_token()
        token_limpo = get_token_login_vonix(token)

        self._login(token_limpo)


        filas = self._get_filas()
        agentes_validos = self._get_agentes_ativos()
        desempenho = self._get_desempenho(filas)
        chamadas = self._get_chamadas()






        