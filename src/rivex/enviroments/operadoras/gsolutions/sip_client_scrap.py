import requests
from bs4 import BeautifulSoup
import os
from dateutil.utils import today
from dotenv import load_dotenv
from datetime import timedelta, datetime, date

load_dotenv()
class SipClient:
    def __init__(self, usuario, password, url, operadora):
        self.usuario = usuario
        self.password = password
        self.url = url

    def login(self, url, usuario, password, operadora):
        url = f'{self.url}/painel/index.php'
        print(f'login: {operadora}')
        req = requests.Session()


        credenciais = {
            'login': self.usuario,
            'senha': self.password,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }

        response = req.post(url, headers=headers, data=credenciais, verify=False)

        if response.status_code == 200:
            print(f'Logado em: {operadora}')
            return req
        else:
            raise RuntimeError(f'Erro: {response.status_code} ao logar')

    def filtrar_dados(self, data_selecionada, operadora, url):
        url = f'{self.url}/painel/relatorio_minutos_revenda.php'
        login_feito = self.login(url, self.usuario, self.password, operadora)

        filtragem = {
            'filtro': 1, # seleção personalizada
            'periodopre': 0,
            'data_inicio': data_selecionada, # formato AAAA-MM-DD
            'horario_inicio': 00,
            'data_fim': data_selecionada, # formato AAAA-MM-DD
            'horario_fim': 23,
            'cliente_filtro': '',
            'tipochamadas': 'todas',
            'action': 'Filtrar'
        }
        requests = login_feito.post(url, headers=login_feito.headers, data=filtragem, verify=False)
        
        if requests.status_code == 200:
            print(f'filtro aplicado para: {operadora}')
            return requests
        else:
            raise RuntimeError(f'Erro: {requests.status_code} ao filtrar')

    def soup_data(self, data_selecionada, operadora):
        '''function to get soup data from url'''
        requisicao = self.filtrar_dados(data_selecionada, operadora, self.url).text
        soup = BeautifulSoup(requisicao, 'html.parser')
        if soup:
            print(f'Sopa coletada: {operadora}')
            return soup
        else:
            print(f'Sem sopa em {operadora}!')
            return False

    def execucao_pipeline_sip(self, url, usuario, password, operadora, data):
        login_sip = self.login(url, usuario, password, operadora)
        filtro_aplicado = self.filtrar_dados(data, operadora, url)
        sopa = self.soup_data(data, operadora)
        return sopa
        
    

class CallsSipClient:
    def road_calls(self):
        '''function to get road calls from url'''
        client = SipClient()
        login = client.login()

        #now the road to the calls


