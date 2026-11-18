import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.environments.discadores.Callix.callix import CallixAPICollector
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.environments.discadores.Callix.callix_client_package import CallixClientData
from src.rivex.data_processing.Callix.cleaner_callix_api import processar_dados
from src.rivex.data_processing.Callix.cleaner_callix_req import limpeza_req_callix
from src.rivex.database.database_callix.database_callix import DatabaseCallix
from src.rivex.database.database_callix.database_callix_clientes import DatabaseClientes


class PipelineCallix:
    def __init__(self):
        load_dotenv()
        self.log = logging.getLogger(__name__)
        self.max_workers = 5
        self.data = DateConfig()
        self.banco_callix = DatabaseCallix()
        self.db_clientes = DatabaseClientes()
        self.data_selecionada = self.data.data_callix()

    def coletar_dados(self, cliente: str, token: str) -> dict:
        """Executa a coleta da API v1 e do Server SDK/v4 para um cliente."""
        cliente_formatado = cliente.removesuffix(
            "contech.callix.com.br"
        ).rstrip(".")

        api = None
        requisicao = None

        try:
            api = CallixAPICollector(self.data_selecionada)
            requisicao = CAllixRequisition(data=self.data_selecionada)

            dados_brutos_api = api.api_callix(token, cliente_formatado)
            dados_brutos_req = requisicao.requisicao_callix(
                cliente=cliente_formatado,
                token=token,
            )

            return {
                "cliente": cliente_formatado,
                "dados_brutos_api": dados_brutos_api,
                "dados_brutos_req": dados_brutos_req,
                "erro": None,
            }

        except Exception as erro:
            self.log.exception(
                "Falha na extração do cliente %s: %s",
                cliente_formatado,
                erro,
            )
            return {
                "cliente": cliente_formatado,
                "dados_brutos_api": None,
                "dados_brutos_req": None,
                "erro": erro,
            }

        finally:
            for instancia in (api, requisicao):
                sessao = getattr(instancia, "session", None)
                if sessao is not None:
                    sessao.close()

    def limpar_dados(self, dados_brutos_api: dict, dados_brutos_req: dict):
        """Limpa os dados da API v1 e do Server SDK/v4."""
        try:
            dict_limpeza = processar_dados(dados_brutos_api)
            metricas_req = limpeza_req_callix(dados_brutos_req)
            return dict_limpeza, metricas_req
        except Exception as erro:
            self.log.exception(
                "Erro durante a limpeza dos dados Callix: %s",
                erro,
            )
            return None, None

    def empacotar_dados(
        self,
        dict_limpeza: dict,
        metricas_req: dict,
        cliente_formatado: str,
    ):
        """Organiza os dados tratados nos objetos de persistência no PostgreSQL."""
        try:
            empacotamento_callix = CallixClientData(
                tech=metricas_req["tech"],
                cliente=cliente_formatado.removesuffix("contech"),
                chamadas=dict_limpeza["Chamadas totais"],
                aceitas=dict_limpeza["Chamadas aceitas"],
                recusadas=dict_limpeza["Chamadas recusadas"],
                abandonadas=dict_limpeza["Chamadas abandonadas"],
                agressividade=metricas_req["agressividade"],
                data=self.data_selecionada,
                agentes_info=metricas_req["chamadas_agentes"],
            )

            return (
                empacotamento_callix.pacote_chamadas(),
                empacotamento_callix.pacote_agentes(),
            )
        except Exception as erro:
            self.log.exception(
                "Erro ao empacotar dados do cliente %s: %s",
                cliente_formatado,
                erro,
            )
            return None, None

    def coletar_clientes_paralelo(self, clientes_db: list[dict]) -> list[dict]:
        """Executa a extração HTTP paralela para clientes com token cadastrado."""
        resultados = []
        clientes_validos = []

        for cliente in clientes_db:
            if not cliente.get("token"):
                self.log.warning(
                    "Cliente %s ignorado na coleta por ausência de token.",
                    cliente.get("cliente"),
                )
                continue
            clientes_validos.append(cliente)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
                    self.log.info("Extração concluída: %s", cliente)
                except Exception as erro:
                    self.log.exception(
                        "Erro inesperado na coleta de %s: %s",
                        cliente,
                        erro,
                    )

        return resultados

    def executar(self):
        try:
            clientes_db = self.db_clientes.consultar_view()
            if not clientes_db:
                raise RuntimeError("Nenhum cliente ativo encontrado no banco.")

            self.log.info(
                "Iniciando coleta de %s clientes ativos.",
                len(clientes_db),
            )

            resultados = self.coletar_clientes_paralelo(clientes_db)

            self.log.info(
                "Extração concluída. Clientes coletados: %s/%s",
                len(resultados),
                len(clientes_db),
            )

            for resultado in resultados:
                cliente = resultado["cliente"]
                try:
                    dict_limpeza, metricas_req = self.limpar_dados(
                        resultado["dados_brutos_api"],
                        resultado["dados_brutos_req"],
                    )
                    if dict_limpeza is None or metricas_req is None:
                        continue

                    dados_cliente, dados_agente = self.empacotar_dados(
                        dict_limpeza,
                        metricas_req,
                        cliente,
                    )
                    if dados_cliente is None or dados_agente is None:
                        continue

                    self.banco_callix.db_callix(dados_cliente, dados_agente)
                    self.log.info("Cliente processado e persistido: %s", cliente)
                except Exception as erro:
                    self.log.exception(
                        "Erro no processamento do cliente %s: %s",
                        cliente,
                        erro,
                    )
        finally:
            self.banco_callix.fechar()
            self.db_clientes.fechar()
