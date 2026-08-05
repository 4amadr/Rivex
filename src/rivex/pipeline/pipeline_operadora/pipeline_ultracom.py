from src.rivex.enviroments.operadoras.ultracom.sippulse_scrap import SipPulseScrap
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.data_processing.ultracom.ultracon_cleaning import *
from dotenv import load_dotenv
import os

class PipelineUltracom:
    def __init__(self):
        self.usuario = os.getenv("ULTRACOM_LOGIN")
        self.senha = os.getenv("ULTRACOM_PASSWORD")
        self.url = os.getenv("ULTRACOM_URL")
        self.sip_scrap = SipPulseScrap(
            url_base=self.url,
            usuario=self.usuario,
            senha=self.senha,
            data=DateConfig.data_selecionadas()
        )

    def execucao(self):
        login, html_tarifadas, dados_monetarios = self.sip_scrap.execucao_sippulse()
        minutos = minutagem_pronta(dados_monetarios)
        custos = custos_prontos(dados_monetarios)
        return html_tarifadas, dados_monetarios

    def limpeza(self, html_tarifadas, html_relatorio):
        chamadas_tarifadas = obter_chamadas_tarifadas(html_tarifadas)
        minutos = minutagem_pronta(html_relatorio)
        custos = custos_prontos(html_relatorio)
        return chamadas_tarifadas, minutos, custos

    def execucao_sippulse(self):
        html_tarifadas, html_asr = self.execucao()
        chamadas_tarifadas, minutos, custos_prontos = self.limpeza(html_tarifadas, html_asr)



        