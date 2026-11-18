def headers_callix(token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def payload_de_requisicao_de_chamadas(data: str) -> dict:
    return {
        "sort": "-date",
        "filter": f"(:and,(date,:gte,`{data}`),(date,:lte,`{data}`))",
        "fields[userPerformanceHistories]": "user.id,user.name",
        "page[limit]": 100,
    }


def payload_get_tech() -> dict:
    return {
        "filter": "(archived,:eq,`false`)",
        "page[limit]": 2000,
        "fields[outboundRoutes]": "name,enabled,archived",
    }


def payload_resumo_campanha(data: str) -> dict:
    return {
        "filter[date]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z",
        "grouping": "day",
    }


def headers_v4_sessao(user_session_token: str) -> dict:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api": "1, 1",
        "x-timezone": "America/Sao_Paulo",
        "cookie": f"token={user_session_token}",
    }


def payload_campanhas_v4() -> dict:
    return {
        "page[limit]": 100,
        "fields[campaigns]": (
            "name,status,type,flavour,"
            "powerAggressiveness,lastRunningAt"
        ),
    }


def payload_audit_campanhas() -> dict:
    return {
        "filter": "(modelName,:eq,`Campaign`)",
        "page[limit]": 200,
        "sort": "-createdAt",
    }


def payload_rotas_chamadas_v4(data_inicio_iso: str) -> dict:
    return {
        "filter": f"(startedAt,:gte,`{data_inicio_iso}`)",
        "fields[campaignCompletedCalls]": "legs,startedAt",
        "page[limit]": 100,
        "sort": "-startedAt",
    }
