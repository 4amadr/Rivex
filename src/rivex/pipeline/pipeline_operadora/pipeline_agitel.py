from src.rivex.environments.operadoras.gsolutions.sip_client_scrap import EmpacotamentoAgitel, SipCharged, SipClient
import os
from src.rivex.utils.infra_utils.date_config import *
from src.rivex.database.database_dados_chamadas import *
from src.rivex.data_processing.agitel.agitel_data_cleaning import CleaningAgitel
import time

class ExecAgitel():
    def __init__(self):
        self.cleaning_agitel = CleaningAgitel()
    
      
    def pipeline_agitel(self):
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
        '''limpar_sip = CleanerSip(consumo=consumo_por_cliente,
                             id_clientes=dict_id_clientes)
        lista_cliente, lista_minutagem, lista_custo = limpar_sip.limpar_consumo()'''
        
        dados = self.cleaning_agitel.dados_agitel(consumo_por_cliente)
        print(f"DADOS COLETADOS: {dados}")
        
        # segunda execução
        # segunda limpeza
        # empacotamento
        # carregamento
