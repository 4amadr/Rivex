import os
import time
from src.rivex.enviroments.discadores.IPBox.colect_ipbox import *
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.database.database_dados_chamadas import DatabaseIpbox
import logging
from dotenv import load_dotenv
from src.rivex.data_processing.IPBox.limpeza_ipbox import *

load_dotenv()
logger = logging.getLogger(__name__)


class PipelineIpbox:
    """
    Classe que vai realizar a extração, limpeza e processamento de dados
    do servidor ipbox
    """
    
    def __init__(self):
        date_config = DateConfig()
        self.data_ipbox = date_config.data_ipbox()
        self.data_agentes = date_config.data_ipbox_payload() 
        self.url = os.getenv('URL_IPBOX')
        self.login = os.getenv('IPBOX_LOGIN')
        self.senha = os.getenv('IPBOX_PASSWORD')
        self.token = os.getenv('IPBOX_TOKEN')
        self.banco_ipbox = DatabaseIpbox()
        
        
    def autenticar_e_listar_clientes(self):
        '''
        Inicializa a sessão no servidor e retorna a lista dos clientes
        '''
        ipbox_init = IpboxInit(
            url=self.url,
            login=self.login,
            senha=self.senha,
            data=self.data_ipbox
        )
        
        return ipbox_init.execucao_base_ipbox() # lista de clientes + sessão autenticada
    
    def processar_cliente(self, cliente, ipbox_client, id_cliente):
        '''Processa a extração e limpeza de dados em um cliente'''
        try:
            agressividade, chamadas, = ipbox_client.execucao_ipbox(nome_cliente=cliente, id_cliente=id_cliente)       
            print(f"Cliente atual: {cliente}")
            dict_cliente = empacotar_dados_clientes(chamadas, cliente, self.data_ipbox, agressividade)
            return dict_cliente

        except Exception as e:
            logger.error(f"Erro ao procesar o cliente {cliente}: {e}", exc_info=True)
            
    def executar(self):
        print('Iniciando a configuração do servidor IPBOX.....')

        sessao_logada, clientes_texto = self.autenticar_e_listar_clientes()

        print('Iniciando a coleta de dados dos clientes...')

        execucao_ipbox = IpboxClientConfig(
            url=self.url,
            login=self.login,
            senha=self.senha,
            data=self.data_ipbox,
            data_agentes=self.data_agentes,
            sessao_anterior=sessao_logada,
            token=self.token
        )

        html_clientes = gerar_html(clientes_texto)
        lista_clientes = gerar_lista_clientes(html_clientes)     
        
        agentes_json = execucao_ipbox.get_relatorio_agente().json()

        for cliente in lista_clientes:

            # cliente limpo aqui
            cliente_coletado = get_cliente(cliente)
            id_cliente = get_identificador(cliente)


            dados_cliente = self.processar_cliente(
                cliente_coletado,
                execucao_ipbox,
                id_cliente
                )
            

            if dados_cliente is None:
                continue

            lista_agentes = []

            for agente in agentes_json["data"]:

                if agente["agente"] == "TOTAIS":
                    continue

                nome_cliente = limpar_nome_cliente(
                    agente["times"][0]
                )

                if nome_cliente not in cliente_coletado:
                    continue

                lista_agentes.append(
                    empacotar_dados_agentes(
                        agente,
                        cliente_coletado,
                        self.data_ipbox
                    )
                )

                logger.debug("Cliente: %s", dados_cliente)
                logger.debug("Agentes: %s", lista_agentes)

            # carregamento
            self.banco_ipbox.db_ipbox(
                dados_cliente,
                lista_agentes
            )

            time.sleep(5)
        self.banco_ipbox.fechar_db_ipbox()