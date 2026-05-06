from src.rivex.utils.requests_utils.requests import HttpRequisitions
from dotenv import load_dotenv
import os

class IpboxApi:
    def __init__(self, url, token, site_base, data):
        self.url = url
        self.token = token
        self.senha = senha
        self.site_base = site_base
        self.hr = HttpRequisitions(session=requests.session())
        
    def gerador_de_requisicao(self):
        url_base = f"{self.site_base}"
        url_produtividade_agentes = f"{url_base}ipbox/api/getPA1"
        url_desempenho_telefonia = f"{url_base}ipbox/api/getTA1"
        url_chamadas_abandonadas = f"{url_base}ipbox/api/getHC1?de={self.data}000000&ate={self.data}"
        return url_produtividade_agentes, url_desempenho_telefonia, url_chamadas_abandonadas
    
    def requisicao_ipbox(self, url):
        dados = self.hr.requisicao_get(headers,
                                       url,
                                       payload) # precisa elaborar o payload antes de executar
        '''
        Talvez alguns dados de payload precisem entrar nos argumentos da
        função
        '''

        return dados
    
    def execucao_ipbox():
        url_produtividade_agentes, url_desempenho_telefonia, url_chamadas_abandonadas = self.gerador_de_requisicao()
        produtividade = self.requisicao_ipbox(url_produtividade_agentes)
        desempenho_telefonia = self.requisicao_ipbox(url_desempenho_telefonia)
        chamadas_abandonadas = self.requisicao_ipbox(url_chamadas_abandonadas)
        
        return produtividade, desempenho_telefonia, chamadas_abandonadas # dados retornados em formato .json