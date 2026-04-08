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
    
    def coletar(self, endpoint, data=None, filtro_ativar=None, filtro_setar=None, ativador_payload: bool=True):
        '''Vai ser usado para coletar todos os tipos de chamadas'''
        payload_config = payload_callix(endpoint, data, filtro_ativar, filtro_setar)
        
        # verificador para automatizar campanhas sem data
        if ativador_payload == False:
            payload_config = None
            
        dados_chamadas = self.hr.requisicao_get(
            headers_callix(self.token),
            self.url_tratada(endpoint),
            payload_config
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
        return self.coletar('campaign_missed_calls', self.data, filtro_ativar="filter[failure_cause]", filtro_setar="9")
    
    def campanha(self):
        print('coletando a campanha')
        return self.coletar('campaigns', ativador_payload=False)
        
    def api_callix(self):
        # chamadas
        chamadas_completas = self.chamadas_completas()
        chamadas_recusadas = self.chamadas_recusadas()
        print("Iniciando timer de 60s para evitar bloqueios do servidor")
        time.sleep(60)
        chamadas_abandonadas = self.chamadas_abandonadas()
        
        # desempenho
        desempenho = self.desempenho()
        
        # campanha (agressividade)
        campanha = self.campanha()
        print("Sequencia de status code das requisições:")
        print("chamadas completas: ", chamadas_completas.status_code)
        print("chamadas recusadas: ", chamadas_recusadas.status_code)
        print("chamadas abandonadas: ", chamadas_abandonadas.status_code)
        print("chamadas desempenho: ", desempenho.status_code)
        print("chamadas campanha: ", campanha.status_code)
        
        
        
        return {
            "Completas": chamadas_completas.json(),
            "Recusadas": chamadas_recusadas.json(),
            "Abandonadas": chamadas_abandonadas.json(),
            "Campanha": campanha.json()
        }
        
        
        
        
    
    

    