import requests
from src.rivex.utils.requests_utils.http_response import *

class HttpRequisitions:
    def __init__(self, session):
        self.session = session


    def requisicao_post_com_certificado(self, payload_post: dict, headers: dict, url, verificacao: bool):
        '''
        Função de post com verify ativado para evitar bloqueios por falta de SSL
        '''
        postagem = self.session.post(url, data=payload_post, headers=headers, verify=verificacao)
        analista_de_erros(postagem.status_code)
        return postagem

    def requisicao_get_com_verificado(self, headers: dict, url: str,  payload_get: dict, verificacao: bool, cookies_requisicao: str | None = None):
        if cookies_requisicao:
            coleta = self.session.get(url, params=payload_get, headers=headers, cookies=cookies_requisicao, verify=verificacao)
            # verificação se há erros nos status_code
            analista_de_erros(coleta.status_code)
            return coleta
        else:
            coleta = self.session.get(url, params=payload_get, headers=headers, verify=verificacao)
            # verificação se há erros nos status_code
            print(coleta.status_code)
            analista_de_erros(coleta.status_code)
            return coleta

    def requisicao_post(self, payload_post: dict, headers: dict, url):
        postagem = self.session.post(url, data=payload_post, headers=headers)
        analista_de_erros(postagem.status_code)
        return postagem
    
    def requisicao_post_json(self, payload_post: dict, headers: dict, url):
        postagem = self.session.post(url, json=payload_post, headers=headers)
        analista_de_erros(postagem.status_code)
        return postagem
    
    def requisicao_get(self, headers: dict, url: str,  payload_get: dict, cookies_requisicao: str | None = None):
        if cookies_requisicao:
            coleta = self.session.get(url, params=payload_get, headers=headers, cookies=cookies_requisicao)
            # verificação se há erros nos status_code
            analista_de_erros(coleta.status_code)
            return coleta
        else:
            coleta = self.session.get(url, params=payload_get, headers=headers,)
            # verificação se há erros nos status_code
            print(coleta.status_code)
            analista_de_erros(coleta.status_code)
            return coleta