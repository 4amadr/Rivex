from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.operadoras.pentagono.pentagono_scrap import *
from src.rivex.data_processing.pentagono.pentagono_cleaning import *
from src.rivex.utils.infra_utils.date_config import *
from src.rivex.database.database import *
from dotenv import load_dotenv
import os

class ExecucaoGerax:
    def __init__(self):
        self.dc = DateConfig()
        self.data = self.dc.data_selecionadas()
        self.db = DatabaseGerax()
        self.ps = pentagonoScrap(
        usuario=os.getenv('GERAX_URL'),
        senha=os.getenv('GERAX_PASSWORD'),
        data=self.data,
        url_base=os.getenv('GERAX_URL')
        )


    def main_gerax(self):
        # Coleta
        login, pagina_inicial, relatorio_html = self.ps.execucao_pentagono()
        
        # limpeza
        dados = execucao_limpeza(relatorio_html)

        # empacotamento
        for dado in dados:
            dict_dados_pentagono = {
                "tech": dado["Cliente ID"],
                "data": self.dc.data_callix(),
                "custo": dado["Custos"],
                "minutagem": dado["Minutagem"],
                "chamadas_tarifadas": dado["Chamadas tarifadas"]
        }   
            print("Dados que serão enviados")
            print(dict_dados_pentagono)
            self.db.enviar_dados_db_gerax(dict_dados_pentagono)
        self.db.fechar_db_telefonia()
