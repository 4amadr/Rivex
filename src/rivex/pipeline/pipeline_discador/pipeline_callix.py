

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent 
LOG_DIR = BASE_DIR / "Log" / "callix-log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

data_execucao = DateConfig.data_selecionadas().replace("/", "-")

logger = logging.getLogger("rivex.callix")
logger.setLevel(logging.INFO)
logger.propagate = False  

if not logger.handlers: 
    handler = logging.FileHandler(
        LOG_DIR / f"callix-exec-dia{data_execucao}.log",
        encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

logger.info("========================================")
logger.info("LOG DO CALLIX INICIADO")
logger.info("========================================")


from src.rivex.environments.discadores.Callix.callix import CallixAPICollector
from src.rivex.data_processing.Callix.cleaner_callix_api import processar_dados
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import limpeza_req_callix
from src.rivex.environments.discadores.Callix.callix_client_package import CallixClientData
from src.rivex.environments.discadores.Callix.callix_get_clients import CallixGetClients, GetTokenCallix
from src.rivex.database.database_dados_chamadas import DatabaseCallix
from src.rivex.data_processing.Callix.callix_clients import *
from src.rivex.database.database_clientes import DatabaseClientes


class PipelineCallix:
    def __init__(self):
        self.data=DateConfig()
        self.login=os.getenv("USUARIO_CALLIX_GERAL")
        self.senha=os.getenv("SENHA_CALLIX_GERAL")
        self.banco_callix=DatabaseCallix()
        self.coletar_clientes=CallixGetClients()
        self.db_clientes=DatabaseClientes()

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


    def processar(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """


        cliente_formatado=cliente.removeprefix("contech.callix.com.br")
        logger.info(f"Coleta iniciada para o cliente o cliente: {cliente_formatado}")



        try:
            data_selecionada = self.data.data_callix()
            # Extração
            api = CallixAPICollector(cliente, token, data_selecionada)
            dados_brutos_api = api.api_callix() # dict
            
            if dados_brutos_api:
                logger.info(f"Dados de API do cliente {cliente_formatado} foram coletados")
            else:
                logger.warning(f"Cliente {cliente_formatado} sem dados. Registro API {dados_brutos_api}")

            req = CAllixRequisition(
                login=self.login, senha=self.senha,
                cliente=cliente_formatado, data=data_selecionada,
                id_campanha=dados_brutos_api['campanha'],
                token=token
            )
            chamadas_brutas, agressividade_bruta, tech_bruta = req.requisicao_callix()
            
            logger.info(f"Chamadas de requisição coletadas para o cliente {cliente_formatado}")
            
            if not tech_bruta:
                logger.warning(f"Cliente {cliente_formatado} teve um erro durante a extração da tech {tech_bruta}")

            # limpeza
            dict_limpeza = processar_dados(
                dados_brutos_api['resumo'],
                dados_brutos_api['campanha']
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
            
            
            logger.info(f"Dados finais\n"
                     f"CHAMADAS: {dict_chamadas}\n "
                     f"AGENTES: {lista_agentes}")
            
            return dict_chamadas, lista_agentes

        except Exception as e:
            logger.error(f"Falha ao processar o cliente {cliente_formatado}. Erro {e}", exc_info=True)
            return None, None

    def executar(self):

        logger.info("Iniciando callix")

        lista_ativos, lista_inativos = self.get_ambiente()

        lista_tokens = self.sincronizar_clientes(lista_ativos, lista_inativos)


        if not lista_tokens:
            raise RuntimeError("Sem clientes ou tokens")

        try:
            for info in lista_tokens:


                dados_cliente, dados_agente = self.processar(
                    info['cliente'],
                    info['token'],
                    )
                
                if dados_cliente is None:
                    logger.warning(
            "Cliente %s ignorado por erro no processamento.",
            info["cliente"]
        )
                    continue
                self.banco_callix.db_callix(dados_cliente, dados_agente)
        finally:
            self.banco_callix.fechar()





