import os
import time
import requests
from dotenv import load_dotenv
from src.rivex.enviroments.discadores.Callix.callix import CallixAPICollector
from src.rivex.enviroments.discadores.Callix.callix_token_db import CallixDB
from src.rivex.data_processing.Callix.cleaner_callix_api import LimpezaCallixAPI
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
from src.rivex.utils.csv_utils.callix_csv.callix_converter import CallixCSVConverter
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.database.database import DatabaseRivex
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.cleaner_callix_req import *
from src.rivex.utils.database_utils.database_config import DatabaseConfig
from src.rivex.enviroments.operadoras.gsolutions.sip_client_scrap import SipClient


def main_gs():
    sc = SipClient(usuario='fbm.revenda',
                   password='Bill23ADM$',
                   url='https://sip3.solutionsvoip.com.br',
                   operadora='Gsolutions',
                   data='2026-04-15')

    custo_minutagem, id_clientes = sc.execucao_pipeline_sip()
    print(custo_minutagem.text)
    print(id_clientes.json())


def main_callix():
    load_dotenv()
    
    print('Iniciando a coleta de dados no discador Callix...')
    # instância de classes
    db = CallixDB()
    dr = DatabaseRivex()
    limpeza = LimpezaCallixAPI()
    Dc = DateConfig()
    tokens_clientes = db.get_token_and_client_from_db()
    data = Dc.data_callix()
    db.close()

    if not tokens_clientes:
        raise RuntimeError('Sem clientes ou tokens no banco')

    password=os.getenv('senha_callix')
    login_ambiente=os.getenv('login_callix')

    resultados = []
    # callix usa padrão YY/MM/DD
    for cliente, token in tokens_clientes.items():
        
        api = CallixAPICollector(cliente, token, data)
        cliente_formatado = cliente.removesuffix("contech.callix.com.br")
        
        '''
        Ordem lógica de coleta que deve ser seguida
        1 - coleta
        2 - limpeza
        3 - DB'''
        
        print(f'Coletando dados do cliente {cliente_formatado}')
        # dicionário com os dados coletados em json
        dict_dados_api = api.api_callix()
        
        print('Limpando...')
        dict_limpeza = limpeza.limpeza_callix(
            dict_dados_api['Completas'],
            dict_dados_api['Recusadas'],
            dict_dados_api['Abandonadas'],
            dict_dados_api['Campanha']
            )
        print(dict_limpeza)
        
        # inicio da coleta por requisições
        req = CAllixRequisition(
                                login=login_ambiente,
                                senha=password,
                                cliente=cliente_formatado,
                                data=data,
                                id_campanha=dict_limpeza['Campanha'], 
                                token=token
        )
        print(f"Iniciando coleta de dados via requisição no cliente: {cliente_formatado}")
        
        chamadas_por_agentes, agressividade = req.requisicao_callix()
        agressividade_limpa, chamadas_limpas = agressividade_e_agentes(json_agentes=chamadas_por_agentes,
                                                                     json_agressividade=agressividade
                                                                     )
        print("Enviando todos os dados para o banco de dados")
        cliente_para_o_banco = {"Cliente": cliente_formatado}
        DatabaseRivex.coleta_callix(data, cliente_para_o_banco, dict_limpeza, agressividade_limpa, chamadas_limpas)    
    return resultados

def main_vonix():
    print('Iniciando a coleta de dados no discador Vonix...')
    ev = ExecucaoVonix()
    lv = LimpezaVonix()
    dc = DateConfig()
    database_conf = DatabaseConfig()
    conexao = database_conf.conect_database()
    
    data = dc.data_selecionadas()
    url_vonix = os.getenv('LINK_VONIX6')

    # lista com os dados para agregação
    resultados = []

    for equipes_vonix, times in dict_agentes.items():
        print(f'Coletando dados do equipe ->', equipes_vonix)

        for equipe in times:
            # timer para não quebrar o servidor
            time.sleep(15)
            print('Executanto a fila ->',equipe)
            # primeiro coletamos os dados em formato HTML

            chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, html_agentes, html_agressividade = ev.execucao_vonix(data=data,
                                                                                                                                                url=url_vonix, 
                                                                                                                                                equipe=equipe)
            print('Dados sujos coletados. Executando agora a limpeza de dados')

            # agora a limpeza de dados para trazer apenas os dados limpos para o banco de dados
            dict_vonix_dados = lv.limpeza_de_dados_vonix(chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, html_agentes, html_agressividade, equipe, data)
           
            # inserir os dados de agentes e suas chamadas no banco
            DatabaseRivex.coleta_agentes(conexao, equipe, data, dict_vonix_dados)
                
            # inserir dados de chamadas no banco
            DatabaseRivex.coleta_chamadas(conexao, dict_vonix_dados)
            
            resultados.append(dict_vonix_dados)
    
    # fechar o banco com os agentes após a execução do loop
    DatabaseRivex.fechar_conexao_vonix(conexao)            
    print('Execução do vonix finalizada')
    return resultados



exec_gs = main_gs()
#dados_vonix = main_vonix()
#dados_callix = main_callix()
