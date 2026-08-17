from dis import print_instructions
import pandas as pd
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from collections import namedtuple
import unicodedata
import re

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

    return media

def _normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    
    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    ).lower()

def _rota_valida(name: str) -> bool:
    """
    Verifica se a rota pode ser utilizada para extrair a Tech.

    Rotas contendo #Geral, Manual ou MaximaVoip são ignoradas.
    """
    nome = _normalizar_texto(name)

    termos_ignorados = (
        "#geral",
        "manual",
        "maximavoip",
    )

    return not any(termo in nome for termo in termos_ignorados)

def _extrair_tech(name: str) -> str | None:
    """
    Extrai o valor da Tech presente no nome da rota.

    Exemplo:
        '1036#01 - Pentagono (Tech: 103601)'
        -> '103601'
    """
    match = re.search(r"\(Tech:\s*(\d+)\)", name)

    if match:
        return match.group(1)

    return None

def limpeza_techs_callix(outbound_routes: dict) -> str:
    """
    Recebe o JSON de outbound-routes e retorna a Tech
    apropriada para ser enviada ao banco de dados.
    """
    for rota in outbound_routes.get("data", []):

        attributes = rota.get("attributes", {})
        name = attributes.get("name", "")

        if not _rota_valida(name):
            continue

        tech = _extrair_tech(name)

        if tech:
            return tech

    raise ValueError("Nenhuma Tech válida foi encontrada no JSON.")



def limpeza_req_callix(json_agressividade, json_agentes, techs_json):

    return limpar_agressividade(json_agressividade), limpar_chamadas_agentes(json_agentes), limpeza_techs_callix(techs_json.json())
    