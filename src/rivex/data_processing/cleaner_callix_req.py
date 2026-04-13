import pandas as pd
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition

'''
Modulo para limpar os dados que vem de requisições do callix.
Aqui serão limpos:
1 - Dados coletados via requests, sem API
2 - Dados coletados em fontes do callix que não tem documentação explicita
3 - Dados que não estão contidos no resultado da API
'''

def limpar_chamadas_agentes(response):
    dados = response.json()

    usuarios = {
        user["id"]: user["attributes"]["name"]
        for user in dados["included"]
        if user["type"] == "users"
    }

    resultado = [
        {
            "agente": usuarios.get(item["relationships"]["user"]["data"]["id"], "Desconhecido"),
            "chamadas_atendidas": item["attributes"]["answeredCount"]
        }
        for item in dados["data"]
    ]

    return resultado

def limpar_agressividade(response):
    dados = response.json()
    atributos = dados["data"]["attributes"]

    return {
        "campanha": atributos["name"],
        "agressividade": atributos["powerAggressiveness"]
    }
    