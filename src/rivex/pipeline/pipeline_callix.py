import logging
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
import os
from src.rivex.enviroments.discadores.Callix.callix import CallixAPICollector
from src.rivex.enviroments.discadores.Callix.callix_token_db import CallixDB
from src.rivex.data_processing.Callix.cleaner_callix_api import LimpezaCallixAPI
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import *
from src.rivex.database.database import DatabaseRivex
from src.rivex.enviroments.discadores.Callix.callix_get_clients import *
from src.rivex.data_processing.Callix.callix_clients import *



load_dotenv()
logger = logging.getLogger(__name__)
from collections import namedtuple

CallixClientData = namedtuple("CallixClientData", [
    "nome_cliente",
    "data",
    "dados_limpos",
    "agressovodade",
    "chamadas_agentes"
])


class PipelineCallix:
    def __init__(self):
        data=DateConfig()
        self.login=os.getenv("login_callix")
        self.senha=os.getenv("senha_callix")
        self.limpeza=LimpezaCallixAPI()

    def get_ambiente(self):
        get_infos = CallixGetClients()
        url_clientes = get_infos.get_infos_callix()

        clientes_ativos = clientes_ativos_callix(url_clientes.json())
        print('Clientes ativos no callix atualmente', clientes_ativos)
        print("URL dos clientes ativos no servidor: ", url_clientes.json())
        return clientes_ativos



    def processar_cliente(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """
        cliente_formatado=cliente.removeprefix("contech.callix.com.br")
        logger.info(f"Coletando dados do cliente {cliente_formatado}")



        try:
            # Extração
            api = CallixAPICollector(cliente, token, self.data)
            dados_brutos_api = api.api_callix()

            req = CAllixRequisition(
                login=self.login, senha=self.senha,
                cliente=cliente_formatado, data=self.data,
                id_campanha=dados_brutos_api['Campanha'], token=token
            )
            chamadas_brutas, agressividade_bruta = req.requisicao_callix()

            # limpeza
            dict_limpeza = self.limpeza.limpeza_callix(
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
            dados_processados = CallixClientData(
                nome_cliente=cliente_formatado,
                data=self.data,
                dados_limpos=dict_limpeza,
                agressovodade=agressividade_limpa,
                chamadas_agentes=chamadas_limpas
            )

            # carregar
            logger.info("Enviando dados estruturados para o banco de dados")
            DatabaseRivex.coleta_callix(dados_processados)

        except Exception as e:
            logger.error(f"Falha ao processar o cliente {cliente_formatado}. Erro {e}", exc_info=True)

    def executar(self):
        logger.info("Iniciando callix")
        clientes_ativos = self.get_ambiente()
        #db = CallixDB()
        #token_clientes = db.get_token_and_client_from_db()
        #db.close()
        

        if not clientes_ativos:
            raise RuntimeError("Sem clientes ativos")
        
        
        for cliente in clientes_ativos:
            cliente = cliente.replace('Contech - ', '')
            tokens_callix = GetTokenCallix(cliente=cliente)
            dict_tokens = tokens_callix.fluxo_de_tokens()
            print("MOSTANDO O DICIONÁRIO")
            print("Di ",dict_tokens)
            self.processar_cliente(cliente, dict_tokens)

