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
    ipbox.coletar_relatorios_de_chamadas(token, dia_ontem, mes, ano)