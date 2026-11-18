import logging
import urllib.parse
import requests

from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.get_url_callix import UrlGetData
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import (
    headers_callix,
    headers_v4_sessao,
    payload_audit_campanhas,
    payload_campanhas_v4,
    payload_de_requisicao_de_chamadas,
    payload_get_tech,
    payload_rotas_chamadas_v4,
)

log = logging.getLogger(__name__)


class CAllixRequisition:
    """Coleta métricas complementares do Callix via Server SDK e endpoints v4."""

    def __init__(self, data: str):
        self.data = data
        self.session = requests.Session()
        self.http_request = HttpRequisitions(session=self.session)
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
            payload_get=payload_get,
        )

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
                "audit_logs": self.requisicao_get_sessao(
                    user_session_token,
                    self.url.url_audit_logs(cliente),
                    payload_audit_campanhas(),
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
                "user_performance_histories": self.requisicao_get_sessao(
                    user_session_token,
                    self.conversor_de_url(
                        self.url.url_user_performance_histories(cliente)
                    ),
                ).json(),
            }
        finally:
            try:
                self.encerrar_sessao_usuario(cliente, user_session_token)
            except Exception as erro:
                log.warning(
                    "Falha ao encerrar sessão Callix em %s: %s",
                    cliente,
                    erro,
                )
