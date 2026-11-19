import requests

from src.rivex.environments.discadores.Callix.payloads_callix import (
    headers_callix,
    payload_resumo_campanha,
)
from src.rivex.utils.requests_utils.requests import HttpRequisitions


class CallixAPICollector:
    def __init__(
        self,
        data: str,
        retry_429_wait: float = 60.0,
        retry_429_max: int = 5,
    ):
        self.data = data
        self.session = requests.Session()
        self.hr = HttpRequisitions(
            session=self.session,
            servico="callix",
            retry_429_wait=retry_429_wait,
            retry_429_max=retry_429_max,
        )

    def url_tratada(self, cliente: str, endpoint: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v1/{endpoint}"

    def campanha(self, token: str, cliente: str):
        return self.hr.requisicao_get(
            url=self.url_tratada(cliente, "campaigns"),
            payload_get={},
            headers=headers_callix(token),
        )

    def resumo_campanha(self, cliente: str, token: str):
        return self.hr.requisicao_get(
            url=self.url_tratada(cliente, "campaign_call_summaries"),
            headers=headers_callix(token),
            payload_get=payload_resumo_campanha(self.data),
        )

    def api_callix(self, token: str, cliente: str) -> dict:
        resposta_campanha = self.campanha(token, cliente)
        campanha_json = resposta_campanha.json()
        if "data" not in campanha_json:
            raise RuntimeError(
                f"Resposta inesperada em campaigns para {cliente} "
                f"(status={resposta_campanha.status_code}): {campanha_json}"
            )
        campanhas = [campanha["id"] for campanha in campanha_json["data"]]

        resposta_resumo = self.resumo_campanha(cliente, token)
        resumo_json = resposta_resumo.json()
        if "data" not in resumo_json:
            raise RuntimeError(
                f"Resposta inesperada em campaign_call_summaries para {cliente} "
                f"(status={resposta_resumo.status_code}): {resumo_json}"
            )

        return {
            "resumo": resumo_json,
            "campanha": campanhas,
        }
