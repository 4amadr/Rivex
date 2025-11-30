import pandas as pd
from itertools import count
import requests
import pytz
import json
import csv
from datetime import datetime, timedelta, date
import time
import base64
import os
import sys
from dotenv import load_dotenv
import argparse
import callix_token_db
from callix_token_db import CallixDB

load_dotenv()

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
                print(f"Erro em {cliente_link} requisição bloqueada para chamadas completas: {response.status_code}")
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
                print(f"Erro em {cliente_link} requisição bloqueada para chamadas recusadas: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro em {cliente_link} ao buscar as chamadas recusadas: {e}")
            return None

    def chamadas_abandonadas(self, cliente_link, ano, mes, dia, token):
        '''Função para buscar as chamadas abandonadas brutas de um cliente'''

        data_inicio = f"{ano}-{mes:02d}-{dia:02d}T00:00:00.000Z"
        data_fim = f"{ano}-{mes:02d}-{dia:02d}T23:59:59.999Z"

        link_tratado = f"{cliente_link.lower().replace(' ', '')}contech"
        
        url = f"https://{link_tratado}.callix.com.br/api/v1/campaign_missed_calls"

        print(f"Cliente original: {repr(cliente_link)}")
        print(f"Link tratado: {repr(link_tratado)}")
        print(f"URL final: {url}")
        print(f"Comprimento: {len(cliente_link)}")

        querystring = {"filter[started_at]":f"{data_inicio},{data_fim}",
        # filtro para chamadas abandonadas: 9 = Abandonada
                    "filter[failure_cause]": "9" # 9 = Abandonada
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }   

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)

            if response.status_code == 200:
                chamadas_abandonadas = response.json()
                print("Chamadas abandonadas coletadas com sucesso!")
                return chamadas_abandonadas
            
            else:
                print(f"Erro em {cliente_link} requisição bloqueada para chamadas abandonadas: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro em {cliente_link} ao buscar as chamadas abandonadas: {e}")
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
    print('iniciando coleta de dados de telefonia no callix...')
    # vou gerar a data formatada para inserir no dataframe posteriormente
    # definindo a data como ontem

    dia = int(datetime.today().day)
    ontem = dia - 1
    mes = int(datetime.today().month)
    ano = int(datetime.today().year)
    hoje = date.today()
    ontem_data = hoje - timedelta(days=1)
    ontem_formatado = ontem_data.strftime('%d/%m/%Y')

    try:
        clientes_ativos = ['Essence', 'investmais', 'Corplar', 'Quality', 'Lunart 3',
                        'valm', 'Datateck', 'RDF', 'afsilva', 'Money Solutions']
        
        cd = CallixDB()
        token_db, cliente_db = cd.get_token_and_client_from_db()
        
        if not token_db or not cliente_db:
            print('Sem tokens')
            sys.exit(1)

        CA = CallixAPI(
            cliente=clientes_ativos,
            token=[token_db], # lista para o futuro loop for tratar como lista e iterar por elemento, não por caractere
            cliente_link=cliente_db,  
        )
        
        cliente_lista = []
        completas_lista = []
        abandonadas_lista = []
        recusadas_lista = []
        totais_lista = []
        data_lista = []
        
        print(f"Quantidade de clientes: {len(clientes_ativos)}")
        for cliente_site, token in zip(CA.cliente, CA.token):
            try:

                print(f'Coletando dados do cliente {cliente_site} dia {ontem}-{mes}-{ano}... ')

                completas_bruto = CA.chamadas_completas(cliente_site, ano, mes, ontem, token)
                time.sleep(2)
                recusadas_bruto = CA.chamadas_recusadas_brutas(cliente_site, ano, mes, ontem, token)
                print('Coletando chamadas abandonadas, aguarde um minuto...')
                time.sleep(60)
                abandonadas_bruto = CA.chamadas_abandonadas(cliente_site, ano, mes, ontem, token)

                print(f'Todas os dados de chamadas de {cliente_site} foram coletadas em .JSON, iniciando agora a conversão')

                completas = CA.tratamento_chamadas(completas_bruto)
                abandonadas = CA.tratamento_chamadas(abandonadas_bruto)
                recusadas_semi_bruto = CA.tratamento_chamadas(recusadas_bruto)
                recusadas = CA.chamadas_recusadas(recusadas_semi_bruto, abandonadas)
                totais = CA.agregar_dados(completas, recusadas_semi_bruto)
                
                cliente_lista.append(cliente_site) 
                data_lista.append(ontem_formatado) 
                completas_lista.append(completas)  
                abandonadas_lista.append(abandonadas)  
                recusadas_lista.append(recusadas)   
                totais_lista.append(totais)         
                
                
                # print de dados separados por clientes
                dados_clientes = {
                    'Cliente': cliente_site,
                    'Data': ontem_formatado,
                    'Chamadas': totais,
                    'Completas': completas,
                    'Recusadas': recusadas,
                    'Abandonadas': abandonadas
                }
                print("\nInformações de Consumo do Cliente")

                for key, value in dados_clientes.items():
                    print(f"{key:<12}: {value}")

                print('\nDados coletados com sucesso de todos os clientes!')
                print('Coleta encerrada')
            except Exception as erro_cliente:
                    print(f'Erro durante a coleta de dados do cliente: {cliente_site} {erro_cliente}')
            except Exception as erro_logica:
                print(f'ERRO: {erro_logica} de lógica durante a coleta de dados')
                
        print('Coleta finalizada. Gerando agora o arquivo .csv')
        
        dados_clientes_completos = {
            'Cliente': cliente_lista,
            'Data': data_lista,
            'Chamadas': totais_lista,
            'Completas': completas_lista,
            'Recusadas': recusadas_lista,
            'Abandonadas': abandonadas_lista
        }
                
        print('Gerando agora o arquivo .csv')
        df = pd.DataFrame(dados_clientes_completos)
        df.to_csv(f'clientes_callix_dia{ontem}.csv', columns=['Cliente', 'Data', 'Chamadas', 'Completas',
        'Recusadas', 'Abandonadas'])
        print('Arquivo gerado com sucesso!')
    except Exception as erro_df:
        print(f'ERRO: {erro_df} durante a geração do arquivo .csv')

