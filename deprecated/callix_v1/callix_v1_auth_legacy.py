"""
Código legado / bloqueado da integração Callix v1 (login via /api/v4/auth/session
com captchaToken, criação/listagem de api-tokens e endpoints legados de campanha/rota).

Desativado devido ao bloqueio de reCAPTCHA pela Callix (401: Recaptcha is needed).
"""


class UrlGetClientsLegacy:
    def __init__(self, url_contech: str):
        self.url_contech = url_contech

    def url_sub_accounts_v1(self):
        return f"{self.url_contech}/api/v1/sub_accounts"


def login_cliente_header(cliente: str) -> str:
    return f"https://{cliente}.callix.com.br/login"


def login_cliente(cliente: str) -> str:
    return f"https://{cliente}.callix.com.br/api/v4/auth/session"


def url_tokens(cliente: str) -> str:
    return f"https://{cliente}.callix.com.br/api/v4/entities/api-tokens"


def url_create_tokens(cliente: str) -> str:
    return f"https://{cliente}.callix.com.br/api/v4/entities/api-tokens"


def url_get_tech(cliente: str) -> str:
    return f"https://{cliente}.callix.com.br/api/v4/entities/outbound-routes"


def url_agressividade(cliente: str, id_campanha: list) -> list[str]:
    return [
        f"https://{cliente}.callix.com.br/api/v4/entities/campaigns/{campanha}"
        for campanha in id_campanha
    ]


def payload_login_callix(login_ambiente: str, password: str, token: str) -> dict:
    return {"username": login_ambiente, "password": password, "captchaToken": token}


def headers_login_callix(base_url: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": base_url,
        "Referer": base_url,
        "X-Api": "1, 1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
    }


def payload_servidor_callix() -> dict:
    return {"page[limit]": "2000"}


def payload_get_tokens() -> dict:
    return {
        "sort": "token",
        "fields%5BapiTokens%5D": "token%2CaccessProfile%2CcreatedAt",
        "page%5Blimit%5D": "100",
    }


def payload_create_tokens() -> dict:
    return {
        "data": {
            "type": "apiTokens",
            "attributes": {},
            "relationships": {
                "accessProfile": {
                    "data": {
                        "id": "3",
                        "type": "accessProfiles",
                    }
                }
            },
        }
    }


def gerar_headers_para_tokens(token: str, cliente: str) -> dict:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": f"token={token}",
        "referer": f"https://{cliente}.callix.com.br/api-tokens",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "x-api": "1",
        "x-timezone": "America/Sao_Paulo",
    }


def payload_agressividade() -> dict:
    return {
        "include": (
            "teams,agentGroups,campaignModel,campaignModel.fields,customerForm,"
            "customerSegmentation,successQualificationGroup,discardQualificationGroup,"
            "timeZone,survey,outboundBlacklists,workingHours,nationalTenantRoute,"
            "nationalOutboundRouteType,nationalInboundNumberAsCallerId,goals.qualifications,"
            "supervisionGroup,nonWorkingDaysCalendars,voiceMessageExternalSipServer,"
            "aiAgentAssistant,ivrOptions.qualification,ivrOptions.chatOutboundTemplate,"
            "ivrOptions.workflow,ivrOptions.chatInteractionQueue,ivrOptions.chatInboundNumber,"
            "ivrOptions.externalSipServer,ivrSound,ivrQueueSound,ivrQueueEndSound,"
            "callNotificationSound,transferTeams,transferIvrs,transferCallQueues,"
            "workingHourExceptions,onHoldSound,transferSuccessQualificationGroup,"
            "transferDiscardQualificationGroup"
        ),
    }


def login_callix_legacy(http_request, login: str, senha: str, captcha_token: str, cliente: str) -> str:
    resp = http_request.requisicao_post_json(
        payload_post=payload_login_callix(login, senha, captcha_token),
        headers=headers_login_callix(login_cliente_header(cliente)),
        url=login_cliente(cliente),
    )
    return resp.json()["token"]
