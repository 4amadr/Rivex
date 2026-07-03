import logging
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
import time
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
        self.banco_callix=DatabaseRivex()

    def get_ambiente(self):
        '''
        Retorna as informações necessárias para requisições futuras
        '''
        get_infos = CallixGetClients()
        tech_clientes, url_clientes = get_infos.get_infos_callix()
        
        print("Consultando clientes ativos no servidor")
        clientes_ativos = clientes_ativos_callix(url_clientes.json())

        get_token = GetTokenCallix(clientes_ativos)
        lista_infos_clientes = get_token.fluxo_de_tokens()
        print("[DEBUG LISTA DE INFORMAÇÕES DOS CLIENTES -> DEVE TER CLIENTE + TOKEN ABAIXO]")
        print(lista_infos_clientes)
        print(type(lista_infos_clientes))
        return lista_infos_clientes # lista de dict



    def processar_cliente(self, cliente:str, token: str, json_tech: str, cursor):
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

            agressividade_limpa, chamadas_limpas, tech_limpa = limpeza_req_callix(
                json_agentes=chamadas_brutas,
                json_agressividade=agressividade_bruta,
                techs_json=json_tech
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
            

            # carregar
            logger.info("Enviando dados estruturados para o banco de dados")
            self.banco_callix.envio_banco(chamadas=dict_chamadas, desempenho_do_agente=lista_agentes, cursor=cursor)

        except Exception as e:
            logger.error(f"Falha ao processar o cliente {cliente_formatado}. Erro {e}", exc_info=True)

    def executar(self):
        print("Abrindo banco de dados")
        cursor, conexao = self.banco_callix.abrir_banco()


        logger.info("Iniciando callix")
        lista_tokens = self.get_ambiente()
        get_clients = CallixGetClients()
        print("[DEBUG DA LISTA DE TOKENS]")
        print(lista_tokens)
        
        if not lista_tokens:
            raise RuntimeError("Sem clientes ou tokens")
        
        for info in lista_tokens: # lista tokens se tornou uma variável simples, e ela precisa ser uma lista
            print("[DEBUG EXECUÇÃO]")
            print(f"INFORMAÇÕES ENVIADAS PARA A EXECUÇÃO: {info}")
            tech = get_clients.get_tech_clientes_callix()


            self.processar_cliente(info['Cliente'], info['Token'], tech, cursor)
        print("Fechando banco de dados")
        self.banco_callix.fechar_db(cursor=cursor, conexao=conexao)



