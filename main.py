import argparse

from src.rivex.pipeline.pipeline_discador.pipeline_callix import PipelineCallix
from src.rivex.pipeline.pipeline_discador.pipeline_ipbox import PipelineIpbox    
from src.rivex.pipeline.pipeline_discador.pipeline_vonix import PipelineVonix
from src.rivex.pipeline.pipeline_operadora.pipeline_agitel import ExecAgitel
from src.rivex.pipeline.pipeline_operadora.pipeline_gerax import ExecucaoGerax
from src.rivex.pipeline.pipeline_operadora.pipeline_pentagono import ExecucaoPentagono
from src.rivex.pipeline.pipeline_operadora.pipeline_ultracom import PipelineUltracom


def main_agitel():
    execucao = ExecAgitel()
    execucao.pipeline_agitel()
    
def main_ipbox():
   pipeline = PipelineIpbox()
   pipeline.executar()

def main_vonix():
    pipeline = PipelineVonix()
    pipeline.execucao_vonix()

def main_callix():
    pipeline_callix = PipelineCallix()
    pipeline_callix.executar()


PIPELINES = {
    "callix": main_callix,
    "agitel": main_agitel,
    "ipbox": main_ipbox,
    "vonix": main_vonix,

}

def main():
    parser = argparse.ArgumentParser(description='Execução de pipelines')

    parser.add_argument(
        "--pipeline",
        required=True,
        choises=PIPELINES.keys(),
        help="Pipeline executado"
    )

    args = parser.parse_args()

    pipeline = PIPELINES[args.pipeline]

    return pipeline()

if __name__ == "__main__":
    main()
