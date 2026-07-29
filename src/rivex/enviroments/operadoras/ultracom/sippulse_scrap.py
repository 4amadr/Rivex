import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.operadoras.ultracom.payloads_ultracom import *
from src.rivex.data_processing.ultracom.get_viewstate import *

class SipPulseUrl:
    def __init__(self, url_base):
        self.url = url_base
        pass

    def login_ultracom(self):
        return f"{self.url}/SipPulsePortal/pages/login/login.jsf"

    def pagina_inicial(self):
        return f"{self.url}/SipPulsePortal/pages/home/home.jsf"

    def chamadas_tarifadas(self):
        return f"{self.url}/SipPulsePortal/pages/reports/asrsubscriber.jsf"

    def relatorio_monetario(self):
        return f"{self.url}/SipPulsePortal/pages/reports/usercalldid0800.jsf"

class SipPulseScrap:
    def __init__(self, url_base, usuario, senha, data):
        self.url_sistema = url_base
        self.usuario = usuario
        self.senha = senha
        self.data = data
        self.url = SipPulseUrl(self.url_sistema)
        self.http_request = HttpRequisitions(session=requests.Session())

    def get_login(self):
        return self.http_request.requisicao_get(
            payload_get={},
            headers=header_sippulse(),
            url=self.url.login_ultracom()
        )

    def login(self, viewstate):
        print("Logando...")
        print("URL: ",self.url.login_ultracom())
        print("HEADER: ",header_sippulse())
        print("PAYLOAD: ", payload_login(self.usuario, self.senha, viewstate))
        login = self.http_request.requisicao_post(
            payload_post=payload_login(self.usuario, self.senha, viewstate),
            headers=header_sippulse(),
            url=self.url.login_ultracom()
        )
        print(login.status_code)
        print(login)
        print(login.text)
        return login

    def pagina_inicial(self):
        return self.http_request.requisicao_get(
            payload_get=payload_pagina_inicial(),
            headers=header_sippulse(),
            url=self.url.pagina_inicial()
        )

    def chamadads_tarifadas(self):
        return self.http_request.requisicao_get(
            payload_get=payload_chamadas_tarifadas(self.data),
            headers=header_sippulse(),
            url=self.url.chamadas_tarifadas()
        )

    def dados_monetarios(self):
        return self.http_request.requisicao_get(
            payload_get=payload_dados_monetarios(self.data),
            headers=header_sippulse(),
            url=self.url.relatorio_monetario()
        )

    def get_viewstate(self):
        login_get = self.get_login()
        return extrair_viewstate(login_get.text)

    def execucao_ultracom(self):
        login = self.login(self.get_viewstate())
        print(login)
        print(login.status_code)
        print(login.text)
        print(login.headers)
        