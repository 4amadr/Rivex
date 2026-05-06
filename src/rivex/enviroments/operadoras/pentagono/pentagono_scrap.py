from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.operadoras.pentagono.payloads_pentagono import *
import random
from urllib.parse import urlencode
import requests
import dotenv
import os

class pentagonoScrap:
    
    def __init__(self, usuario, senha, data):
        self.usuario = usuario
        self.senha = senha
        self.data = data
        self.hr = HttpRequisitions(session=requests.Session())
        
    def gerador_url(self):
        url_login_pentagono = 'https://sip8.pentagonotelecom.com.br/security/validate'
        url_cdr = 'https://sip8.pentagonotelecom.com.br/relatorioAgrupadoLinhas/data'
        url_pagina_inicial = 'https://sip8.pentagonotelecom.com.br/inicial/'
        return url_login_pentagono, url_cdr, url_pagina_inicial

    def login_pentagono(self, url_login_pentagono):
        
        login = self.hr.requisicao_post(payload_post=payload_login_pentagono(self.usuario, self.senha),
                                        headers=headers_pentagono(),
                                        url=url_login_pentagono)
        print("=== LOGIN ===")
        print(f"Status:   {login.status_code}")
        print(f"URL final (após redirects): {login.url}")
        print(f"Cookies na sessão: {dict(self.hr.session.cookies)}")
        print(f"Resposta (primeiros 300 chars): {login.text[:300]}")
        return login

    def get_pagina_inicial(self, url_pagina_inicial):
        '''Estabelece a conexão na pag inicial para poder prosseguir com a coleta de dados'''

        url = f"{url_pagina_inicial}?{random.random()}"
        pagina_inicial = self.hr.requisicao_get(headers=headers_pentagono(),
                                                payload_get={},
                                                url=url)
        return pagina_inicial

    def get_cdr(self, url_cdr):
        cache_buster = random.random()
        query_string = f"{cache_buster}&{urlencode(payloads_relatorio(self.data))}"
        url = f"{url_cdr}?{query_string}"

        relatorio_cdr = self.hr.requisicao_get(payload_get={},
                                               headers=headers_pentagono(),
                                               url=url
                                               )
        return relatorio_cdr
    def execucao_pentagono(self):
        url_login, url_cdr, url_pagina_inicial = self.gerador_url()
        login = self.login_pentagono(url_login)
        pagina_inicial = self.get_pagina_inicial(url_pagina_inicial)
        relatorio_html = self.get_cdr(url_cdr)

        return login, pagina_inicial, relatorio_html
        
        