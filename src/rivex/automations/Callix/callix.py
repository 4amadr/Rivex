from dbm.sqlite3 import error
from itertools import count
import requests
import json
import csv
from datetime import datetime, timedelta, date
import time
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta, date

load_dotenv()

class CallixAPI:

    # Inicializa a classe com os valores passados como parâmetros
    def __init__(self):
        pass

    def requisicao_tratada(self, cliente, requisicao):
        '''recebe o link e trata para fazer as requisições'''
        link = f'https://{cliente}/api/v1/{requisicao}'
        return link

    def data_selecionadas(self):
        data_ref = date.today() - timedelta(days=1)
        data_formatada = data_ref.strftime("%Y-%m-%d")
        print('Dia selecionado para a coleta: ', data_formatada)
        return data_formatada

    def dados_gerais(self,  cliente, requisicao,data, token, filtro: dict | None = None):
        '''função para coletar os dados de chamadas'''
        print(f'Coletando {requisicao}')

        link = self.requisicao_tratada(cliente, requisicao)

        if requisicao == "user_performance_reports":
            querystring = {
                "filter[date]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z"
            }
        else:
            querystring = {
                "filter[started_at]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z",
            }
        if filtro:
            querystring.update(filtro)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        response = requests.request("GET", link, headers=headers, params=querystring)
        if response.status_code == 200:
            print(f'Coleta de chamadas do tipo: {requisicao} Finalizada')
            coleta_chamadas = response.json()
            return coleta_chamadas
        else:
            raise RuntimeError(f'Erro durante as chamadas do tipo: {requisicao} Resposta do servidor {response.status_code}')
            return False

    def execucao_por_cliente(self, cliente, data, token):
        '''Função para coletar os dados por cliente'''
        try:
            time.sleep(10)
            recusadas_bruto = self.dados_gerais(cliente, 'campaign_missed_calls', data, token)
            completas_bruto = self.dados_gerais(cliente, 'campaign_completed_calls', data, token)
            print(f'Aguarde um momento, timer de requisição de 65 segundos para o pedido não ser metralhado pelo servidor kk')
            time.sleep(65)
            abandonadas_bruto = self.dados_gerais(cliente, 'campaign_missed_calls', data, token, filtro={"filter[failure_cause]": "9"})
            time.sleep(20)
            performace_bruta = self.dados_gerais(cliente, 'user_performance_reports', data, token)
            return {
                "completas": completas_bruto,
                "recusadas": recusadas_bruto,
                "abandonadas": abandonadas_bruto,
                "performance": performace_bruta,
            }
        except Exception as e:
            raise RuntimeError(f'Erro: {e} na coleta de dados de {cliente}') from e
            return None


