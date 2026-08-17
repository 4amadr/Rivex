from src.rivex.environments.operadoras.ultracom.sippulse_scrap import SipPulseScrap
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.data_processing.ultracom.ultracon_cleaning import *
from src.rivex.database.database_dados_chamadas import DatabaseUltracom
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)

class PipelineUltracom:
    def __init__(self):
        self.usuario = os.getenv("ULTRACOM_LOGIN")
        self.senha = os.getenv("ULTRACOM_PASSWORD")
        self.url = os.getenv("ULTRACOM_URL")
        self.data = DateConfig.data_selecionadas()
        self.sip_scrap = SipPulseScrap(
            url_base=self.url,
            usuario=self.usuario,
            senha=self.senha,
            data=self.data
        )
        self.db = DatabaseUltracom()

    def execucao(self):
        login, html_tarifadas, dados_monetarios = self.sip_scrap.execucao_sippulse()
        return html_tarifadas, dados_monetarios

    def limpeza(self, html_tarifadas, html_relatorio):
        chamadas_tarifadas = obter_chamadas_tarifadas(html_tarifadas)
        minutos = minutagem_pronta(html_relatorio)
        custos = custos_prontos(html_relatorio)

        return {
            "data": self.data,
            "custo": custos,
            "minutagem": minutos,
            "chamadas_tarifadas": chamadas_tarifadas
        }
    

    def execucao_sippulse(self):
        html_tarifadas, html_asr = self.execucao()
        dict_dados = self.limpeza(html_tarifadas, html_asr)
        logger.info(f"[DADOS ULTRACON] enviados para o DB {dict_dados}")
        self.db.enviar_dados_db_ultracon(dict_dados)
        self.db.fechar_db_telefonia()




        