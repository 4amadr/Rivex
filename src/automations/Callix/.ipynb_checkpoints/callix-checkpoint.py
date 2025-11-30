from itertools import count
import requests
import pytz
import json
import csv
from datetime import datetime, timedelta
import time
import base64
import os
import sys
from dotenv import load_dotenv
import argparse
import callix_token_db
from callix_token_db import CallixDB
load_dotenv()

dia = int(datetime.today().day)
ontem = dia - 1
mes = int(datetime.today().month)
ano = int(datetime.today().year)
dia_teste = ontem - 5

class CallixAPI:

    # Inicializa a classe com os valores passados como parâmetros
    def __init__(self, cliente, token, cliente_link):
        self.cliente = cliente
        self.token = token_db
        self.cliente_link = cliente_db

    def chamadas_completas(self, cliente_link, ano, mes, dia, token):
        '''Função para buscar as chamadas completas de um cliente'''

        data_inicio = f"{ano}-{mes:02d}-{dia:02d}T00:00:00.000Z"
        data_fim = f"{ano}-{mes:02d}-{dia:02d}T23:59:59.999Z"

        # tratar a requisição
        # alguns clientes vem com nome capitalizado e sem o sufixo "contech"
        link_tratado = f"{cliente_link.lower().replace(' ', '')}contech"

        url = f"https://{link_tratado}.callix.com.br/api/v1/campaign_completed_calls"

        print(f'Cliente selecionado {link_tratado}')

        querystring = {
        "filter[started_at]": f"{data_inicio},{data_fim}"
    }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)

            
            
            if response.status_code == 200:
                chamadas_completas = response.json()
                print("Chamadas completas coletadas com sucesso!")
                return chamadas_completas
            else:
                print(f"Erro em {cliente_link} ao buscar as chamadas completas: {response.status_code}")
                print(f" {response.text}")
                return None
        except Exception as e:
            print(f"Erro em {cliente_link} ao buscar as chamadas completas: {e}")
            return None

    def chamadas_recusadas_brutas(self, cliente_link, ano, mes, dia, token):
        '''Função para buscar as chamadas recusadas brutas de um cliente'''

        data_inicio = f"{ano}-{mes:02d}-{dia:02d}T00:00:00.000Z"
        data_fim = f"{ano}-{mes:02d}-{dia:02d}T23:59:59.000Z"

        link_tratado = f"{cliente_link.lower().replace(' ', '')}contech"

        url = f"https://{link_tratado}.callix.com.br/api/v1/campaign_missed_calls"

        querystring = {
        "filter[started_at]": f"{data_inicio},{data_fim}"
    }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }   

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)

            if response.status_code == 200:
                chamadas_recusadas_bruto = response.json()
                print("Chamadas recusadas(BRUTAS) coletadas com sucesso. AINDA FALTA TRATAR !!!")
                return chamadas_recusadas_bruto
            else:
                print(f"Erro em {self.cliente_link} ao buscar as chamadas recusadas: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro em {self.cliente_link} ao buscar as chamadas recusadas: {e}")
            return None

    def chamadas_abandonadas(self, cliente_link, ano, mes, dia, token):
        '''Função para buscar as chamadas abandonadas brutas de um cliente'''

        data_inicio = f"{ano}-{mes:02d}-{dia:02d}T00:00:00.000Z"
        data_fim = f"{ano}-{mes:02d}-{dia:02d}T23:59:59.999Z"

        link_tratado = f"{cliente_link.lower().replace(' ', '')}contech"
        
        url = f"https://{link_tratado}.callix.com.br/api/v1/campaign_missed_calls"

        querystring = {"filter[started_at]":f"{data_inicio},{data_fim}",
        # filtro para chamadas abandonadas: 9 = Abandonada
                    "filter[failure_cause]": "9" # 9 = Abandonada
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }   

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)

            if response.status_code == 200:
                chamadas_abandonadas = response.json()
                print("Chamadas abandonadas coletadas com sucesso!")
                print(chamadas_abandonadas)
                return chamadas_abandonadas
            
            else:
                print(f"Erro em {self.cliente_link} ao buscar as chamadas abandonadas: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro em {self.cliente_link} ao buscar as chamadas abandonadas: {e}")
            return None
    
    def tratamento_chamadas(self, dados_chamadas):
        '''função para pegar o arquivo .json e filtrar apenas os dados que
        serão necessários'''
        try:
            if 'meta' in dados_chamadas:
                count_data = dados_chamadas['meta']
                if 'count' in count_data:
                    chamadas_dict = int(count_data['count'])
                    return chamadas_dict
        except Exception as e:
            print(f"ERRO {e} durante o tratamento de chamadas")
            chamadas_dict = 0
            return chamadas_dict

    def agregar_dados(self, completas, recusadas):
        '''Função para obter o total de chamadas em um dia 
        OBS: O ARGUMENTO DEVE SER AS COMPLETAS + RECUSADAS(BRUTAS!!!!)'''
        try:
            chamadas_totais = completas + recusadas
            return chamadas_totais
        except Exception as e:
            print(f"ERRO: {e} Durante a geração do total")
            chamadas_totais = 0
            return chamadas_totais

    def chamadas_recusadas(self, recusadas_semi_bruto, abandonadas):
        '''Função para calcular o valor limpo das chamadas recusadas'''
        try:
            recusadas = recusadas_semi_bruto - abandonadas
            print('Chamadas, recusadas: ', recusadas )
            return recusadas
            # vou adicionar uma condição
            # chamadas recusadas quase nunca vai ser menor que abandonadas
            # se isso acontecer, provavelmente houve um erro na coleta de chamadas recusadas
            # como quase nunca != nunca a condição vai verificar apenas se recusadas é menor do que zero
            if recusadas < 0:
                print("Erro de lógica em chamadas recusadas, colete novamente!")
                return False
        except Exception as e:
            print(f"ERRO: {e} durante o tratamento das recusadas")
            recusadas = 0
            return recusadas



