import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import (
    headers_callix,
    payload_resumo_campanha,
)


class CallixAPICollector:
    def __init__(self, data: str):
        self.data = data
        self.session = requests.Session()
        self.hr = HttpRequisitions(session=self.session)

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
        resumo_campanha = self.resumo_campanha(cliente, token)

        return {
            "resumo": resumo_campanha.json(),
            "campanha": campanhas,
        }
