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
from src.rivex.data_processing.Callix.cleaner_callix_req import *
from src.rivex.utils.database_utils.database_config import DatabaseConfig
from src.rivex.enviroments.operadoras.gsolutions.sip_client_scrap import SipClient, SipCharged
from src.rivex.data_processing.gsolutions.cleaner_sip import *
from src.rivex.enviroments.operadoras.pentagono.pentagono_scrap import pentagonoScrap
from dotenv import load_dotenv
from src.rivex.data_processing.pentagono.pentagono_cleaning import *
from src.rivex.enviroments.discadores.IPBox.colect_ipbox import *
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *


load_dotenv()


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
    dc = DateConfig()
    data = dc.data_ipbox()
    ii = IpboxInit(url='https://contech1.ipboxcloud.com.br:8624/',
                   login=os.getenv('IPBOX_LOGIN'),
                   senha=os.getenv('IPBOX_PASSWORD'),
                   data=data
    )
    print("Iniciando a configuração do servidor")
    sessao_logada, lista_clientes = ii.execucao_base_ipbox() # lista de dicionários
    for cliente in lista_clientes:

        print("Iniciando a coleta de dados do servidor IPBOX")

        ic = IpboxClientConfig(url='https://contech1.ipboxcloud.com.br:8624/',
                               login=os.getenv('IPBOX_LOGIN'),
                               senha=os.getenv('IPBOX_PASSWORD'),
                               data=data,
                               id_cliente=cliente['ID Cliente'],
                               nome_cliente=cliente['Cliente'],
                               sessao_anterior=sessao_logada,
                               token=os.getenv('IPBOX_TOKEN'),
                               )
        agressividade, chamadas, agentes = ic.execucao_ipbox()
        print("HTML DE AGRESSIVIDADE",agressividade)
        #print(chamadas)
        #print(agentes)




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


exec_ipbox = main_ipbox()
#exec_pentagono = main_pentagono()
#exec_agitel = main_agitel()
#exec_gs = main_gs()
#dados_vonix = main_vonix()
#dados_callix = main_callix()
