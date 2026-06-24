from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.operadoras.pentagono.pentagono_scrap import *
from src.rivex.data_processing.pentagono.pentagono_cleaning import *
from dotenv import load_dotenv
import os

class ExecucaoPentagono:
    def __init__(self):
        pass
    def main_pentagono(self):
        dc = DateConfig()
        data = dc.data_selecionadas()
        
        ps = pentagonoScrap(
        usuario=os.getenv('PENTAGONO_LOGIN'),
        senha=os.getenv('PENTAGONO_PASSWORD'),
        data=data
        )
        
        # execução e coleta de dados sujos em formato HTML
        login, pagina_inicial, relatorio_html = ps.execucao_pentagono()
        
        # limpeza de dados
        dados = execucao_limpeza(relatorio_html)
        print(dados)