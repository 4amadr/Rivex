import os
import time
import requests
from dotenv import load_dotenv
from src.rivex.enviroments.discadores.Callix.callix import CallixAPICollector
from src.rivex.enviroments.discadores.Callix.callix_token_db import CallixDB
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
from src.rivex.utils.csv_utils.callix_csv.callix_converter import CallixCSVConverter
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.database.database import DatabaseRivex
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import *
from src.rivex.utils.database_utils.database_config import DatabaseConfig
from src.rivex.enviroments.operadoras.gsolutions.sip_client_scrap import SipClient, SipCharged
from src.rivex.data_processing.gsolutions.cleaner_sip import *
from src.rivex.enviroments.operadoras.pentagono.pentagono_scrap import pentagonoScrap
from dotenv import load_dotenv
from src.rivex.data_processing.pentagono.pentagono_cleaning import *
from src.rivex.enviroments.discadores.IPBox.colect_ipbox import *
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *
import logging
from src.rivex.pipeline.pipeline_ipbox import *
from src.rivex.pipeline.pipeline_callix import *

load_dotenv()
logger = logging.getLogger(__name__)


def main_gs():
    dc = DateConfig()
    data = dc.data_selecionadas()
    print(f"Coleta do dia {data} na Gsolutions")
    sc = SipClient(usuario=os.getenv('GSOLUTIONS_LOGIN'),
                   password=os.getenv('GSOLUTIONS_PASSWORD'),
                   url=os.getenv('GSOLUTIONS_URL'),
                   operadora='Gsolutions',
                   data=data)
    sch = SipCharged(
        data=data,
        url_base=os.getenv('GSOLUTIONS_URL'),
        usuario=os.getenv('GSOLUTIONS_LOGIN'),
        password=os.getenv('GSOLUTIONS_PASSWORD'),
        
    )
    ''' coleta que retorna:
    consumo_cliente -> Clientes online, Minutagem e custo.
    id_clientes -> Id de cada cliente, nome do cliente
    '''
    custo_minutagem_por_cliente, id_clientes = sc.execucao_pipeline_sip()
    clientes_mapeados = mapeamento_clientes(id_clientes.json())
    
    #Limpeza de dados
    clientes_mapeados, resultado_custos = limpeza_de_dados_base(id_clientes.json(),
                                                                custo_minutagem_por_cliente.text
                                                                            )
    
    '''
    Desempacotando dicionários para usar na próxima função que retorna as chamadas tarifadas
    ids_online é a lista de ids referente aos clientes que tiveram consumo no dia selecionado
    '''
    chamadas_tarifadas = sch.execucao_sip_tarifas(resultado_custos, clientes_mapeados)
    lista_dados = limpeza_de_dados_final(chamadas_tarifadas, resultado_custos)
    print(lista_dados)
    
def main_agitel():
        dc = DateConfig()
        data = dc.data_selecionadas()
        print(f"Coleta do dia {data} na agitel")
        sc = SipClient(usuario=os.getenv('AGITEL_USER'),
                    password=os.getenv('AGITEL_PASSWORD'),
                    url=os.getenv('AGITEL_URL'),
                    operadora='Agitel',
                    data=data)
        sch = SipCharged(
            data=data,
            url_base=os.getenv('AGITEL_URL'),
            usuario=os.getenv('AGITEL_USER'),
            password=os.getenv('AGITEL_PASSWORD'),
            
        )
        # execução
        consumo_por_cliente, dict_id_clientes = sc.execucao_pipeline_sip()
        
        # limpeza
        clientes_ativos = mapeamento_clientes(dict_id_clientes.text) # list
        print("IDS DO CLIENTE: ", dict_id_clientes)
        print("CONSUMO POR CLIENTE: ", clientes_ativos)
        clientes, consumos = limpeza_de_dados_base(dict_id_clientes.text, consumo_por_cliente.text)
        print("CONSUMO AQUI: ",consumos) # lista que está faltando a tech
        
        lista_chamadas_tarifadas = sch.lista_chamadas_tarifadas(clientes_ativos, dict_id_clientes.text)
        tarifas_limpas = processar_tarifas_com_resiliencia(lista_chamadas_tarifadas) # lista
        print(tarifas_limpas)
        print("Dados limpos! Preparando dados para o banco de dados")
        # empacotamento
        for cliente_ativo, consumo, chamada_tarifada in zip(clientes_ativos, consumos, tarifas_limpas):
            if not chamada_tarifada:
                chamada_tarifada = 0
            dict_pronto = {
                "tech" : cliente_ativo["Tech"],
                "Cliente" : cliente_ativo["Cliente"],
                "Data" : data,
                "Minutagem": consumo["Minutagem"],
                "Custo": consumo["Custo"],
                "Chamadas tarifadas": chamada_tarifada
            }
            print(dict_pronto)


        
        


def main_pentagono():
    dc = DateConfig()
    data = dc.data_selecionadas()
    
    ps = pentagonoScrap(
    usuario=os.getenv('PENTAGONO_LOGIN'),
    senha=os.getenv('PENTAGONO_PASSWORD'),
    data=data
    )
    
    # execução e coleta de dados sujos em formato HTML
    login, pagina_inicial, relatorio_html = ps.execucao_pentagono()
    
    # limpeza de dados
    dados = execucao_limpeza(relatorio_html)
    print(dados)
    
def main_ipbox():
   pipeline = PipelineIpbox()
   pipeline.executar()

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

def main_callix():
    pipeline_callix = PipelineCallix()
    pipeline_callix.executar()

#exec_ipbox = main_ipbox()
#exec_pentagono = main_pentagono()
exec_agitel = main_agitel()
#exec_gs = main_gs()
#dados_vonix = main_vonix()
#dados_callix = main_callix()
