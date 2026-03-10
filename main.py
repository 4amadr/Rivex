import os
import time
from src.rivex.enviroments.discadores.Callix.callix import CallixAPI
from src.rivex.enviroments.discadores.Callix.callix_token_db import CallixDB
from src.rivex.data_processing.Callix.cleaner_callix_api import LimpezaCallixAPI
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
from src.rivex.utils.csv_utils.callix_csv.callix_converter import CallixCSVConverter
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.database.database import DatabaseRivex



def main_callix():
    print('Iniciando a coleta de dados no discador Callix...')
    db = CallixDB()
    tokens_clientes = db.get_token_and_client_from_db()
    db.close()

    if not tokens_clientes:
        raise RuntimeError('Sem clientes ou tokens no banco')

    api = CallixAPI()
    limpeza = LimpezaCallixAPI()
    Dc = DateConfig()

    resultados = []
    # callix usa padrão YY/MM/DD
    data = Dc.data_callix()
    for cliente, token in tokens_clientes.items():
        try:
            print('Coletando dados do cliente', cliente)

            dados_brutos = api.execucao_por_cliente(cliente, data, token=token)
            dados_limpos = limpeza.execucao_limpeza(
                discador_usado=dados_brutos["Fila"],
                completas_bruto=dados_brutos["completas"],
                recusadas_bruto=dados_brutos["recusadas"],
                abandonadas_bruto=dados_brutos["abandonadas"],
                performace_suja=dados_brutos["performance"],
                agressividade_suja=dados_brutos["Agressividade"]
            )
            print(type(dados_limpos), dados_limpos)

            resultados.append({
                'Discador': 'Callix',
                'cliente': cliente,
                "Data": data,
                **dados_limpos
            })

        except Exception as e:
            print(f'Erro na execução do cliente {cliente}: {e}')

    converter = CallixCSVConverter()
    caminho = converter.save_csv(resultados)
    print(f'Coleta completamente acabada\n dados salvos em {caminho}')
    return resultados


def main_vonix():
    print('Iniciando a coleta de dados no discador Vonix...')
    ev = ExecucaoVonix()
    lv = LimpezaVonix()
    dc = DateConfig()
    
    data = dc.data_selecionadas()
    url_vonix = os.getenv('LINK_VONIX6')

    # lista com os dados para agregação
    resultados = []

    for equipes_vonix, times in dict_agentes.items():
        print(f'Coletando dados do equipe ->', equipes_vonix)

        for equipe in times:
            # timer para não quebrar o servidor
            time.sleep(15)
            print('Executanto time ->',equipe)
            # primeiro coletamos os dados em formato HTML

            chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, html_agentes, html_agressividade = ev.execucao_vonix(data, url_vonix, equipe)
            print('Dados sujos coletados. Executando agora a limpeza de dados')

            # agora a limpeza de dados para trazer apenas os dados limpos para o banco de dados
            dict_vonix_dados = lv.limpeza_de_dados_vonix(chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, html_agentes, html_agressividade, equipe, data)
            print('Dados limpos. Coleta finalizada.')
            print(dict_vonix_dados)
            
    print('Execução do vonix finalizada')
    return dict_vonix_dados


def main_database(dados: dict):
    # execução e envio dos dados para o banco de dados
    dr = DatabaseRivex
    dr.coleta_chamadas(dados_equipe=dados)


#dados_vonix = main_vonix()
#main_database(dados_vonix)
dados_callix = main_callix()
main_database(dados_callix)
