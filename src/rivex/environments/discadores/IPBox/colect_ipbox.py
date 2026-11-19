from __future__ import annotations

import requests

from src.rivex.domain.exceptions import ErroAutenticacao
from src.rivex.environments.discadores.IPBox.payloads_ipbox import (
    headers_api_telefonia,
    headers_ipbox,
    payload_api_telefonia,
    payload_get_clientes,
    payload_login_ipbox,
)
from src.rivex.utils.requests_utils.requests import HttpRequisitions


class UrlIpbox:
    def __init__(self, url: str):
        self.url = (url or "").rstrip("/")

    def _gerar_url_login(self) -> str:
        return f"{self.url}/contech/autenticacao.php"

    def _gerar_url_clientes(self) -> str:
        return f"{self.url}/contech/listFila.php"

    def _gerar_url_agressividade(self) -> str:
        return f"{self.url}/contech/editFila.php?act=alter&obj_fila_id="

    def _gerar_url_relatorio_chamadas(self) -> str:
        return f"{self.url}/ipbox/api/getTA1"

    def _gerar_url_relatorio_agentes(self) -> str:
        return f"{self.url}/ipbox/api/getPA1"


class IpboxInit:
    def __init__(self, login: str, senha: str, data: str, url: str):
        self.url = UrlIpbox(url)
        self.login = login
        self.senha = senha
        self.data = data
        self.http_client = HttpRequisitions(session=requests.Session(), servico="ipbox")

    def login_ipbox(self) -> requests.Session:
        """Autentica no IPBox e valida se a sessão foi aceita."""
        resposta = self.http_client.requisicao_post(
            payload_post=payload_login_ipbox(self.login, self.senha),
            headers=headers_ipbox(),
            url=self.url._gerar_url_login(),
        )
        corpo_lower = (resposta.text or "").lower()
        if "autenticacao.php" in (resposta.url or "").lower() and "dologin" in corpo_lower:
            raise ErroAutenticacao("Falha na autenticação do IPBox: credenciais inválidas.")
        return self.http_client.session

    def buscar_lista_clientes(self) -> requests.Response:
        """Coleta o HTML com a relação de clientes ativos no IPBox."""
        resposta = self.http_client.requisicao_get(
            payload_get=payload_get_clientes,
            headers=headers_ipbox(),
            url=self.url._gerar_url_clientes(),
        )
        if "autenticacao.php" in (resposta.url or "").lower():
            raise ErroAutenticacao("Sessão IPBox expirada ou não autenticada ao listar clientes.")
        return resposta

    def execucao_base_ipbox(self) -> tuple[requests.Session, str]:
        """Orquestrador público da classe."""
        sessao = self.login_ipbox()
        clientes_html = self.buscar_lista_clientes().text
        return sessao, clientes_html


class IpboxClientConfig:
    def __init__(
        self,
        url: str,
        login: str,
        senha: str,
        data: str,
        data_agentes: dict[str, str],
        sessao_anterior: requests.Session,
        token: str,
    ):
        self.url = UrlIpbox(url)
        self.login = login
        self.senha = senha
        self.data = data
        self.data_agentes = data_agentes
        self.session = sessao_anterior
        self.http_client = HttpRequisitions(session=sessao_anterior, servico="ipbox")
        self.token = token

    def get_agressividade(self, id_cliente: str) -> requests.Response:
        return self.http_client.requisicao_get(
            headers=headers_ipbox(),
            url=f"{self.url._gerar_url_agressividade()}{id_cliente}",
            payload_get={},
        )

    def get_relatorio_chamadas(self, nome_cliente: str) -> requests.Response:
        return self.http_client.requisicao_post(
            headers=headers_api_telefonia(self.token),
            payload_post=payload_api_telefonia(self.data, nome_cliente),
            url=self.url._gerar_url_relatorio_chamadas(),
        )

    def get_relatorio_agente(self) -> requests.Response:
        return self.http_client.requisicao_post(
            headers=headers_api_telefonia(self.token),
            payload_post=self.data_agentes,
            url=self.url._gerar_url_relatorio_agentes(),
        )

    def execucao_ipbox(self, nome_cliente: str, id_cliente: str) -> dict:
        agressividade = self.get_agressividade(id_cliente)
        chamadas = self.get_relatorio_chamadas(nome_cliente)
        return {
            "Agressividade": agressividade.text,
            "Chamadas": chamadas.json(),
            "Operadores": agressividade.text,
        }
