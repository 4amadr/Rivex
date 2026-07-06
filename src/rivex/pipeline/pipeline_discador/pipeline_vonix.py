from src.rivex.enviroments.discadores.vonix.fluxo_coleta import *
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import *
from src.rivex.data_processing.Vonix.cleaning_vonix import *
import os
from dotenv import load_dotenv

class PipelineVonix:
    def __init__(self):
        load_dotenv()
        self.data = DateConfig()
        self.login = os.getenv('LOGIN_VONIX')
        self.senha = os.getenv('SENHA_VONIX')
        self.url = os.getenv('URL_BASE_VONIX6')

    def inicial_config(self):
        vonix_execucao = ExecucaoVonix(
            login=self.login,
            senha=self.senha,
            data=self.data,
            url_base=self.url
        )

        token_encontrado = vonix_execucao.execucao_vonix()
        html_token = get_html(token_encontrado)
        return get_token(html_token)

        
