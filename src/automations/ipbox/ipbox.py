import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

class IPBoxAPI:
    def __init__(self, token, url):
        self.token = token
        self.url = url

    def coletar_dados_de_agentes(self, token, dia, mes, ano):
        '''Função para a coleta de dados de agentes e desempenho do IPBox
        a função coleta todos os agentes e as suas informações de ligação no determinado dia'''

        url = 'https://contech1.ipboxcloud.com.br:8624/ipbox/api/getPA1'

        payload = f'de={ano}{mes:02d}{dia:02d}000000&ate={ano}{mes:02d}{dia:02d}235959'

        headers = {
            'Authorization': f'{token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            try:
                json_agentes = response.json()["data"]
                return json_agentes
            except Exception as erro_req:
                print(f'ERRO: {erro_req} Ao coletar dados do IPBOX')

    def coletar_relatorios_de_chamadas(self, token, dia, mes, ano):
        payload = f'de={ano}{mes:02d}{dia:02d}000000&ate={ano}{mes:02d}{dia:02d}235959&operacao=Opera%C3%A7%C3%A3o%201'
        #payload = 'de=20210501000000&ate=20211231235959&operacao=Opera%C3%A7%C3%A3o%201'

        url = 'https://contech1.ipboxcloud.com.br:8624/ipbox/api/getTA1'

        headers = {
            'Authorization': f'{token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            try:
                json_chamadas = response.json()["data"]
                print(json_chamadas)
                return json_chamadas
            except Exception as erro_req:
                print(f'ERRO: {erro_req} Ao coletar dados do IPBOX')
        else:
            print('Requisição foi atropelada', response.status_code)
            print('Detalhes: ', response.text)
            return False


if __name__ == '__main__':
    ipbox = IPBoxAPI(
        token=os.getenv('token_ipbox'),
        url=os.getenv('url_ipbox_pa1')
    )
    dia_hoje = int(datetime.today().day)
    dia_ontem = dia_hoje - 1
    mes = int(datetime.today().month)
    ano = int(datetime.today().year)
    url = os.getenv('url_ipbox')
    token = os.getenv('token_ipbox')
    #ipbox.coletar_dados_de_agentes(token, dia_ontem, mes, ano)
    ipbox.coletar_relatorios_de_chamadas(token, dia_ontem, mes, ano)