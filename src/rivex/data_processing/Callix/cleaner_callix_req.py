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

    # se não houver "included", não há agentes para processar
    if "included" not in dados:
        print("Sem dados de agentes na resposta da API")
        return []

    usuarios = {
        user["id"]: user["attributes"]["name"]
        for user in dados["included"]
        if user["type"] == "users"
    }

    if not usuarios:
        print("Sem dados")
        return []

    resultado = [
        {
            "agente": usuarios.get(item["relationships"]["user"]["data"]["id"], "Desconhecido"),
            "chamadas_atendidas": item["attributes"]["answeredCount"]
        }
        for item in dados["data"]
    ]

    return resultado

def limpar_agressividade(json_agressividade): # por enquanto vai retornar a media de agressividade 
    lista_agressividade = []
    
    for agressividade in json_agressividade:
        dados = agressividade.json()
        atributos = dados["data"]["attributes"]
        lista_agressividade.append(atributos["powerAggressiveness"])

    media = round(sum(lista_agressividade) / len(lista_agressividade), 2) if lista_agressividade else 0.0

    return {"agressividade": media}


def agressividade_e_agentes(json_agressividade, json_agentes):
    return limpar_agressividade(json_agressividade), limpar_chamadas_agentes(json_agentes)
    