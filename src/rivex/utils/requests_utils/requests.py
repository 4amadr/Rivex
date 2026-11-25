from __future__ import annotations

import requests
from src.rivex.domain.exceptions import ErroHttpDiscador
from src.rivex.utils.logging_config import ExtractLogger



class HttpRequisitions:
    def __init__(self, session, servico):
        self.servico = servico
        self.erro_http = ErroHttpDiscador()
        self.session = session

    def requisicao(self, url, headers, get: bool, payload: None):

        if get is True:
            req = self.session.get(url=url, headers=headers, params=payload, timeout=20)
        else: 
            req = self.session.post(url=url, headers=headers, params=payload, timeout=20)

        if req.status_code == 200:
            return req
        else:
            self.erro_http.analisar_erros(req.status_code, url)

    def req_get(self, url, headers, payload):
        return self.requisicao(url, headers, True, payload)

    def req_post(self, url, headers, payload):
        return self.requisicao(url, headers, False, payload)

