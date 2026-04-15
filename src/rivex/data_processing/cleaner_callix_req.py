import pandas as pd
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition

'''
Modulo para limpar os dados que vem de requisições do callix.
Aqui serão limpos:
1 - Dados coletados via requests, sem API
2 - Dados coletados em fontes do callix que não tem documentação explicita
3 - Dados que não estão contidos no resultado da API
'''

def limpar_chamadas_agentes(json_agentes):
    dados = json_agentes.json()

    usuarios = {
        user["id"]: user["attributes"]["name"]
        for user in dados["included"]
        if user["type"] == "users"
    }
    if not usuarios:
        print("Sem dados")
        return None

    resultado = [
        {
            "agente": usuarios.get(item["relationships"]["user"]["data"]["id"], "Desconhecido"),
            "chamadas_atendidas": item["attributes"]["answeredCount"]
        }
        for item in dados["data"]
    ]

    return resultado

def limpar_agressividade(json_agressividade): # json_agressividade é uma lista
    lista_agressividade = []
    
    for agressividade in json_agressividade:
        dados = agressividade.json()
        atributos = dados["data"]["attributes"]
        lista_agressividade.append(atributos["powerAggressiveness"])

    return {
        "agressividade": lista_agressividade
    }
    
def agressividade_e_agentes(json_agressividade, json_agentes):
    return limpar_chamadas_agentes(json_agentes), limpar_agressividade(json_agressividade)
    