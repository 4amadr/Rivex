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
    
    def coletar(self, endpoint, data=None, filtro_ativar=None, filtro_setar=None, ativador_payload: bool=True):
        '''Vai ser usado para coletar todos os tipos de chamadas'''
        payload_config = payload_callix(endpoint, data, filtro_ativar, filtro_setar)
        
        # verificador para automatizar campanhas sem data
        if not ativador_payload:
            payload_config = None
            
        dados_chamadas = self.hr.requisicao_get(
            headers=headers_callix(self.token),
            url=self.url_tratada(endpoint),
            payload_get=payload_config
        )
        return dados_chamadas

    def coletar_todos(self, endpoint, data=None, limite=5000):
        primeira_resposta = self.coletar(endpoint, data).json()
        total = primeira_resposta.get("meta", {}).get("count", 0)
        registros = primeira_resposta.get("data", [])

        log.info(f"[{endpoint}] Total disponível: {total} | Primeira página: {len(registros)}")

        if total <= limite:
            return registros

        offsets = range(limite, total, limite)

        def buscar_pagina(offset):
            time.sleep(0.5)
            payload = {
                "filter[started_at]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z",
                "page[limit]": limite,
                "page[offset]": offset
            }
            resposta = self.hr.requisicao_get(
                headers=headers_callix(self.token),
                url=self.url_tratada(endpoint),
                payload_get=payload
            ).json()
            pagina = resposta.get("data", [])
            log.info(f"[{endpoint}] offset={offset} | registros={len(pagina)}")
            return pagina

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(buscar_pagina, offset): offset for offset in offsets}
            for future in as_completed(futures):
                registros.extend(future.result())

        log.info(f"[{endpoint}] Coleta finalizada: {len(registros)} de {total}")
        return registros
    
    def chamadas_completas(self):
        log.info('coletando chamadas completas')
        return self.coletar('campaign_completed_calls', self.data)
    
    def chamadas_recusadas(self):
        log.info('coletando chamadas recusadas')
        return self.coletar_todos('campaign_missed_calls', self.data)

    
    def chamadas_abandonadas(self):
        log.info('coletando chamadas abandonadas')
        return self.coletar('campaign_missed_calls', self.data, filtro_ativar="filter[failure_cause]", filtro_setar="9")
    
    def campanha(self):
        log.info('coletando a campanha')
        campanha = self.coletar('campaigns', ativador_payload=False)
        return campanha
        
    def api_callix(self):
        
        # chamadas
        chamadas_completas = self.chamadas_completas()
        chamadas_recusadas = self.chamadas_recusadas()
        campanha_json = self.campanha().json()
        campanhas = [campanha['id'] for campanha in campanha_json['data']]
        
        return {
            "Completas": chamadas_completas.json(),
            "Recusadas": chamadas_recusadas,
            "Campanha": campanhas
        }
        
        
        
        
    
    

    