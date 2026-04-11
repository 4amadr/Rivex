import pandas as pd
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition

'''
Modulo para limpar os dados que vem de requisições do callix.
Aqui serão limpos:
1 - Dados coletados via requests, sem API
2 - Dados coletados em fontes do callix que não tem documentação explicita
3 - Dados que não estão contidos no resultado da API
'''

def limpeza_chamadas_por_agentes(json_de_dados_dos_agentes):
    