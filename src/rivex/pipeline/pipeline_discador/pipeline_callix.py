from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Optional

from src.rivex.config.settings import Settings
from src.rivex.data_processing.Callix.callix_client_package import CallixClientData
from src.rivex.data_processing.Callix.cleaner_callix_api import processar_dados
from src.rivex.data_processing.Callix.cleaner_callix_req import limpeza_req_callix
from src.rivex.database.config_database import conexao_rivex
from src.rivex.database.database_callix.database_callix import DatabaseCallix
from src.rivex.database.database_callix.database_callix_clientes import DatabaseClientes
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro, ResumoExecucao
from src.rivex.environments.discadores.Callix.callix import CallixAPICollector
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.logging_config import PipelineLogger


class PipelineCallix:
    nome = "callix"

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings
        self.log = PipelineLogger("callix")
        callix_cfg = settings.callix if settings is not None else None
        self.max_workers = callix_cfg.max_workers if callix_cfg else 5
        self.retry_429_wait = float(callix_cfg.retry_429_wait) if callix_cfg else 60.0
        self.retry_429_max = callix_cfg.retry_429_max if callix_cfg else 5
        self.data_selecionada: date = DateConfig.ontem()

    def coletar_dados(self, cliente: str, token: str) -> dict:
        """Executa a coleta da API v1 e do Server SDK/v4 para um cliente."""
        cliente_formatado = cliente.removesuffix(
            "contech.callix.com.br"
        ).rstrip(".")

        api = None
        requisicao = None
        data_str = self.data_selecionada.strftime("%Y-%m-%d")

        try:
            api = CallixAPICollector(
                data_str,
                retry_429_wait=self.retry_429_wait,
                retry_429_max=self.retry_429_max,
            )
            requisicao = CAllixRequisition(
                data=data_str,
                retry_429_wait=self.retry_429_wait,
                retry_429_max=self.retry_429_max,
            )

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
            self.log.erro(
                "Falha na extração do cliente",
                erro=erro,
                cliente=cliente_formatado,
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
            self.log.erro(
                "Erro durante a limpeza dos dados Callix",
                erro=erro,
            )
            return None, None

    def empacotar_dados(
        self,
        dict_limpeza: dict,
        metricas_req: dict,
        cliente_formatado: str,
    ) -> tuple[Optional[ClienteRegistro], Optional[list[OperadorRegistro]]]:
        """Organiza os dados tratados nos modelos Pydantic canônicos."""
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
                operadores_contratados=metricas_req.get("operadores_contratados", 0),
                valor_cliente=metricas_req.get("valor_cliente", 0),
                rota_cliente=metricas_req.get("rota_cliente"),
            )

            return (
                empacotamento_callix.pacote_chamadas(),
                empacotamento_callix.pacote_agentes(),
            )
        except Exception as erro:
            self.log.erro(
                "Erro ao empacotar dados do cliente",
                erro=erro,
                cliente=cliente_formatado,
            )
            return None, None

    def coletar_clientes_paralelo(
        self, clientes_db: list[dict]
    ) -> tuple[list[dict], list[str]]:
        """Executa a extração HTTP paralela para clientes com token cadastrado."""
        resultados: list[dict] = []
        falhas: list[str] = []
        clientes_validos: list[dict] = []

        for cliente in clientes_db:
            if not cliente.get("token"):
                nome_cli = cliente.get("cliente") or "desconhecido"
                self.log.aviso(
                    "Cliente ignorado na coleta por ausência de token",
                    cliente=nome_cli,
                )
                falhas.append(f"{nome_cli}: sem token")
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
                        falhas.append(f"{cliente}: {resultado['erro']}")
                        continue
                    resultados.append(resultado)
                    self.log.etapa("Extração concluída", cliente=cliente)
                except Exception as erro:
                    falhas.append(f"{cliente}: {erro}")
                    self.log.erro(
                        "Erro inesperado na coleta do cliente",
                        erro=erro,
                        cliente=cliente,
                    )

        return resultados, falhas

    def _carregar_clientes_ativos(self) -> list[dict]:
        db_settings = self.settings.db if self.settings is not None else None
        with conexao_rivex(db_settings) as conn:
            db_clientes = DatabaseClientes(conexao_compartilhada=conn)
            return db_clientes.consultar_view()

    def executar(self, data: Optional[date] = None) -> ResumoExecucao:
        if data is not None:
            self.data_selecionada = data

        clientes_db = self._carregar_clientes_ativos()
        if not clientes_db:
            raise RuntimeError("Nenhum cliente ativo encontrado no banco.")

        self.log.inicio(
            "Iniciando coleta de clientes ativos",
            total_clientes=len(clientes_db),
            data=str(self.data_selecionada),
        )

        resultados, falhas = self.coletar_clientes_paralelo(clientes_db)

        self.log.etapa(
            "Extração concluída",
            coletados=len(resultados),
            total_clientes=len(clientes_db),
        )

        persistidos = 0
        db_settings = self.settings.db if self.settings is not None else None
        with conexao_rivex(db_settings) as conn:
            banco_callix = DatabaseCallix(conexao_compartilhada=conn)
            for resultado in resultados:
                cliente = resultado["cliente"]
                try:
                    dict_limpeza, metricas_req = self.limpar_dados(
                        resultado["dados_brutos_api"],
                        resultado["dados_brutos_req"],
                    )
                    if dict_limpeza is None or metricas_req is None:
                        falhas.append(f"{cliente}: falha na limpeza")
                        continue

                    dados_cliente, dados_agente = self.empacotar_dados(
                        dict_limpeza,
                        metricas_req,
                        cliente,
                    )
                    if dados_cliente is None or dados_agente is None:
                        falhas.append(f"{cliente}: falha no empacotamento")
                        continue

                    banco_callix.db_callix(dados_cliente, dados_agente)
                    persistidos += 1
                    self.log.etapa("Cliente processado e persistido", cliente=cliente)
                except Exception as erro:
                    falhas.append(f"{cliente}: {erro}")
                    self.log.erro(
                        "Erro no processamento do cliente",
                        erro=erro,
                        cliente=cliente,
                    )

        resumo = ResumoExecucao(
            pipeline=self.nome,
            total=len(clientes_db),
            persistidos=persistidos,
            falhas=falhas,
        )
        self.log.fim(
            "Pipeline Callix finalizada",
            total=resumo.total,
            persistidos=resumo.persistidos,
            falhas=len(resumo.falhas),
        )
        return resumo
