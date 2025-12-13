import requests
import os
import dotenv
from dotenv import load_dotenv
from datetime import date, timedelta

class IPBoxAPI:
    
    def __init__(self, token, url):
        self.token=token
        self.url=url
        
    def colect_data(token, url):
        '''Função para coletar os dados em .JSON'''
        
        headers = {
            'Authorization': token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload,)
        dados = response.json()
        if response.status_code == 200:
            try:
                dados_ipbox = response.json()['data']
                print(dados_ipbox[:2])
                print('Dados coletados do IPBox!')
                
            except Exception as erro_coleta_de_dados_ipbox:
                print('Erro durante a coleta de dados do IPBox')
                
            finally:
                print('Coleta do ipbox finalizada')
                
        else:
            print(f'ERRO: {response.status_code} requisição do IPBox invalida')
            
if __init__ == '__name__':
    ipbox = IPBoxAPI(
        token=os.getenv('token_ipbox'),
        url=os.getenv('url_ipbox_pa1')
    )