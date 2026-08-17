from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.environments.operadoras.pentagono.payloads_pentagono import *
import random
from urllib.parse import urlencode
import requests

class NextBillingUrl:
    def __init__(self, url_base):
        self.url_base = url_base
        
    def url_login(self):
        return f'{self.url_base}/security/validate'
    
    def url_get_cdr(self):
        return f'{self.url_base}/relatorioAgrupadoLinhas/data'
    
    def url_pagina_inicial(self):
        return f'{self.url_base}/dashboard/customer/index'

class NextBillingScrap:
    
    def __init__(self, usuario, senha, data, url_base):
        self.usuario = usuario
        self.senha = senha
        self.data = data
        self.hr = HttpRequisitions(session=requests.Session())
        self.link = NextBillingUrl(url_base)
        

    def login(self):
        return self.hr.requisicao_post(payload_post=payload_login_pentagono(self.usuario, self.senha),
                                        headers=headers_pentagono(),
                                        url=self.link.url_login())


    def pagina_inicial(self):

        return self.hr.requisicao_get(headers=headers_pentagono(),
                                                payload_get={},
                                                url=self.link.url_pagina_inicial())

    def relatorio(self):
        return self.hr.requisicao_get(payload_get=payloads_relatorio(self.data),
                                               headers=headers_pentagono(),
                                               url=self.link.url_get_cdr()
                                               )

    def execucao_nextbiling(self):
        login = self.login()
        pagina_inicial = self.pagina_inicial()
        relatorio_html = self.relatorio()
        return login, pagina_inicial, relatorio_html
        
        