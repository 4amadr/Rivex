import pandas as pd
from src.automations.gsolutions.gsolutions_scrap import SipClient

class GsolutionsCleaner:
    def selecionar_dabelas(self):
        gs = SipClient()
        html = gs.execucao_gsolutions(data_selecionada='23/12/2025')
