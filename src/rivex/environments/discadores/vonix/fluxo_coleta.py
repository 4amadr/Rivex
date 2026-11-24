from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from src.rivex.domain.exceptions import ErroAutenticacao
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
        return f"{self.url_base}/calls"

    def _url_operadores_cliente(self) -> str:
        return f"{self.url_base}/admin/agent_list"


class ExecucaoVonix:
    def __init__(self, login: str, senha: str, data: str, url_base: str):
        self.login = login
        self.senha = senha
        self.data = data
        self.url_base = (url_base or "").rstrip("/")
        self.session = requests.Session()
        self.url = GerarUrlVonix(self.url_base)
        self.http_requisitions = HttpRequisitions(self.session, servico="vonix")

    def get_cookie(self):
        return self.http_requisitions.requisicao_get(
            headers=headers(),
            url=self.url._url_login(),
            payload_get={},
        )

    def get_html(self, pag: str) -> BeautifulSoup:
        return BeautifulSoup(pag, "html.parser")

    def get_token(self, token_html: BeautifulSoup) -> str:
        token = token_html.find("input", {"name": "authenticity_token"})
        if token is None:
            raise ValueError("Não foi encontrado o token de autenticidade do vonix!")
        return token.get("value")

    def login_vonix(self, token: str) -> requests.Response:
        resposta = self.http_requisitions.requisicao_post(
            payload_post=payload_de_login(self.login, self.senha, token),
            headers=headers(),
            url=self.url._url_login(),
        )
        if "login/signin" in (resposta.url or "").lower():
            raise ErroAutenticacao("Falha na autenticação do Vonix: credenciais inválidas.")
        return resposta

    def get_clientes_ambiente(self) -> requests.Response:
        resposta = self.http_requisitions.requisicao_get(
            payload_get={},
            headers={},
            url=self.url.url_base,
        )
        if "login/signin" in (resposta.url or "").lower():
            raise ErroAutenticacao("Sessão Vonix inválida ao consultar lista de clientes.")
        return resposta

    def get_filtragem(self, equipe: str, token: str) -> requests.Response:
        resposta = self.http_requisitions.requisicao_post(
            payload_de_filtragem(token, equipe),
            headers(),
            self.url._url_filtragem(),
        )
        if "login/signin" in (resposta.url or "").lower():
            raise ErroAutenticacao(f"Sessão Vonix expirada ao filtrar cliente {equipe}.")
        return resposta

    def get_chamadas(self, tipo_chamada: str | None = None):
        return self.http_requisitions.requisicao_get(
            payload_get=payload_de_chamadas(self.data, tipo_chamada),
            headers=headers(),
            url=self.url._url_get_chamadas(),
        )

    def get_agentes(self):
        return self.http_requisitions.requisicao_get(
            payload_get=payload_de_agentes(self.data),
            headers=headers(),
            url=self.url._url_get_agentes(),
        )

    def get_operadores_cliente(self, token=None):
        """Coleta a lista HTML de operadores vinculados ao(s) cliente(s) filtrado(s) na sessão."""
        return self.http_requisitions.requisicao_get(
            payload_get=payload_de_operadores_cliente(),
            headers=headers_operadores_cliente(self.url_base, token),
            url=self.url._url_operadores_cliente(),
        )

    def coleta_de_agressividade_vonix(self, cliente: str, token: str):
        return self.http_requisitions.requisicao_get(
            payload_get=payload_de_agressividade(token),
            headers=headers(),
            url=f"{self.url._url_get_agressividade()}{cliente}",
        )

    def token_pronto(self) -> str:
        tokens = self.get_cookie()
        html_token = self.get_html(tokens.text)
        return self.get_token(html_token)

    def get_clientes(self, token: str) -> str:
        self.login_vonix(token)
        clientes = self.get_clientes_ambiente()
        return clientes.text
