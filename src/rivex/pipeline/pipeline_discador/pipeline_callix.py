from pathlib import Path
import os
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.environments.discadores.Callix.callix import CallixAPICollector
from src.rivex.data_processing.Callix.cleaner_callix_api import processar_dados
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import limpeza_req_callix
from src.rivex.environments.discadores.Callix.callix_client_package import CallixClientData
from src.rivex.environments.discadores.Callix.callix_get_clients import CallixGetClients
from src.rivex.data_processing.Callix.callix_clients import *
from src.rivex.environments.discadores.Callix.sincronizar_clientes import SincroniaCallix
from src.rivex.database.database_callix.database_callix import DatabaseCallix


class PipelineCallix:
    def __init__(self):
        load_dotenv()
        self.data=DateConfig()
        self.login=os.getenv("USUARIO_CALLIX_GERAL")
        self.senha=os.getenv("SENHA_CALLIX_GERAL")
        self.banco_callix=DatabaseCallix()
        self.coletar_clientes=CallixGetClients()
        self.data_selecionada=self.data.data_callix()
        self.api = CallixAPICollector(self.data_selecionada)
        self.sincronizar = SincroniaCallix()
        self.requisicao = CAllixRequisition(
            login=self.login, 
            senha=self.senha,
            data=self.data_selecionada
        )

    def get_ambiente(self):
        '''
        Retorna as informações necessárias para requisições futuras
        '''
        nome_clientes_ativos = self.coletar_clientes.get_infos_callix()

        clientes_totais = get_clientes_servidor_callix(nome_clientes_ativos.json())

        return  clientes_totais

    def coletar_dados(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """
        cliente_formatado=cliente.removesuffix("contech.callix.com.br")

        try:
            # Extração
            dados_brutos_api = self.api.api_callix(token, cliente_formatado) 
            dados_brutos_req = self.requisicao.requisicao_callix(dados_brutos_api["campanha"], cliente_formatado, token)
            return dados_brutos_api, dados_brutos_req, cliente_formatado

        except Exception as e:
            return None, None, cliente_formatado

    def limpar_dados(self, dados_brutos_api, dados_brutos_req, cliente_formatado):
        try:
            # limpeza
            dict_limpeza = processar_dados(
                dados_brutos_api,
            )
            agressividade_limpa, chamadas_limpas, tech_limpa, produtos_contratados, preco_produto  = limpeza_req_callix(
                json_agentes=dados_brutos_req["chamadas agentes"],
                json_agressividade=dados_brutos_req["agressividade"],
                techs_json=dados_brutos_req["tech"],
                produto=dados_brutos_req["produto"]
            )

        except Exception as e:
            return None, None, None, None

        return dict_limpeza, agressividade_limpa, chamadas_limpas, tech_limpa

    def empacotar_dados(self, dict_limpeza, agressividade_limpa, chamadas_limpas, tech_limpa, data_selecionada, cliente_formatado):
        empacotamento_callix = CallixClientData(
                tech=tech_limpa,
                cliente=cliente_formatado.removesuffix("contech"),
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

    def executar(self):
        clientes_totais = self.get_ambiente()
        clientes_db = self.sincronizar.sincronizar_clientes(clientes_totais)

        if not clientes_db:
            raise RuntimeError("Sem clientes no banco")

        try:
            for dados_cadastro_cliente_ativo in clientes_db:
                dados_brutos_api, dados_brutos_req, cliente_formatado = self.coletar_dados(
                    dados_cadastro_cliente_ativo["cliente"],
                    dados_cadastro_cliente_ativo["token"]
                )


                if dados_brutos_api is None or dados_brutos_req is None:
                    continue
                dict_limpeza, agressividade_limpa, chamadas_limpas, tech_limpa = self.limpar_dados(
                    dados_brutos_api,
                    dados_brutos_req,
                    cliente_formatado)
                
                if dict_limpeza is None:
                    continue

                dados_cliente, dados_agente = self.empacotar_dados(
                    dict_limpeza,
                    agressividade_limpa, 
                    chamadas_limpas, 
                    tech_limpa, 
                    self.data_selecionada, 
                    cliente_formatado)

                if dados_cliente is None:
                    continue
                
                self.banco_callix.db_callix(dados_cliente, dados_agente)
        finally:
            self.banco_callix.fechar()
