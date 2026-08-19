import time
import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.utils.environments_utils.discador.callix.payloads_callix import *
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

log = logging.getLogger(__name__)

class CallixAPICollector:
    def __init__(self, cliente, token, data):
        self.cliente = cliente
        self.token = token
        self.data = data
        self.session = requests.Session()
        self.hr = HttpRequisitions(session=self.session)
        
    def url_tratada(self, endpoint):
        url = f'https://{self.cliente}.callix.com.br/api/v1/{endpoint}'
        return url
    
    def campanha(self):
        log.info('coletando a campanha')
        campanha = self.hr.requisicao_get(url=self.url_tratada('campaigns'),
                                          payload_get={},
                                          headers=headers_callix(self.token))
        return campanha

    def resumo_campanha(self, campanha):
        log.info("Coletando resumo das campanhas")
        resumo_campanha = self.hr.requisicao_get(url=self.url_tratada('campaign_call_summaries'),
                                                 headers=headers_callix(self.token),
                                                 payload_get=payload_resumo_campanha(self.data))
        return resumo_campanha
            
    def api_callix(self):
        campanha_json = self.campanha().json()
        campanhas = [campanha['id'] for campanha in campanha_json['data']]
        resumo_campanha = self.resumo_campanha(campanhas)
        
        return {
            "resumo": resumo_campanha.json(),
            "campanha": campanhas
        }
        
        
        
        
    
    

    