import requests
from bs4 import BeautifulSoup

class ClientSimulator:
    def __init__(self, session):
        self.session = session

    def gerar_headers(self, url):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def gerar_token(self, html):
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("input", {"name": "authenticity_token"})["value"]

    def gerar_pagina_html(self, url):
        response = self.session.get(url)
        return response.text

    def gerador_de_requisitos(self, url):
        headers = self.gerar_headers(url)
        pagina = self.gerar_pagina_html(url)
        token = self.gerar_token(pagina)

        return headers, pagina, token