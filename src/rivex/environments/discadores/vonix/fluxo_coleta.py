from __future__ import annotations

import requests

from src.rivex.environments.discadores.vonix.payloads_vonix import (
    headers,
    payload_de_login,
)
from src.rivex.utils.beautiful_soup_utils.login_parser import get_token_login_vonix
from src.rivex.utils.requests_utils.requests import HttpRequisitions


class GerarUrlVonix:
    def __init__(self, url_base: str):
        self.url_base = (url_base or "").rstrip("/")

    def _url_login(self) -> str:
        return f"{self.url_base}/login/signin"

    def _url_get_filas(self) -> str:
        return f"{self.url_base}/admin/queues"

    def _url_get_agentes_ativos(self) -> str:
        return f"{self.url_base}/admin/agents"

    def _url_get_desempenho(self, equipe: str) -> str:
        return f"{self.url_base}/admin/queue_edit/{equipe}"

    def _url_get_chamadas(self) -> str:
        return f"{self.url_base}/overview/calls"


class ConfigVonix:
    def __init__(self, url_base: str, session: requests.Session | None = None):
        self.url_base = (url_base or "").rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update(headers())
        self.url = GerarUrlVonix(self.url_base)
        self.http_requisitions = HttpRequisitions(self.session, servico="vonix")
        self._autenticado = False

    def autenticar(self) -> None:
        resp_login = self.http_requisitions.req_get(
            url=self.url._url_login(),
            headers=headers(),
            payload={},
        )
        token = get_token_login_vonix(resp_login)
        self.http_requisitions.req_post(
            url=self.url._url_login(),
            headers=headers(),
            payload=payload_de_login(token=token),
        )
        self._autenticado = True

    def fluxo_fila(self) -> requests.Response:
        if not self._autenticado:
            self.autenticar()
        return self.http_requisitions.req_get(
            url=self.url._url_get_filas(),
            headers=headers(),
            payload={},
        )


class GetDadosVonix:
    def __init__(self, url_base: str, session: requests.Session | None = None):
        self.url_base = (url_base or "").rstrip("/")
        self.session = session or requests.Session()
        self.config_vonix = ConfigVonix(self.url_base, session=self.session)
        self.url = self.config_vonix.url
        self.http_requisitions = self.config_vonix.http_requisitions

    def _get_agentes_ativos(self) -> requests.Response:
        return self.http_requisitions.req_get(
            url=self.url._url_get_agentes_ativos(),
            headers=headers(),
            payload={},
        )

    def _get_desempenho(self, equipe: str) -> requests.Response:
        return self.http_requisitions.req_get(
            url=self.url._url_get_desempenho(equipe),
            headers=headers(),
            payload={},
        )

    def _get_chamadas(self) -> requests.Response:
        return self.http_requisitions.req_get(
            url=self.url._url_get_chamadas(),
            headers=headers(),
            payload={},
        )

    def get_dados(self, equipe: str) -> dict[str, requests.Response]:
        if not self.config_vonix._autenticado:
            self.config_vonix.autenticar()

        return {
            "agents": self._get_agentes_ativos(),
            "queue_edit": self._get_desempenho(equipe),
            "calls": self._get_chamadas(),
        }
