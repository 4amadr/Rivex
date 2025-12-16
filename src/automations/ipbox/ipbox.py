import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

class IPBoxAPI:
    def __init__(self, token, url):
        self.token = token
        self.url = url

    def coleta_dados(self, url, token, dia, mes, ano):
        '''Função para a coleta de dados do IPBox'''

        payload = f'de={ano}{mes:02d}{dia:02d}000000ate={ano}{mes:02d}{dia:02d}235959'

        headers = {
            'Authorization': token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        print("STATUS:", response.status_code)
        print("HEADERS:", response.headers)
        print("BODY:", response.text)
        dados = response.headers.get('Content-Type')
        if response.status_code == 200:
            print('Dados coletados do IPBox!')
            return dados
        else:
            print(f'Erro ao coletar dados do IPBox: {response.status_code}')
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
    ipbox.coleta_dados(url, token, dia_ontem, mes, ano)