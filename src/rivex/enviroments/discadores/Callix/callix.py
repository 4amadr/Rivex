import time
import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.Callix.payloads_callix import headers_callix, payload_callix


class CallixAPICollector:
    _BASE_URL = "https://{cliente}/api/v1/{endpoint}"

    def __init__(self, cliente: str, token: str, data: str):
        self.cliente = cliente
        self.token = token
        self.data = data
        self._session = requests.Session()
        self._hr = HttpRequisitions(self._session)

    def _get(self, cliente, token, requisicao, data=None, filtro=None):
        print(f'Coletando {requisicao}')
        dados = self._hr.requisicao_get(
            url= self._BASE_URL.format(cliente=cliente, endpoint=requisicao),
            payload_get=payload_callix(requisicao, data, filtro),
            headers=headers_callix(token)
        )
        return dados
    
    def chamadas_completas(self, cliente, token, data):
        return self._get(cliente, token, 'campaign_completed_calls', data)
    
    def chamadas_recusadas(self, cliente, token, data):
        return self._get(cliente, token, 'campaign_missed_calls', data)
    
    def perfomace_dos_agentes(self, cliente, token, data):
        return self._get(cliente, token, 'user_perfomace_report', data)
    
    def chamadas_abandonadas(self, cliente, token, data):
        return self._get(cliente, token, 'campaign_missed_calls', data, filtro={"filter[failure_cause]": "9"})
    
    def coletar_tudo(self, cliente, token, data):
        return {
            'Completas': self.chamadas_completas(cliente, token, data),
            'Recusadas': self.chamadas_recusadas(cliente, token, data),
            'Abandonadas': self.chamadas_abandonadas(cliente, token, data),
            'Performace de agentes': self.perfomace_dos_agentes(cliente, token, data)
        }
        
        
        