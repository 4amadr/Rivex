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
    dados = json_agentes

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

    raise ValueError("Cliente sem rota valida, retornando zero como valor padrão.")

def produtos_contratados(produto):
    return produto["webAccess"]["professional"]["units"]

def preco_produto(produto):
    return produto["webAccess"]["professional"]["unitPrice"]


def extrair_operadores_contratados(accounts: dict) -> dict:
    contas = accounts.get("data", [])

    if not contas:
        raise ValueError("Nenhuma conta encontrada no Callix.")

    attributes = contas[0].get("attributes", {})

    return {
        "operadores_contratados": attributes.get(
            "simultaneousWebAccessPaidQty"
        ),
        "valor_operador": attributes.get(
            "simultaneousWebAccessPrice"
        ),
    }


def limpar_agressividade(campanhas: dict) -> float:
    valores = [
        item.get("attributes", {}).get("powerAggressiveness")
        for item in campanhas.get("data", [])
        if item.get("attributes", {}).get(
            "powerAggressiveness"
        ) is not None
    ]

    return round(sum(valores) / len(valores), 2) if valores else 0.0


def extrair_historico_agressividade(audit_logs: dict) -> list:
    historico = []

    for registro in audit_logs.get("data", []):
        attributes = registro.get("attributes", {})
        alteracoes = attributes.get("propertiesChanged", {})

        serialized = alteracoes.get("$serialized", {})

        agressividade = serialized.get(
            "powerAggressiveness", {}
        )

        if not agressividade:
            agressividade = alteracoes.get(
                "powerAggressiveness", {}
            )

        valor = agressividade.get("value")

        if valor is not None:
            historico.append({
                "valor": valor,
                "data": attributes.get("createdAt"),
                "campanha": attributes.get("modelId"),
            })

    return historico


def mapear_rotas(outbound_routes: dict) -> dict:
    return {
        rota.get("id"): rota.get("attributes", {}).get("name")
        for rota in outbound_routes.get("data", [])
        if rota.get("id")
    }


def extrair_rota_real(chamadas_completas: dict, mapa_rotas: dict):
    rotas_utilizadas = []

    for chamada in chamadas_completas.get("data", []):
        attributes = chamada.get("attributes", {})

        for leg in attributes.get("legs", []):
            route_id = leg.get("routeId")

            if route_id in mapa_rotas:
                nome_rota = mapa_rotas[route_id]
                tech = _extrair_tech(nome_rota)

                rotas_utilizadas.append({
                    "route_id": route_id,
                    "rota": nome_rota,
                    "tech": tech,
                })

    return rotas_utilizadas


def extrair_tech_rotas(rotas_utilizadas: list):
    for rota in rotas_utilizadas:
        if rota.get("tech"):
            return rota["tech"]

    return None


def limpeza_req_callix(dados_brutos_req: dict) -> dict:
    accounts = dados_brutos_req.get("accounts") or {}
    campanhas = dados_brutos_req.get("campanhas") or {}
    audit_logs = dados_brutos_req.get("audit_logs") or {}
    outbound_routes = dados_brutos_req.get("outbound_routes") or {}
    chamadas_completas = dados_brutos_req.get("chamadas_completas") or {}
    user_performance_histories = (
        dados_brutos_req.get("user_performance_histories") or {}
    )

    agressividade = limpar_agressividade(campanhas)
    historico_agressividade = extrair_historico_agressividade(audit_logs)
    chamadas_agentes = limpar_chamadas_agentes(user_performance_histories)

    mapa_rotas = mapear_rotas(outbound_routes)
    rotas_utilizadas = extrair_rota_real(chamadas_completas, mapa_rotas)
    tech = extrair_tech_rotas(rotas_utilizadas)

    if tech is None:
        tech = limpeza_techs_callix(outbound_routes)

    operadores = (
        extrair_operadores_contratados(accounts)
        if accounts.get("data")
        else {"operadores_contratados": None, "valor_operador": None}
    )

    return {
        "agressividade": agressividade,
        "historico_agressividade": historico_agressividade,
        "chamadas_agentes": chamadas_agentes,
        "tech": tech,
        "rotas_utilizadas": rotas_utilizadas,
        "operadores_contratados": operadores["operadores_contratados"],
        "valor_operador": operadores["valor_operador"],
    }

    