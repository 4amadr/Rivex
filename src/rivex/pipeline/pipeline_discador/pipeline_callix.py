import logging
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.environments.discadores.Callix.callix import CallixAPICollector
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.environments.discadores.Callix.callix_client_package import CallixClientData
from src.rivex.environments.discadores.Callix.callix_get_clients import CallixGetClients
from src.rivex.environments.discadores.Callix.sincronizar_clientes import SincroniaCallix
from src.rivex.data_processing.Callix.cleaner_callix_api import processar_dados
from src.rivex.data_processing.Callix.cleaner_callix_req import limpeza_req_callix
from src.rivex.database.database_callix.database_callix import DatabaseCallix
from src.rivex.data_processing.Callix.callix_clients import get_clientes_servidor_callix


class PipelineCallix:
    def __init__(self):
        load_dotenv()
        self.log = logging.getLogger(__name__)
        self.max_workers = 5
        self.data = DateConfig()
        self.banco_callix = DatabaseCallix()
        self.coletar_clientes = CallixGetClients()
        self.data_selecionada = self.data.data_callix()
        self.sincronizar = SincroniaCallix()

    def get_ambiente(self):
        '''
        Retorna as informações necessárias para requisições futuras
        '''
        nome_clientes_ativos = (
            self.coletar_clientes.get_infos_callix()
        )
        
        nome_clientes_ativos.raise_for_status()

        clientes_totais = get_clientes_servidor_callix(
            nome_clientes_ativos.json()
            )

        return  clientes_totais

    def coletar_dados(self, cliente:str, token: str):
        """
        Processa a coleta, limpeza e carga de um liente
        """
        cliente_formatado=cliente.removesuffix(
            "contech.callix.com.br"
            ).rstrip(".")

        api = None
        requisicao = None

        try:
            # Instância independente para cada cliente.
            api = CallixAPICollector(
                self.data_selecionada
            )

            requisicao = CAllixRequisition(
                data=self.data_selecionada
            )

            # Extração da API de campanhas.
            dados_brutos_api = api.api_callix(
                token,
                cliente_formatado
            )

            # Autenticação Server SDK e coleta dos dados.
            dados_brutos_req = requisicao.requisicao_callix(
                cliente=cliente_formatado,
                token=token
            )

            return {
                "cliente": cliente_formatado,
                "dados_brutos_api": dados_brutos_api,
                "dados_brutos_req": dados_brutos_req,
                "erro": None
            }

        except Exception as erro:
            self.log.exception(
                "Falha na extração do cliente %s: %s",
                cliente_formatado,
                erro
            )

            return {
                "cliente": cliente_formatado,
                "dados_brutos_api": None,
                "dados_brutos_req": None,
                "erro": erro
            }

        finally:
            for instancia in (api, requisicao):
                sessao = getattr(instancia, "session", None)
                if sessao is not None:
                    sessao.close()

    def limpar_dados(
        self,
        dados_brutos_api: dict,
        dados_brutos_req: dict
    ):
        """
        Realiza a limpeza dos dados provenientes das APIs.

        Os dados do Server SDK são recebidos em blocos:
        accounts, campanhas, audit_logs, outbound_routes,
        chamadas_completas e user_performance_histories.
        """

        try:
            # Limpeza das informações de campanhas e agentes.
            dict_limpeza = processar_dados(
                dados_brutos_api
            )

            # Limpeza dos dados obtidos via Server SDK.
            metricas_req = limpeza_req_callix(
                dados_brutos_req
            )

            return dict_limpeza, metricas_req

        except Exception as erro:
            self.log.exception(
                "Erro durante a limpeza dos dados Callix: %s",
                erro
            )

            return None, None

    def empacotar_dados(
        self,
        dict_limpeza: dict,
        metricas_req: dict,
        cliente_formatado: str
    ):
        """
        Organiza os dados tratados nos objetos utilizados
        para persistência no PostgreSQL.
        """

        try:
            agressividade_limpa = metricas_req[
                "agressividade"
            ]

            chamadas_limpas = metricas_req[
                "chamadas_agentes"
            ]

            tech_limpa = metricas_req["tech"]

            empacotamento_callix = CallixClientData(
                tech=tech_limpa,

                cliente=cliente_formatado.removesuffix(
                    "contech"
                ),

                chamadas=dict_limpeza["Chamadas totais"],

                aceitas=dict_limpeza["Chamadas aceitas"],

                recusadas=dict_limpeza["Chamadas recusadas"],

                abandonadas=dict_limpeza[
                    "Chamadas abandonadas"
                ],

                agressividade=agressividade_limpa,

                data=self.data_selecionada,

                agentes_info=chamadas_limpas
            )

            dict_chamadas = (
                empacotamento_callix.pacote_chamadas()
            )

            lista_agentes = (
                empacotamento_callix.pacote_agentes()
            )

            return dict_chamadas, lista_agentes

        except Exception as erro:
            self.log.exception(
                "Erro ao empacotar dados do cliente %s: %s",
                cliente_formatado,
                erro
            )

            return None, None
    
    def coletar_clientes_paralelo(self, clientes_db):
        """
        Executa a extração HTTP de até cinco clientes
        simultaneamente.

        O processamento e a gravação no banco ficam fora
        das threads.
        """

        resultados = []

        clientes_validos = []
        for cliente in clientes_db:
            if not cliente.get("token"):
                self.log.warning(
                    "Cliente %s ignorado na coleta por ausência de token.",
                    cliente.get("cliente")
                )
                continue
            clientes_validos.append(cliente)

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            tarefas = {
                executor.submit(
                    self.coletar_dados,
                    cliente["cliente"],
                    cliente["token"],
                ): cliente["cliente"]

                for cliente in clientes_validos
            }

            for future in as_completed(tarefas):

                cliente = tarefas[future]

                try:
                    resultado = future.result()

                    if resultado["erro"] is not None:
                        continue

                    resultados.append(resultado)

                    self.log.info(
                        "Extração concluída: %s",
                        cliente
                    )

                except Exception as erro:
                    self.log.exception(
                        "Erro inesperado na coleta de %s: %s",
                        cliente,
                        erro
                    )

        return resultados

    def executar(self):

        try:
            # Descoberta dos clientes com fallback para a base local.
            try:
                clientes_totais = self.get_ambiente()
                clientes_db = self.sincronizar.sincronizar_clientes(
                    clientes_totais
                )
            except Exception as erro:
                self.log.warning(
                    "Falha ao consultar API central Callix (%s). "
                    "Usando base cadastrada no banco.",
                    erro,
                )
                clientes_db = self.sincronizar.consultar_clientes_ativos()

            if not clientes_db:
                raise RuntimeError(
                    "Nenhum cliente ativo encontrado no banco."
                )

            self.log.info(
                "Iniciando coleta de %s clientes.",
                len(clientes_db)
            )

            # Extração paralela.
            resultados = self.coletar_clientes_paralelo(
                clientes_db
            )

            self.log.info(
                "Extração concluída. Clientes coletados: %s/%s",
                len(resultados),
                len(clientes_db)
            )

            # Processamento e persistência sequencial.
            for resultado in resultados:

                cliente = resultado["cliente"]

                try:
                    # Limpeza.
                    dict_limpeza, metricas_req = (
                        self.limpar_dados(
                            resultado["dados_brutos_api"],
                            resultado["dados_brutos_req"]
                        )
                    )

                    if (
                        dict_limpeza is None
                        or metricas_req is None
                    ):
                        continue

                    # Empacotamento.
                    dados_cliente, dados_agente = (
                        self.empacotar_dados(
                            dict_limpeza,
                            metricas_req,
                            cliente
                        )
                    )

                    if (
                        dados_cliente is None
                        or dados_agente is None
                    ):
                        continue

                    # Persistência.
                    self.banco_callix.db_callix(
                        dados_cliente,
                        dados_agente
                    )

                    self.log.info(
                        "Cliente processado e persistido: %s",
                        cliente
                    )

                except Exception as erro:
                    self.log.exception(
                        "Erro no processamento do cliente %s: %s",
                        cliente,
                        erro
                    )

        finally:
            self.banco_callix.fechar()

