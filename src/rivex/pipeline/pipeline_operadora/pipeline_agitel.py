from src.rivex.environments.operadoras.gsolutions.sip_client_scrap import EmpacotamentoAgitel, SipCharged, SipClient
import os
from src.rivex.utils.infra_utils.date_config import *
from src.rivex.database.database_dados_chamadas import *
from src.rivex.data_processing.agitel.agitel_data_cleaning import *
from src.rivex.database.database_dados_chamadas import DatabaseAgitel
import time
import logging

log = logging.getLogger(__name__)

class ExecAgitel():

    
      
    def pipeline_agitel(self):
        dc = DateConfig()
        data_selecionada = dc.data_selecionadas()
        database = DatabaseAgitel()
        print(f"Coleta do dia {data_selecionada} na agitel")
        sc = SipClient(usuario=os.getenv('AGITEL_USER'),
                    password=os.getenv('AGITEL_PASSWORD'),
                    url=os.getenv('AGITEL_URL'),
                    operadora='Agitel',
                    data=data_selecionada)
        sch = SipCharged(
            data=data_selecionada,
            url_base=os.getenv('AGITEL_URL'),
            usuario=os.getenv('AGITEL_USER'),
            password=os.getenv('AGITEL_PASSWORD'),
            
        )

        consumo_por_cliente, dict_id_clientes = sc.execucao_pipeline_sip()

        dados_consumo = get_dados_clientes(consumo_por_cliente.text)
 
        for dado in dados_consumo:
            dados_prontos = dados_empacotados(dado, data_selecionada)
            print(f"Dados a ser enviados para o banco de dados: {dados_prontos}")
            database.enviar_dados_db_agitel(dados_prontos)
        database.fechar_db_telefonia()