if __name__ == '__main__':
    print('iniciando...')
    try:
        
        clientes_ativos = ['Essence', 'investmais', 'Corplar', 'Quality', 'Lunart 3',
                        'V.A.L.M', 'Datateck', 'RDF Consultoria', 'afsilva', 'Money Solutions']
        
        
        cd = CallixDB()
        token_db, cliente_db = cd.get_token_and_client_from_db()
        
        if not token_db or not cliente_db:
            print('Sem tokens')
            sys.exit(1)
            
        
        CA = CallixAPI(
            cliente=clientes_ativos,
            token=token_db,
            cliente_link=cliente_db,  
        )
        print(f"Quantidade de clientes: {len(clientes_ativos)}")
        

        for cliente_site in CA.cliente:

            nome_cliente = cliente_site

            print(f'Coletando dados do cliente {cliente_site} dia {dia_teste}-{mes}-{ano}... ')
            
            completas_bruto = CA.chamadas_completas(cliente_site, ano, mes, dia_teste, token_db)
            time.sleep(2)
            recusadas_bruto = CA.chamadas_recusadas_brutas(cliente_site, ano, mes, dia_teste, token_db)
            print('Coletando chamadas abandonadas, aguarde um minuto...')
            time.sleep(60)
            abandonadas_bruto = CA.chamadas_abandonadas(cliente_site, ano, mes, dia_teste, token_db)
            
            print(f'Todas os dados de chamadas de {cliente_site} foram coletadas em .JSON, iniciando agora a conversão')

            completas = CA.tratamento_chamadas(completas_bruto)
            abandonadas = CA.tratamento_chamadas(abandonadas_bruto)
            recusadas_semi_bruto = CA.tratamento_chamadas(recusadas_bruto)
            recusadas = CA.chamadas_recusadas(recusadas_semi_bruto, abandonadas)
            totais = CA.agregar_dados(completas, recusadas_semi_bruto)

            print('Informações de consumo do cliente:')
            dados_clientes = {
                'Chamadas': totais,
                'Cliente': nome_cliente,
                'Completas': completas,
                'Recusadas': recusadas,
                'Abandonadas': abandonadas
            }
            if dados_clientes:
                print("\n=== Informações de Consumo do Cliente ===")

                for key, value in dados_clientes.items():
                    print(f"{key:<12}: {value}")

                print("==========================================\n")
            else:
                print('Dados vazios')
                print(dados_clientes)
    except Exception as e:
        print(f'ERRO: {e} durante a coleta de dados')

