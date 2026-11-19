import urllib.parse
import requests

from src.rivex.environments.discadores.Callix.get_url_callix import UrlGetData
from src.rivex.environments.discadores.Callix.payloads_callix import (
    headers_callix,
    headers_v4_sessao,
    payload_campanhas_v4,
    payload_de_requisicao_de_chamadas,
    payload_get_tech,
    payload_rotas_chamadas_v4,
)
from src.rivex.utils.requests_utils.requests import HttpRequisitions


class CAllixRequisition:
    """Coleta métricas complementares do Callix via Server SDK e endpoints v4."""

    def __init__(
        self,
        data: str,
        retry_429_wait: float = 60.0,
        retry_429_max: int = 5,
    ):
        self.data = data
        self.session = requests.Session()
        self.http_request = HttpRequisitions(
            session=self.session,
            servico="callix",
            retry_429_wait=retry_429_wait,
            retry_429_max=retry_429_max,
        )
        self.url = UrlGetData()

    def conversor_de_url(self, url_chamadas_agentes: str) -> str:
        params = payload_de_requisicao_de_chamadas(self.data)
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"{url_chamadas_agentes}?{query_string}"

    def localizar_usuario_ativo(self, cliente: str, token_api: str) -> str:
        """
        Localiza um usuário ativo e autorizado no ambiente Callix.

        Prioridade:
        1. Usuário admin.
        2. Usuário com e-mail da Contech.
        3. Primeiro usuário elegível.
        """
        response = self.http_request.requisicao_get(
            headers=headers_callix(token_api),
            url=self.url.url_users_v1(cliente),
            payload_get={"page[limit]": 2000},
        )

        usuarios = response.json().get("data", [])

        usuarios_elegiveis = [
            usuario
            for usuario in usuarios
            if usuario.get("attributes", {}).get("blocked") is not True
            and usuario.get("attributes", {}).get("active") is not False
        ]

        if not usuarios_elegiveis:
            raise ValueError(f"Nenhum usuário elegível encontrado em {cliente}")

        def _obter_login(usuario: dict) -> str:
            attributes = usuario.get("attributes", {})
            return attributes.get("login") or attributes.get("username") or ""

        def prioridade(usuario: dict) -> int:
            attributes = usuario.get("attributes", {})
            login = _obter_login(usuario).lower()
            email = (attributes.get("email") or "").lower()

            if login == "admin":
                return 0
            if "contech" in email:
                return 1
            return 2

        usuarios_elegiveis.sort(key=prioridade)
        return _obter_login(usuarios_elegiveis[0])

    def criar_sessao_usuario(self, cliente: str, token_api: str) -> str:
        usuario = self.localizar_usuario_ativo(
            cliente=cliente,
            token_api=token_api,
        )

        response = self.http_request.requisicao_post_json(
            payload_post={"username": usuario},
            headers=headers_callix(token_api),
            url=self.url.url_sdk_user_session(cliente),
        )

        dados = response.json()
        user_session_token = dados.get("userSessionToken")

        if not user_session_token:
            raise ValueError(
                f"Server SDK não retornou userSessionToken em {cliente} "
                f"(status={response.status_code}, resposta={dados})"
            )

        return user_session_token

    def encerrar_sessao_usuario(self, cliente: str, user_session_token: str):
        return self.http_request.requisicao_delete(
            headers=headers_v4_sessao(user_session_token),
            url=self.url.url_logout_v4(cliente),
        )

    def requisicao_get_sessao(
        self,
        user_session_token: str,
        url: str,
        payload_get: dict | None = None,
    ):
        return self.http_request.requisicao_get(
            headers=headers_v4_sessao(user_session_token),
            url=url,
            payload_get=payload_get or {},
        )

    def _paginar_get_sessao(
        self,
        user_session_token: str,
        url_inicial: str,
        max_paginas: int = 20,
    ) -> dict:
        """Agrega registros paginados via links.next da API v4."""
        pagina = self.requisicao_get_sessao(user_session_token, url_inicial).json()
        dados = list(pagina.get("data", []))
        incluidos = list(pagina.get("included", []))

        proxima_url = (pagina.get("links") or {}).get("next")
        paginas = 1
        while proxima_url and paginas < max_paginas:
            pagina = self.requisicao_get_sessao(user_session_token, proxima_url).json()
            dados.extend(pagina.get("data", []))
            incluidos.extend(pagina.get("included", []))
            proxima_url = (pagina.get("links") or {}).get("next")
            paginas += 1

        resultado = {"data": dados}
        if incluidos:
            resultado["included"] = incluidos
        return resultado

    def requisicao_callix(self, cliente: str, token: str) -> dict:
        user_session_token = self.criar_sessao_usuario(cliente, token)

        data_iso = (
            self.data
            if "T" in str(self.data)
            else f"{self.data}T00:00:00.000Z"
        )

        try:
            return {
                "accounts": self.requisicao_get_sessao(
                    user_session_token,
                    self.url.url_accounts(cliente),
                ).json(),
                "campanhas": self.requisicao_get_sessao(
                    user_session_token,
                    self.url.url_campanhas_v4(cliente),
                    payload_campanhas_v4(),
                ).json(),
                "outbound_routes": self.requisicao_get_sessao(
                    user_session_token,
                    self.url.url_outbound_routes(cliente),
                    payload_get_tech(),
                ).json(),
                "chamadas_completas": self.requisicao_get_sessao(
                    user_session_token,
                    self.url.url_chamadas_completas_v4(cliente),
                    payload_rotas_chamadas_v4(data_iso),
                ).json(),
                "user_performance_histories": self._paginar_get_sessao(
                    user_session_token,
                    self.conversor_de_url(
                        self.url.url_user_performance_histories(cliente)
                    ),
                ),
            }
        finally:
            try:
                self.encerrar_sessao_usuario(cliente, user_session_token)
            except Exception as erro:
                self.http_request.extract_logger.log_conf.log_warning(
                    f"Falha ao encerrar sessão Callix em {cliente}: {erro}"
                )
