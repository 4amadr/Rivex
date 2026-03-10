from dbm.sqlite3 import error
from itertools import count
import requests
import json
import csv
import time
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.Callix.payloads_callix import PayloadsCallix

load_dotenv()

class CallixAPI:

    # Inicializa a classe com os valores passados como parâmetros
    def __init__(self):
        pass

    def requisicao_tratada(self, cliente, requisicao):
        '''recebe o link e trata para fazer as requisições'''
        link = f'https://{cliente}contech.callix.com.br/api/v1/{requisicao}'
        return link
    
            
    def login_callix(self, password, cliente):
        # iniciar o login no ambiente callix
        url = f'https://{cliente}contech.callix.com.br/api/v4/auth/session'
        hr = HttpRequisitions()
        hc = HeadersCallix()
        
        payload_login = {"username": login, "password": password}
        headers = rc.headers_callix(token)
        login = hr.requisicao_post(payload_login, headers)
        
        # token para ser utilizado durante a coleta da agressividade
        token = login.cookies.get("token")
        return token
    
    def get_agressividade(self, data, cliente, token):
        '''Função para Verificar a alteração de agressividade no callix'''
        
        print(f"Verrificando a agressividade do cliente: {cliente}")
        
        url = f'https://{cliente}contech.callix.com.br/audit-logs'
        
        
        params = {
            "sorting": "-createdAt",
            "createdAt": f"{data},{data}",
            "page[limit]": 100,
            "page[offset]": 0
        }
        
        cookies = {"token": token}
        
        agressividade = requests.get(url, params=params, cookies=cookies)
        if agressividade.status_code == 200:
            return agressividade.json()
        elif agressividade is None:
            print(f"A agressividade do cliente: {cliente} Não foi alterada!")
            return None
        else: 
            print('Erro ao coletar agressividade', agressividade.status_code)
            return False
        
        

    def dados_gerais(self,  cliente, requisicao, data, token, filtro: dict | None = None):
        '''função para coletar os dados de chamadas'''
        pc = PayloadsCallix()
        hr = HttpRequisitions()
        hc = HeadersCallix()
        print(f'Coletando {requisicao}')

        link = self.requisicao_tratada(cliente, requisicao)
        
        querystring = pc.payload_request(requisicao)
        headers = rc.headers_callix(token)
        
        response = hr.requisicao_get(querystring, headers)
        return response.json()

    def execucao_por_cliente(self, cliente, data, token):
        '''Função para coletar os dados por cliente'''
        try:
            time.sleep(10)
            print(f"Logando no cliente {cliente}")
            token_para_agressividade = self.login_callix(password, cliente)
            agressividade_json = self.get_agressividade(data, cliente, token_para_agressividade)
            recusadas_bruto = self.dados_gerais(cliente, 'campaign_missed_calls', data, token)
            completas_bruto = self.dados_gerais(cliente, 'campaign_completed_calls', data, token)
            print(f'Aguarde um momento, timer de requisição de 65 segundos para o pedido não ser metralhado pelo servidor kk')
            time.sleep(65)
            abandonadas_bruto = self.dados_gerais(cliente, 'campaign_missed_calls', data, token, filtro={"filter[failure_cause]": "9"})
            time.sleep(20)
            performace_bruta = self.dados_gerais(cliente, 'user_performance_reports', data, token)
            
            
            return {
                "Fila": "Callix",
                "completas": completas_bruto,
                "recusadas": recusadas_bruto,
                "abandonadas": abandonadas_bruto,
                "performace": performace_bruta,
                "Agressividade": agressividade_json
            }
        except Exception as e:
            raise RuntimeError(f'Erro: {e} na coleta de dados de {cliente}') from e
            return None
        


