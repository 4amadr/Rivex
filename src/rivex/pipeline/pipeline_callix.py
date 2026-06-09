import logging
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
import os
from src.rivex.enviroments.discadores.Callix.callix import CallixAPICollector
from src.rivex.enviroments.discadores.Callix.callix_token_db import CallixDB
from src.rivex.data_processing.Callix.cleaner_callix_api import *
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import *
from src.rivex.database.database import DatabaseRivex
from src.rivex.enviroments.discadores.Callix.callix_client_package import *
from src.rivex.enviroments.discadores.Callix.callix_get_clients import *
from src.rivex.data_processing.Callix.callix_clients import *
load_dotenv()
logger = logging.getLogger(__name__)



class PipelineCallix:
    def __init__(self):
        self.data=DateConfig()
        self.login=os.getenv("USUARIO_CALLIX_GERAL")
        self.senha=os.getenv("SENHA_CALLIX_GERAL")

    def get_ambiente(self):
        '''
        Retorna as informações necessárias para requisições futuras
        '''
        get_infos = CallixGetClients()
        url_clientes = get_infos.get_infos_callix()
        clientes_ativos = clientes_ativos_callix(url_clientes.json())
        print('CLIENTES ATIVOS:  ',clientes_ativos)
        get_token = GetTokenCallix(clientes_ativos)
        lista_infos_clientes = get_token.fluxo_de_tokens()
        
        return lista_infos_clientes



    def processar_cliente(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """
        cliente_formatado=cliente.removeprefix("contech.callix.com.br")
        logger.info(f"Coletando dados do cliente {cliente_formatado}")



        try:
            data_selecionada = self.data.data_callix()
            # Extração
            api = CallixAPICollector(cliente, token, data_selecionada)
            dados_brutos_api = api.api_callix() # dict
            print("ID DA CAMPANHA: ", dados_brutos_api["Campanha"])

            req = CAllixRequisition(
                login=self.login, senha=self.senha,
                cliente=cliente_formatado, data=data_selecionada,
                id_campanha=dados_brutos_api['Campanha']
            )
            chamadas_brutas, agressividade_bruta = req.requisicao_callix()

            # limpeza
            dict_limpeza = processar_dados(
                dados_brutos_api['Completas'],
                dados_brutos_api['Recusadas'],
                dados_brutos_api['Abandonadas'],
                dados_brutos_api['Campanha']
            )

            agressividade_limpa, chamadas_limpas = agressividade_e_agentes(
                json_agentes=chamadas_brutas,
                json_agressividade=agressividade_bruta
            )

            # emcapsulando
            empacotamento_callix = CallixClientData(
                cliente=cliente_formatado,
                chamadas=dict_limpeza["Chamadas totais"],
                aceitas=dict_limpeza["Chamadas aceitas"],
                recusadas=dict_limpeza["Chamadas recusadas"],
                abandonadas=dict_limpeza["Chamadas abandonadas"],
                agressividade=agressividade_limpa,
                data=data_selecionada,
                agentes_info=chamadas_limpas
            )
            dict_chamadas = empacotamento_callix.pacote_chamadas()
            dict_agentes = empacotamento_callix.pacote_agentes()
            print("CHAMADAAAAAAAAAAS: ", dict_chamadas)
            print("AGENTEEEEEEEEEEEEEEES: ", dict_agentes)
            

            # carregar
            logger.info("Enviando dados estruturados para o banco de dados")

        except Exception as e:
            logger.error(f"Falha ao processar o cliente {cliente_formatado}. Erro {e}", exc_info=True)

    def executar(self):
        logger.info("Iniciando callix")
        lista_tokens = self.get_ambiente()
        
        if not lista_tokens:
            raise RuntimeError("Sem clientes ou tokens")
        
        
        for info in lista_tokens:
            self.processar_cliente(info['Cliente'], info['Token'])

