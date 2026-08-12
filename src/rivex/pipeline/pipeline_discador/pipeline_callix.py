import logging
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
import os
from src.rivex.enviroments.discadores.Callix.callix import CallixAPICollector
from src.rivex.data_processing.Callix.cleaner_callix_api import *
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import *
from src.rivex.enviroments.discadores.Callix.callix_client_package import *
from src.rivex.enviroments.discadores.Callix.callix_get_clients import *
from src.rivex.database.database import DatabaseCallix
from src.rivex.data_processing.Callix.callix_clients import *
load_dotenv()
logger = logging.getLogger(__name__)



class PipelineCallix:
    def __init__(self):
        self.data=DateConfig()
        self.login=os.getenv("USUARIO_CALLIX_GERAL")
        self.senha=os.getenv("SENHA_CALLIX_GERAL")
        self.banco_callix=DatabaseCallix()

    def get_ambiente(self):
        '''
        Retorna as informações necessárias para requisições futuras
        '''
        get_infos = CallixGetClients()
        nome_clientes_ativos = get_infos.get_infos_callix()
        
        logger.info("Consultando clientes ativos no servidor")
        lista_cliente = clientes_ativos_callix(nome_clientes_ativos.json())

        get_token = GetTokenCallix(lista_cliente)
        
        return get_token.fluxo_de_tokens()

    def processar(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """


        cliente_formatado=cliente.removeprefix("contech.callix.com.br")
        logger.info(f"Coletando dados do cliente: {cliente_formatado}")



        try:
            data_selecionada = self.data.data_callix()
            # Extração
            api = CallixAPICollector(cliente, token, data_selecionada)
            dados_brutos_api = api.api_callix() # dict

            req = CAllixRequisition(
                login=self.login, senha=self.senha,
                cliente=cliente_formatado, data=data_selecionada,
                id_campanha=dados_brutos_api['Campanha'],
                token=token
            )
            chamadas_brutas, agressividade_bruta, tech_bruta = req.requisicao_callix()

            # limpeza
            dict_limpeza = processar_dados(
                dados_brutos_api['Completas'],
                dados_brutos_api['Recusadas'],
                dados_brutos_api['Abandonadas'],
                dados_brutos_api['Campanha']
            )

            agressividade_limpa, chamadas_limpas, tech_limpa = limpeza_req_callix(
                json_agentes=chamadas_brutas,
                json_agressividade=agressividade_bruta,
                techs_json=tech_bruta
            )

            # emcapsulando
            empacotamento_callix = CallixClientData(
                tech=tech_limpa,
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
            lista_agentes = empacotamento_callix.pacote_agentes()
            
            return dict_chamadas, lista_agentes

        except Exception as e:
            logger.error(f"Falha ao processar o cliente {cliente_formatado}. Erro {e}", exc_info=True)
            return None, None

    def executar(self):

        logger.info("Iniciando callix")

        lista_tokens = self.get_ambiente()
        
        if not lista_tokens:
            raise RuntimeError("Sem clientes ou tokens")
        
        get_clients = CallixGetClients()
        try:
            for info in lista_tokens:


                dados_cliente, dados_agente = self.processar(
                    info['cliente'],
                    info['token'],
                    )
                
                if dados_cliente is None:
                    logger.warning(
            "Cliente %s ignorado por erro no processamento.",
            info["Cliente"]
        )
                    continue
                self.banco_callix.db_callix(dados_cliente, dados_agente)
        finally:
            self.banco_callix.fechar()





