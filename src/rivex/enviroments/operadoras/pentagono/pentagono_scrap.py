from random import random
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.operadoras.pentagono.payloads_pentagono import *
import random
from urllib.parse import urlencode
import requests
import dotenv
import os

class PentagonoURL:
    def __init__(self):
        self.url_base = 'https://sip8.pentagonotelecom.com.br/'
        
    def url_login(self):
        return f'{self.url_base}security/validate'
    
    def url_get_cdr(self):
        return f'{self.url_base}/relatorioAgrupadoLinhas/data'
    
    def url_pagina_inicial(self):
        return f'{self.url_base}inicial/'

class pentagonoScrap:
    
    def __init__(self, usuario, senha, data):
        self.usuario = usuario
        self.senha = senha
        self.data = data
        self.hr = HttpRequisitions(session=requests.Session())
        self.link = PentagonoURL()
        

    def login_pentagono(self):
        return self.hr.requisicao_post(payload_post=payload_login_pentagono(self.usuario, self.senha),
                                        headers=headers_pentagono(),
                                        url=self.link.url_login())


    def get_pagina_inicial(self, ):

        '''Estabelece a conexão na pag inicial para poder prosseguir com a coleta de dados'''
        url=str(f"{self.link.url_pagina_inicial()}?{random.random()}")

        pagina_inicial = self.hr.requisicao_get(headers=headers_pentagono(),
                                                payload_get={},
                                                url=f"{url}")
        return pagina_inicial

    def get_cdr(self):
        cache_buster = random.random()
        query_string = f"{cache_buster}&{urlencode(payloads_relatorio(self.data))}"
        url = f"{self.link.url_get_cdr()}?{query_string}"

        relatorio_cdr = self.hr.requisicao_get(payload_get={},
                                               headers=headers_pentagono(),
                                               url=url
                                               )
        return relatorio_cdr
    def execucao_pentagono(self):
        login = self.login_pentagono()
        pagina_inicial = self.get_pagina_inicial()
        relatorio_html = self.get_cdr()

        return login, pagina_inicial, relatorio_html
        
        