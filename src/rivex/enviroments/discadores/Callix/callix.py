import time
import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.Callix.payloads_callix import headers_callix, payload_callix

class CallixAPICollector:
    def __init__(self, cliente, token, data):
        self.cliente = cliente
        self.token = token
        self.data = data
        self.session = requests.Session()
        self.hr = HttpRequisitions(session=self.session)
        
    def url_tratada(self, endpoint):
        url = f'https://{self.cliente}/api/v1/{endpoint}'
        return url
    
    def coletar(self, endpoint, data=None, filtro=None):
        '''Vai ser usado para coletar todos os tipos de chamadas'''
        dados_chamadas = self.hr.requisicao_get(
            headers_callix(self.token),
            self.url_tratada(endpoint),
            payload_callix(endpoint, data, filtro)
        )
        return dados_chamadas
    
    def chamadas_completas(self):
        print('coletando chamadas completas')
        return self.coletar('campaign_completed_calls', self.data)
    
    def chamadas_recusadas(self):
        print('coletando chamadas recusadas')
        return self.coletar('campaign_missed_calls', self.data)
    
    def chamadas_abandonadas(self):
        print('coletando chamadas abandonadas')
        return self.coletar('campaign_completed_calls', self.data, filtro={"filter[failure_cause]": "9"})
    
    def desempenho(self):
        print('coletando o desempenho')
        return self.coletar('user_perfomace_report', self.data)
    
    def campanha(self):
        print('coletando a campanha')
        return self.coletar('campaign')
        
    def api_callix(self):
        # chamadas
        chamadas_completas = self.chamadas_completas()
        chamadas_recusadas = self.chamadas_recusadas()
        chamadas_abandonadas = self.chamadas_abandonadas()
        
        # desempenho
        desempenho = self.desempenho()
        
        # campanha (agressividade)
        campanha = self.campanha()
        print(chamadas_completas)
        
        return {
            "Completas": chamadas_completas.json(),
            "Recusadas": chamadas_recusadas.json(),
            "Abandonadas": chamadas_abandonadas.json(),
            "Desempenho": desempenho.json(),
            "Campanha": campanha.json()
        }
        
        
        
    
    

    