import requests
from src.rivex.utils.requests_utils.http_response import analista_de_erros
import logging
from src.rivex.utils.logging_config.request_log.logging_requests import *

log = logging.getLogger()

class HttpRequisitions:
    def __init__(self, session):
        self.session = session

    def _requisitar(self, metodo: str, url:str, headers: dict,
                    params: dict | None = None, data: dict | None = None,
                    json: dict | None = None, cookies: str | None = None,
                    verify: bool = True):

        req_log(url, headers, params)

        resposta = self.session.request(
            metodo, url,
            params=params, data=data, json=json,
            headers=headers, cookies=cookies, verify=verify
        )

        res_log(resposta)
        analista_de_erros(resposta.status_code)

        return resposta


    # ------------------------- POST -------------------------
 
    def requisicao_post_com_certificado(self, payload_post: dict, headers: dict, url: str, verificacao: bool):
        """
        POST com controle explícito de verify (usado quando é preciso
        contornar bloqueios por falta de certificado SSL válido).
        """
        return self._requisitar("POST", url, headers, data=payload_post, verify=verificacao)
 
    def requisicao_post(self, payload_post: dict, headers: dict, url: str):
        """POST padrão, com verify=True (comportamento default do requests)."""
        return self._requisitar("POST", url, headers, data=payload_post)
 
    def requisicao_post_json(self, payload_post: dict, headers: dict, url: str):
        """POST enviando o payload como JSON no corpo, em vez de form-data."""
        return self._requisitar("POST", url, headers, json=payload_post)
 
    # ------------------------- GET -------------------------
 
    def requisicao_get_com_verificado(self, headers: dict, url: str, payload_get: dict,
                                       verificacao: bool, cookies_requisicao: str | None = None):
        """GET com controle explícito de verify, com ou sem cookies."""
        return self._requisitar("GET", url, headers, params=payload_get,
                               cookies=cookies_requisicao, verify=verificacao)
 
    def requisicao_get(self, headers: dict, url: str, payload_get: dict,
                        cookies_requisicao: str | None = None):
        """GET padrão (verify=True), com ou sem cookies."""
        return self._requisitar("GET", url, headers, params=payload_get, cookies=cookies_requisicao)
 