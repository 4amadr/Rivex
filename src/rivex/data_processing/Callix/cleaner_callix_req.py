import logging
import re
import unicodedata

log = logging.getLogger(__name__)


def limpar_chamadas_agentes(json_agentes: dict) -> list[dict]:
    if "included" not in json_agentes:
        log.debug("Sem dados de agentes na resposta da API")
        return []

    usuarios = {
        user["id"]: user.get("attributes", {}).get("name", "Desconhecido")
        for user in json_agentes["included"]
        if user.get("type") == "users" and "id" in user
    }

    if not usuarios:
        log.debug("Nenhum usuario encontrado em included")
        return []

    resultado = []
    for item in json_agentes.get("data", []):
        user_data = (
            (item.get("relationships") or {}).get("user") or {}
        ).get("data") or {}
        user_id = user_data.get("id")
        answered = (item.get("attributes") or {}).get("answeredCount", 0)
        resultado.append({
            "agente": usuarios.get(user_id, "Desconhecido"),
            "Chamadas atendidas": answered,
        })

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
    termos_ignorados = ("#geral", "manual", "maximavoip")
    return not any(termo in nome for termo in termos_ignorados)


def _extrair_tech(name: str) -> str | None:
    """
    Extrai o valor da Tech presente no nome da rota.

    Exemplo:
        '1036#01 - Pentagono (Tech: 103601)' -> '103601'
    """
    match = re.search(r"\(Tech:\s*(\d+)\)", name)
    return match.group(1) if match else None


def limpeza_techs_callix(outbound_routes: dict) -> str:
    """Extrai a Tech da primeira rota válida em outbound-routes."""
    for rota in outbound_routes.get("data", []):
        name = rota.get("attributes", {}).get("name", "")
        if not _rota_valida(name):
            continue

        tech = _extrair_tech(name)
        if tech:
            return tech

    raise ValueError("Cliente sem rota válida para extração de Tech.")


def extrair_operadores_contratados(accounts: dict) -> dict:
    contas = accounts.get("data", [])
    if not contas:
        raise ValueError("Nenhuma conta encontrada no Callix.")

    attributes = contas[0].get("attributes", {})
    return {
        "operadores_contratados": attributes.get("simultaneousWebAccessPaidQty"),
        "valor_operador": attributes.get("simultaneousWebAccessPrice"),
    }


def limpar_agressividade(campanhas: dict) -> float:
    valores = [
        item.get("attributes", {}).get("powerAggressiveness")
        for item in campanhas.get("data", [])
        if item.get("attributes", {}).get("powerAggressiveness") is not None
    ]
    return round(sum(valores) / len(valores), 2) if valores else 0.0


def extrair_historico_agressividade(audit_logs: dict) -> list:
    historico = []

    for registro in audit_logs.get("data", []):
        attributes = registro.get("attributes", {})
        alteracoes = attributes.get("propertiesChanged", {})
        serialized = alteracoes.get("$serialized", {})

        agressividade = serialized.get("powerAggressiveness", {})
        if not agressividade:
            agressividade = alteracoes.get("powerAggressiveness", {})

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


def extrair_rota_real(chamadas_completas: dict, mapa_rotas: dict) -> list[dict]:
    rotas_utilizadas = []

    for chamada in chamadas_completas.get("data", []):
        attributes = chamada.get("attributes", {})
        for leg in attributes.get("legs", []):
            route_id = leg.get("routeId")
            if route_id in mapa_rotas:
                nome_rota = mapa_rotas[route_id]
                rotas_utilizadas.append({
                    "route_id": route_id,
                    "rota": nome_rota,
                    "tech": _extrair_tech(nome_rota),
                })

    return rotas_utilizadas


def extrair_tech_rotas(rotas_utilizadas: list) -> str | None:
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
