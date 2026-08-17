import requests
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.environments.operadoras.ultracom.payloads_ultracom import *
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

    def get_login(self):
        return self.http_request.requisicao_get(
            payload_get={},
            headers=header_sippulse(),
            url=self.url.login_ultracom()
        )

    def post_login(self, viewstate):
        return self.http_request.requisicao_post(
            payload_post=payload_login(self.usuario, self.senha, viewstate),
            headers=header_sippulse(),
            url=self.url.login_ultracom()
        )
        
    def login(self):
        html_login = self.get_login()
        viewstate = extrair_viewstate(html_login.text)
        return self.post_login(viewstate)


    def get_home(self):
        return self.http_request.requisicao_get(
            payload_get={},
            headers=header_sippulse(),
            url=self.url.pagina_inicial()
        )
        
    def post_home(self):
        return self.http_request.requisicao_post(
            payload_post={},
            headers=header_sippulse(),
            url=self.url.pagina_inicial()
        )
    
    def get_chamadas_tarifadas(self):
        return self.http_request.requisicao_get(
            payload_get={},
            headers=header_sippulse(),
            url=self.url.chamadas_tarifadas()   
        )
    
    def post_chamadas_tarifadas(self, viewstate):
        return self.http_request.requisicao_post(
            payload_post=payload_chamadas_tarifadas(self.data, viewstate),
            headers=header_sippulse(),
            url=self.url.chamadas_tarifadas()
        )
        
    def chamadas_tarifadas(self):
        get_tarifadas = self.get_chamadas_tarifadas()
        viewstate = extrair_viewstate(get_tarifadas.text)
        return self.post_chamadas_tarifadas(viewstate)
        
    def get_dados_monetarios(self):
        return self.http_request.requisicao_get(
            payload_get={},
            headers=header_sippulse(),
            url=self.url.relatorio_monetario()
        )
        
    def post_dados_monetarios(self, viewstate):
        return self.http_request.requisicao_post(
            payload_post=payload_dados_monetarios(self.data, viewstate),
            headers=header_sippulse(),
            url=self.url.relatorio_monetario()
        )
        
    def dados_monetarios(self):
        get_dados = self.get_dados_monetarios()
        viewstate = extrair_viewstate(get_dados.text)
        return self.post_dados_monetarios(viewstate)
    
    def execucao_sippulse(self):
        login = self.login()
        html_tarifadas = self.chamadas_tarifadas()
        dados_monetarios = self.dados_monetarios()
        return login, html_tarifadas.text, dados_monetarios.text
        
    
        