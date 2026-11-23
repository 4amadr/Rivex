from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from src.rivex.config.settings import Settings, carregar_settings
from src.rivex.database.database_indicadores import enviar_desempenho_pipeline
from src.rivex.domain.registros import PipelineProtocol, ResumoExecucao
from src.rivex.pipeline.pipeline_discador.pipeline_callix import PipelineCallix
from src.rivex.pipeline.pipeline_discador.pipeline_ipbox import PipelineIpbox
from src.rivex.pipeline.pipeline_discador.pipeline_vonix import PipelineVonix
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.infra_utils.execution_timer import CronometroPipelines
from src.rivex.utils.logging_config import PipelineLogger

log = PipelineLogger("executions")

PIPELINES: dict[str, type] = {
    "callix": PipelineCallix,
    "ipbox": PipelineIpbox,
    "vonix": PipelineVonix,
}


def _parse_data(valor: str) -> date:
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError as erro:
        raise argparse.ArgumentTypeError(
            f"Data inválida '{valor}'. Use o formato YYYY-MM-DD."
        ) from erro


def _executar_pipeline(
    nome: str,
    pipeline_cls: type,
    settings: Settings,
    data_ref: date,
) -> ResumoExecucao:
    pipeline: PipelineProtocol = pipeline_cls(settings=settings)
    log.inicio("Iniciando execução da pipeline", alvo=nome, data=str(data_ref))
    resumo = pipeline.executar(data=data_ref)
    log.fim(
        "Execução da pipeline finalizada",
        alvo=nome,
        total=resumo.total,
        persistidos=resumo.persistidos,
        falhas=len(resumo.falhas),
    )
    return resumo


def main() -> int:
    parser = argparse.ArgumentParser(description="Execução de pipelines ETL do Rivex")
    parser.add_argument(
        "--pipeline",
        required=True,
        choices=[*PIPELINES.keys(), "all"],
        help="Nome do discador a executar ou 'all' para executar todos",
    )
    parser.add_argument(
        "--data",
        type=_parse_data,
        default=None,
        help="Data de referência no formato YYYY-MM-DD (padrão: ontem)",
    )
    args = parser.parse_args()
    data_ref = args.data or DateConfig.ontem()

    settings = carregar_settings(args.pipeline)
    alvos = list(PIPELINES.keys()) if args.pipeline == "all" else [args.pipeline]

    cronometro = CronometroPipelines()

    houve_falha_critica = False
    for nome in alvos:
        pipeline_cls = PIPELINES[nome]
        try:
            with cronometro.medir_pipeline(nome):
                resumo = _executar_pipeline(nome, pipeline_cls, settings, data_ref)
            if len(resumo.falhas) > settings.max_falhas_pipeline or (
                resumo.total > 0 and resumo.persistidos == 0
            ):
                houve_falha_critica = True
        except Exception as error:
            houve_falha_critica = True
            log.erro("Erro durante a execução da pipeline", erro=error, alvo=nome)
            continue

    tempos = cronometro.obter_tempos()
    total_segundos = cronometro.tempo_total
    log.fim(
        "Tempo de execução consolidado das pipelines",
        data=str(data_ref),
        tempos=tempos,
        total_segundos=total_segundos,
    )

    db_settings = getattr(settings, "db", None)
    if tempos and db_settings is not None:
        try:
            enviar_desempenho_pipeline(
                data_ref=data_ref,
                tempos_pipelines=tempos,
                total=total_segundos,
                db_settings=db_settings,
            )
        except Exception as error:
            log.erro(
                "Erro ao persistir desempenho das pipelines",
                erro=error,
                data=str(data_ref),
            )

    return 1 if houve_falha_critica else 0


if __name__ == "__main__":
    sys.exit(main())
