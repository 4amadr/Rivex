from dis import print_instructions
import pandas as pd
from src.rivex.enviroments.discadores.Callix.callix_req import CAllixRequisition
from collections import namedtuple

'''
Modulo para limpar os dados que vem de requisições do callix.
Aqui serão limpos:
1 - Dados coletados via requests, sem API
2 - Dados coletados em fontes do callix que não tem documentação explicita
3 - Dados que não estão contidos no resultado da API
'''
AgenteData = namedtuple(
    "AgenteData",
    []    
)


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
            "Chamadas atendidas": item["attributes"]["answeredCount"]
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

def  limpeza_techs_callix(techs_json):
    '''
    Vai isolar o valor da tech de um arquivo json
    '''
    data_json = techs_json['included']
    for dados in data_json:
        tech_suja = dados['attributes']['name']
    print("TECH COMPLETA DO CLIENTE ATUAL: ",tech_suja)
    return tech_suja
        
def tech_limpa_callix(tech_suja):
    '''Vai retornar
    *tech*
    *ID*
    *Fila*
    '''
    numeracao = "".join(caractere for caractere in tech_suja if caractere.isdigit())
    print("NUMERAÇÃO DE IDENTIFICADOR: ",numeracao)
    
    dict_info = {
        "Tech": numeracao[:6],
        "Id": numeracao[:4],
        "Fila": numeracao[1:3]
    }
    print("INFORMAÇÕES DO CLIENTE SELECIONADO: ",dict_info)
    return dict_info

def limpeza_req_callix(json_agressividade, json_agentes, techs_json):
    tech_suja = limpeza_techs_callix(techs_json)
    return limpar_agressividade(json_agressividade), limpar_chamadas_agentes(json_agentes), tech_limpa_callix(tech_suja)
    