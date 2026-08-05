import os
import time
import requests
from dotenv import load_dotenv
from src.rivex.enviroments.discadores.Callix.callix import CallixAPICollector
from src.rivex.enviroments.discadores.Callix.callix_token_db import CallixDB
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
from src.rivex.utils.csv_utils.callix_csv.callix_converter import CallixCSVConverter
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.data_processing.Callix.cleaner_callix_req import *
from src.rivex.utils.database_utils.database_config import DatabaseConfig
from src.rivex.enviroments.operadoras.gsolutions.sip_client_scrap import *
from src.rivex.data_processing.gsolutions.cleaner_sip import *
from dotenv import load_dotenv
from src.rivex.data_processing.pentagono.pentagono_cleaning import *
from src.rivex.enviroments.discadores.IPBox.colect_ipbox import *
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *
from src.rivex.pipeline.pipeline_operadora.pipeline_pentagono import *
import logging
from src.rivex.pipeline.pipeline_discador.pipeline_ipbox import *
from src.rivex.pipeline.pipeline_discador.pipeline_callix import *
from src.rivex.pipeline.pipeline_operadora.pipeline_agitel import *
from src.rivex.pipeline.pipeline_discador.pipeline_vonix import *
from src.rivex.pipeline.pipeline_operadora.pipeline_gerax import *
from src.rivex.pipeline.pipeline_operadora.pipeline_ultracom import *
load_dotenv()
logger = logging.getLogger(__name__)
    
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



exec_ipbox = main_ipbox()
dados_vonix = main_vonix()
dados_callix = main_callix()
dados_gerax = main_gerax()
dados_ultracom = main_ultracom()


# operadoras inativas
#exec_agitel = main_agitel()
#exec_gs = main_gs()
#exec_pentagono = main_pentagono()

