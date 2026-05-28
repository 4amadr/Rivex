import os
import time
from src.rivex.enviroments.discadores.IPBox.colect_ipbox import *
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *
from src.rivex.utils.infra_utils.date_config import DateConfig
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def main_ipbox():
    class PipelineIpbox:
        """
        Classe que vai realizar a extração, limpeza e processamento de dados
        do servidor ipbox
        """
        
        def __int__(self):
            date_config = DateConfig()
            self.data_ipbox = date_config.data_ipbox()
            self.data_agentes = date_config.data_ipbox_payload() 
            self.url = os.getenv('URL_IPBOX')
            self.login = os.getenv('IPBOX_LOGIN')
            self.senha = os.getenv('IPBOX_PASSWORD')
            self.token = os.getenv('IPBOX_TOKEN')
            
            
        def autenticar_e_listar_clientes(self):
            '''
            Inicializa a sessão no servidor e retorna a lista dos clientes
            '''
            
            IpboxInit = IpboxInit(
                url=self.url,
                login=self.login,
                senha=self.senha,
                data=self.data_ipbox
            )
            
            return IpboxInit.execucao_base_ipbox()
        
        def processar_cliente(self, cliente, ipbox_client):
            '''Processa a extração e limpeza de dados em um clietne'''
            try:
                nome_cliente = cliente['Cliente']
                agressividade, chamadas, agentes = ipbox_client.execucao_ipbox(nome_cliente=nome_cliente)
                
                agressividade_limpa = limpeza_agressividade(agressividade_html=agressividade)
                agentes_limpos = limpeza_agentes_ipbox(agentes.json())
                chamadas_aceitas, chamadas_totais = limpeza_chamadas_ipbox(chamadas.json())
                
                print(f"Dados processados para {nome_cliente}")
                
            except Exception as e:
                logger.error(f'Erro ao procesar o cliente {cliente.get('Cliente')}: {e}', exc_info=True)
                
        def executar(self):
            print('Iniciando a configuração do servidor IPBOX.....')
            sessao_logada, lista_clientes = self.autenticar_e_listar_clientes()
            
            print('Iniciando a coleta de dados dos clietnes...')
            ipbox_client = IpboxClientConfig(
                url=self.url,
                login=self.login,
                senha=self.senha,
                data=self.data_ipbox,
                data_agentes=self.data_agentes,
                sessao_anterior=sessao_logada,
                token=self.token
            )
            
            for cliente in lista_clientes:
                self.processar_cliente(cliente, ipbox_client)
                time.sleep(5)
                