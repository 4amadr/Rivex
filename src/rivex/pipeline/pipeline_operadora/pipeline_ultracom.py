from src.rivex.enviroments.operadoras.ultracom.sippulse_scrap import SipPulseScrap
from src.rivex.utils.infra_utils.date_config import DateConfig
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
        login = self.sip_scrap.execucao_ultracom()
        return login
        