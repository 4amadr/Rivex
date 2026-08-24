

from pathlib import Path
import os
import logging
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.environments.discadores.Callix.callix import CallixAPICollector
from src.rivex.data_processing.Callix.cleaner_callix_api import processar_dados
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import limpeza_req_callix
from src.rivex.environments.discadores.Callix.callix_client_package import CallixClientData
from src.rivex.environments.discadores.Callix.callix_get_clients import CallixGetClients, GetTokenCallix
from src.rivex.database.database_dados_chamadas import DatabaseCallix
from src.rivex.data_processing.Callix.callix_clients import *
from src.rivex.database.database_clientes import DatabaseClientes

load_dotenv()

logger = logging.getLogger(__name__)

formato = logging.Formatter(
    "%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

Path("Log/callix.log").mkdir(
    parents=True,
    exist_ok=True
)

handler_callix = logging.FileHandler(f"Log/callix_log/callix_dia_{DateConfig.data_selecionadas().replace("/", "-")}.log")
handler_callix.setFormatter(formato)

logger.addHandler(handler_callix)

logger.info("Iniciando configuração do servidor Callix...")

class PipelineCallix:
    def __init__(self):
        self.data=DateConfig()
        self.login=os.getenv("USUARIO_CALLIX_GERAL")
        self.senha=os.getenv("SENHA_CALLIX_GERAL")
        self.banco_callix=DatabaseCallix()
        self.coletar_clientes=CallixGetClients()
        self.db_clientes=DatabaseClientes()
        self.data_selecionada=self.data.data_callix()

    def get_ambiente(self):
        '''
        Retorna as informações necessárias para requisições futuras
        '''
        nome_clientes_ativos = self.coletar_clientes.get_infos_callix()

        lista_cliente = get_clientes_servidor_callix(nome_clientes_ativos.json())

        lista_ativos, lista_inativos = separar_clientes((lista_cliente))

        return lista_ativos, lista_inativos

    def sincronizar_clientes(self, lista_ativos, lista_inativos):

        clientes_db = self.db_clientes.sincronizar_clientes()

        # Clientes ativos do Callix que ainda não existem no banco
        clientes_novos = [
            cliente
            for cliente in lista_ativos
            if cliente not in clientes_db
        ]

        # Clientes que já existiam no DB, mas estavam inativos
        clientes_reativados = [
            cliente
            for cliente in lista_ativos
            if (
                    cliente in clientes_db
                    and not clientes_db[cliente]["ativo"]
            )
        ]

        # Reativar clientes
        for cliente in clientes_reativados:
            self.db_clientes.reativar_clientes(cliente)

        # Buscar tokens SOMENTE dos clientes novos
        novos_clientes = {}

        if clientes_novos:

            get_tokens = GetTokenCallix()

            tokens_novos = get_tokens.fluxo_de_tokens(
                clientes_novos
            )

            tokens_novos = [
                item[0]
                for item in tokens_novos
            ]

            # Validar quantidade
            if len(clientes_novos) != len(tokens_novos):
                raise RuntimeError(
                    f"Quantidade diferente de tokens e clientes. "
                    f"Clientes: {len(clientes_novos)} | "
                    f"Tokens: {len(tokens_novos)}"
                )

            logger.info("Clientes Novos: %r: ", clientes_novos)
            logger.info("Tokens Novos: %r: ", tokens_novos)

            # Associar cliente → token
            novos_clientes = dict(
                zip(clientes_novos, tokens_novos)
            )

        # Inserir somente clientes novos
        for cliente, token in novos_clientes.items():
            self.db_clientes.db_clientes_callix({
                "cliente": cliente,
                "token": token
            })
            logger.info(
                "Tipo do token: %s | valor: %r",
                type(token).__name__,
                token
            )


        # Inativar clientes que estão inativos no Callix
        for cliente in lista_inativos:

            if cliente in clientes_db:
                self.db_clientes.inativar_cliente(cliente)

        # Montar lista final
        lista_tokens = []

        for cliente in lista_ativos:

            if cliente in novos_clientes:
                # Cliente recém cadastrado
                token = novos_clientes[cliente]

            else:
                # Cliente já existente no banco
                token = clientes_db[cliente]["token"]

            lista_tokens.append({
                "cliente": cliente,
                "token": token
            })

        return lista_tokens

    def coletar_dados(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """
        cliente_formatado=cliente.removeprefix("contech.callix.com.br")
        logger.info(f"Coleta iniciada para o cliente o cliente: {cliente_formatado}")

        try:

            # Extração
            api = CallixAPICollector(cliente, token, self.data_selecionada)
            dados_brutos_api = api.api_callix() # dict
            
            logger.info(f"Dados de API do cliente {cliente_formatado} foram coletados")

            req = CAllixRequisition(
                login=self.login, 
                senha=self.senha,
                cliente=cliente_formatado, 
                data=self.data_selecionada,
                id_campanha=dados_brutos_api['campanha'],
                token=token
            )

            chamadas_brutas, agressividade_bruta, tech_bruta = req.requisicao_callix()
            logger.info(f"Chamadas de requisição coletadas para o cliente {cliente_formatado}")

            return dados_brutos_api, chamadas_brutas, agressividade_bruta, tech_bruta, cliente_formatado

        except Exception as e:
            logger.error(f"Falha na coleta de dados do cliente {cliente_formatado}. Erro {e}", exc_info=True)
            return None, None, None, None, None

    def limpar_dados(self, dados_brutos_api, chamadas_brutas, agressividade_bruta, tech_bruta, cliente_formatado):
        try:
            # limpeza
            dict_limpeza = processar_dados(
                dados_brutos_api,
            )

            agressividade_limpa, chamadas_limpas, tech_limpa = limpeza_req_callix(
                json_agentes=chamadas_brutas,
                json_agressividade=agressividade_bruta,
                techs_json=tech_bruta
            )

        except Exception as e:
            logger.error(f"Falha na limpeza de dados do cliente {cliente_formatado}. Erro {e}", exc_info=True)
            return None, None, None, None

        return dict_limpeza, agressividade_limpa, chamadas_limpas, tech_limpa
    

    def empacotar_dados(self, dict_limpeza, agressividade_limpa, chamadas_limpas, tech_limpa, data_selecionada, cliente_formatado):
        try:
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
    
    
            logger.info(f"Dados finais\n"
                    f"CHAMADAS: {dict_chamadas}\n "
                     f"AGENTES: {lista_agentes}")
            
        except Exception as e:
            logger.error(f"Falha no empacotamento de dados do cliente {cliente_formatado}. Erro {e}", exc_info=True)
            return None, None

        return dict_chamadas, lista_agentes

    def executar(self):
        lista_ativos, lista_inativos = self.get_ambiente()
        logger.info("Iniciando pipeline callix")
        lista_tokens = self.sincronizar_clientes(lista_ativos, lista_inativos)


        if not lista_tokens:
            raise RuntimeError("Sem clientes ou tokens")

        try:
            for info in lista_tokens:


                dados_brutos_api, chamadas_brutas, agressividade_bruta, tech_bruta, cliente_formatado = self.coletar_dados(
                    info['cliente'],
                    info['token'],
                    )

                dict_limpeza, agressividade_limpa, chamadas_limpas, tech_limpa = self.limpar_dados(
                    dados_brutos_api,
                    chamadas_brutas,
                    agressividade_bruta,
                    tech_bruta,
                    cliente_formatado)

                dados_cliente, dados_agente = self.empacotar_dados(
                    dict_limpeza,
                    agressividade_limpa, 
                    chamadas_limpas, 
                    tech_limpa, 
                    self.data_selecionada, 
                    cliente_formatado)

                
                if dados_cliente is None:
                    logger.warning(
                        "Cliente %s ignorado por erro no processamento.",
                        cliente_formatado
                    )
                    continue

                self.banco_callix.db_callix(dados_cliente, dados_agente)
        finally:
            self.banco_callix.fechar()





