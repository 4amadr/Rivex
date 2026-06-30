from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.enviroments.operadoras.pentagono.pentagono_scrap import *
from src.rivex.data_processing.pentagono.pentagono_cleaning import *
from src.rivex.utils.infra_utils.date_config import *
from src.rivex.database.database import *
from dotenv import load_dotenv
import os

class ExecucaoPentagono:
    def __init__(self):
        pass
    def main_pentagono(self):
        dc = DateConfig()
        data = dc.data_selecionadas()
        db = DatabaseRivex()
        
        ps = pentagonoScrap(
        usuario=os.getenv('PENTAGONO_LOGIN'),
        senha=os.getenv('PENTAGONO_PASSWORD'),
        data=data
        )
        
        # Coleta
        login, pagina_inicial, relatorio_html = ps.execucao_pentagono()
        
        # limpeza
        dados = execucao_limpeza(relatorio_html)

        print("Abrindo banco de dados")
        cursor, conexao = db.abrir_banco()

        # empacotamento
        lista_dados_empacotados = []
        for dado in dados:
            dict_dados_pentagono = {
                "tech": dado["Cliente ID"],
                "cliente": None,
                "operadora": "Pentágono",
                "data": dc.data_callix(),
                "custo": dado["Custos"],
                "minutagem": dado["Minutagem"],
                "chamadas_tarifadas": dado["Chamadas tarifadas"]
        }   
            print("Dados que serão enviados")
            print(dict_dados_pentagono)
            db.enviar_banco_operadoras(dict_dados_pentagono, cursor)
        print("Fechando o banco de dados")
        db.fechar_db(cursor, conexao)
