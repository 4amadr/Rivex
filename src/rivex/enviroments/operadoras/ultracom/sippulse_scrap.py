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
        return f"{self.url}/SipPulsePortal/pages/reports/usercall.jsf"

class SipPulseScrap:
    def __init__(self, url_base, usuario, senha, data):
        self.url_sistema = url_base
        self.usuario = usuario
        self.senha = senha
        self.data = data
        self.url = SipPulseUrl(self.url_sistema)
        self.http_request = HttpRequisitions(session=requests.Session())
        self.viewstate = None

    def get_login(self):
        return self.http_request.requisicao_get(
            payload_get={},
            headers=header_sippulse(),
            url=self.url.login_ultracom()
        )

    def login(self):

        resposta_login = self.get_login()
        self.get_viewstate(resposta_login.text)

        login = self.http_request.requisicao_post(
            payload_post=payload_login(self.usuario, self.senha, self.viewstate),
            headers=header_sippulse(),
            url=self.url.login_ultracom()
        )

        self.get_viewstate(login.text)

        return login

    def pagina_inicial(self):
        return self.http_request.requisicao_get(
            payload_get={},#payload_pagina_inicial(self.viewstate),
            headers=header_sippulse(),
            url=self.url.pagina_inicial()
        )

    def chamadads_tarifadas(self):
        return self.http_request.requisicao_post(
            payload_post=payload_chamadas_tarifadas(self.data, self.viewstate),
            headers=header_sippulse(),
            url=self.url.chamadas_tarifadas()
        )

    def dados_monetarios(self):
        return self.http_request.requisicao_post(
            payload_post=payload_dados_monetarios(self.data, self.viewstate),
            headers=header_sippulse(),
            url=self.url.relatorio_monetario()
        )

    def get_viewstate(self, html):
        self.viewstate = extrair_viewstate(html)
        return self.viewstate

    def execucao_ultracom(self):
        login = self.login()


        pagina_inicial = self.pagina_inicial()

        print("HOME STATUS:", pagina_inicial.status_code)
        print("HOME URL:", pagina_inicial.url)
        print("VIEWSTATE HOME:", self.viewstate)
        self.get_viewstate(pagina_inicial.text)

        chamadas = self.chamadads_tarifadas()
        self.get_viewstate(chamadas.text)

        monetarios = self.dados_monetarios()
        self.get_viewstate(monetarios.text)
        