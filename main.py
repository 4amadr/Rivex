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

def main_pentagono():
    execucao_pentagono = ExecucaoPentagono()
    execucao_pentagono.main_pentagono()
    
def main_ipbox():
   pipeline = PipelineIpbox()
   pipeline.executar()

def main_vonix():
    pipeline = PipelineVonix()
    pipeline.execucao_vonix()

def main_callix():
    pipeline_callix = PipelineCallix()
    pipeline_callix.executar()

def main_gerax():
    pipeline_gerax = ExecucaoGerax()
    pipeline_gerax.main_gerax()

def main_ultracom():
    pipeline_ultracom = PipelineUltracom()
    pipeline_ultracom.execucao_sippulse()

if __name__ == '__main__':
    dados_callix = main_callix()
    dados_ipbox = main_ipbox()
    dados_vonix = main_vonix()
    dados_gerax = main_gerax()
    dados_ultracom = main_ultracom()