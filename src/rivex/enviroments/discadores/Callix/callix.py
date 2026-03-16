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
from src.rivex.enviroments.discadores.Callix.payloads_callix import *

load_dotenv()

class CallixAPI:

    # Inicializa a classe com os valores passados como parâmetros
    def __init__(self, password, login_ambiente):
        self.password = password
        self.login_ambiente = login_ambiente

    def requisicao_tratada(self, cliente, requisicao):
        '''recebe o link e trata para fazer as requisições'''
        link = f'https://{cliente}/api/v1/{requisicao}'
        return link
    
            
    def login_callix(self, login_ambiente,  password, cliente, token_callix):
        # iniciar o login no ambiente callix
        url = f'https://{cliente}/api/v4/auth/session'
        session = requests.Session()
        hr = HttpRequisitions(session)
        
        # cabeçalhos da requisição
        headers = headers_callix(token_callix)
        payload = payload_login_callix(login_ambiente, password)
        
        login = requests.post(url, params=payload, headers=headers)
        
        return token_callix
    
    def get_agressividade(self, data, cliente, token):
        '''Função para Verificar a alteração de agressividade no callix'''
        
        url = f'https://{cliente}/audit-logs'
        
        # cabeçalhos da requisição de agressividade
        params = params_para_agressividade(data)
        cookies = {"token": token}      
        agressividade = requests.get(url, params=params, cookies=cookies)
        if agressividade.status_code == 200:
            return agressividade.text
        else: 
            print('Erro ao coletar agressividade', agressividade.status_code)
            return False
        
    def get_id_campanha(self, campanha):
        # função para coletar o id da campanha que posteriormente vai ser utilizada para coletar a agressividade
        lista_de_campanhas = []
        for numero in json_campanha['data']:
            for campanhas in numero['id']:
                # loop de iteração pois o cliente pode ter mais de uma campanha
                lista_de_campanhas.append(campanhas)
        return lista_de_campanhas
        
    def get_agressividade(self, cliente,  id_campanha):
        # função para usar o id da campanha e coletar a agressividade
        for campanha in id_campanha:
            url_agressividade = f'https://{cliente}contech.callix.com.br/api/v4/entities/campaigns/{campanha}'
            campanha_detalhada = requests.get(url=url_agressividade, headers=headers_callix)
            if campanha_detalhada.status_code == 200:
                return campanha_detalhada.json()
            else:
                print('Erro ao coletar campanha:', campanha_detalhada.status_code)
                return False
        
    def dados_gerais(self,  cliente, requisicao, data, token, filtro: dict | None = None):
        '''função para coletar os dados de chamadas'''
        session = requests.Session()
        hr = HttpRequisitions(session)
        
        print(f'Coletando {requisicao}')

        link = self.requisicao_tratada(cliente, requisicao)
        
        querystring = payload_request(requisicao, data, filtro)
        headers = headers_callix(token)
        
        response = hr.requisicao_get(querystring, headers, link)
        return response.json()

    def execucao_por_cliente(self, login_ambiente, password, cliente, data, token):
        '''Função para coletar os dados por cliente'''
        try:
              
            time.sleep(10)
            print(f"Logando no cliente {cliente}")
            campanha_json = self.dados_gerais(cliente, 'campaigns', data, token)
            recusadas_bruto = self.dados_gerais(cliente, 'campaign_missed_calls', data, token)
            completas_bruto = self.dados_gerais(cliente, 'campaign_completed_calls', data, token)
            print(f'Aguarde 65 segundos')
            time.sleep(65)
            abandonadas_bruto = self.dados_gerais(cliente, 'campaign_missed_calls', data, token, filtro={"filter[failure_cause]": "9"})
            time.sleep(20)
            performace_bruta = self.dados_gerais(cliente, 'user_performance_reports', data, token)
            token_para_agressividade = self.login_callix(login_ambiente, password, cliente, token)
            id_campanha = self.get_id_campanha(campanha=campanha_json)
            agressividade_json = self.get_agressividade(data, cliente, id_campanha)
            
            
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
        


