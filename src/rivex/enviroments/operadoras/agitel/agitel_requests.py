import requests
from src.rivex.utils.requests_utils.http_response import HttpResponse


class AgitelSip:
    def __init__(self, usuario, senha):
        self.usuario = usuario
        self.senha = senha
        self.hr = HttpResponse(session=requests.Session())
        self.url_base = 'https://35.247.218.95/painel/'

    def gerador_de_url(self):


    def login_agitel(self):