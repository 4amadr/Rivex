import urllib.parse

def payload_callix(requisicao, data, filtro=None, set=None):
    if requisicao == "campaign":
        querystring = None
        
    elif requisicao == "user_performance_reports":
        querystring = {
            "filter[date]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z"
        }
        
    else:
        querystring = {
            "filter[started_at]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z",
        }
        
    if filtro:
        querystring = {
            "filter[started_at]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z",
            filtro: set
        }
        
    return querystring

def payload_login_callix(login_ambiente, password):
    payload = {"username": login_ambiente, "password": password}
    return payload

def headers_callix(token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    return headers

def headers_login_callix(BASE_URL):
    headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/login",
    "X-Api": "1, 1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
}
    return headers

def payload_de_requisicao_de_chamadas(data):
    return {
        "sort": "-date",
        "filter": f"(:and,(date,:gte,`{data}`),(date,:lte,`{data}`))",  # parênteses externos
        "fields[userPerformanceHistories]": "user.id,user.name",
        "page[limit]": 100,
    }

def get_performance_headers(token: str, url) -> dict:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "referer": url,
        "x-api": "1, 1",
        "x-timezone": "America/Sao_Paulo",
        "cookie": f"token={token}",
    }
    
def payload_agressividade():
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
        "fields[nationalTenantRoute]": "name,requiresCallerId",
        "fields[nationalOutboundRouteType]": "name,type",
        "fields[teams]": "name",
        "fields[agentGroups]": "name",
        "fields[campaignModel]": "name",
        "fields[campaignModel.fields]": "name",
        "fields[customerForm]": "name",
        "fields[successQualificationGroup]": "name",
        "fields[discardQualificationGroup]": "name",
        "fields[timeZone]": "name",
        "fields[survey]": "name",
        "fields[outboundBlacklists]": "name",
        "fields[nationalInboundNumberAsCallerId]": "phone",
        "fields[goals.qualifications]": "name",
        "fields[supervisionGroup]": "name",
        "fields[nonWorkingDaysCalendars]": "name",
        "fields[voiceMessageExternalSipServer]": "name",
        "fields[aiAgentAssistant]": "name",
        "fields[ivrOptions.qualification]": "name",
        "fields[ivrOptions.chatOutboundTemplate]": "name,status",
        "fields[ivrOptions.workflow]": "name",
        "fields[ivrOptions.chatInteractionQueue]": "name",
        "fields[ivrOptions.chatInboundNumber]": "phone",
        "fields[ivrOptions.externalSipServer]": "name",
        "fields[ivrSound]": "name",
        "fields[ivrQueueSound]": "name",
        "fields[ivrQueueEndSound]": "name",
        "fields[transferTeams]": "name",
        "fields[transferIvrs]": "name",
        "fields[transferCallQueues]": "name",
        "fields[onHoldSound]": "name",
        "fields[customerSegmentation]": "name",
        "fields[transferSuccessQualificationGroup]": "name",
        "fields[transferDiscardQualificationGroup]": "name",
    }

def payload_servidor_callix():
    return {
        "filter": "(status,:in,[`3`])",
        "page[limit]": "100"
    }

def payload_techs_callix():
    return {
        "include": "callProviderServer.callProvider",
        "sort": "name",
        "filter": "(archived%2C%3Aeq%2C%60false%60)(tenantOwner.id%2C%3Ain%2C%5B%6011278%60%2C%6011279%60%2C%6011755%60%2C%6011843%60%2C%6011851%60%2C%6011860%60%2C%6011907%60%2C%6011924%60%2C%6012467%60%2C%6012569%60%2C%6012700%60%2C%6012728%60%2C%6012832%60%2C%6012964%60%2C%6012999%60%2C%6013034%60%2C%6013166%60%2C%6013287%60%2C%6013431%60%2C%6013569%60%2C%6013663%60%2C%6013693%60%2C%6013705%60%2C%6013716%60%2C%6013734%60%2C%6013805%60%2C%6013978%60%2C%6013989%60%2C%6014007%60%2C%6014031%60%2C%6014069%60%2C%6014122%60%2C%6014138%60%2C%6014146%60%2C%6014156%60%2C%6014249%60%2C%6014263%60%2C%6014438%60%2C%6014450%60%2C%6014544%60%2C%6014589%60%2C%6014615%60%2C%6014646%60%2C%6014665%60%2C%6014667%60%2C%6014698%60%2C%6014710%60%2C%6014777%60%2C%6014788%60%2C%6014809%60%2C%6014820%60%2C%6014900%60%2C%6014908%60%2C%6014918%60%2C%6014940%60%2C%6014982%60%2C%6015024%60%2C%6015039%60%2C%6015076%60%2C%6015116%60%2C%6015180%60%2C%6015184%60%2C%6015193%60%2C%6015225%60%2C%6015244%60%2C%6015253%60%2C%6015281%60%2C%6015319%60%2C%6015373%60%2C%6015381%60%2C%6015383%60%2C%6015409%60%2C%6015411%60%2C%6015458%60%2C%6015469%60%2C%6015477%60%2C%6015481%60%2C%6015482%60%2C%6015519%60%2C%6015536%60%2C%6015540%60%2C%6015547%60%2C%6015614%60%2C%6015627%60%2C%6015648%60%2C%6015690%60%2C%6015721%60%2C%6015724%60%2C%6015727%60%2C%6015728%60%2C%6015729%60%2C%6015733%60%2C%6015736%60%2C%6015754%60%2C%6015764%60%2C%6015773%60%2C%6015776%60%2C%6015793%60%2C%6015803%60%2C%6015808%60%2C%6015814%60%2C%6015817%60%2C%6015826%60%2C%6015840%60%2C%6015855%60%2C%6015860%60%2C%6015861%60%2C%6015864%60%2C%6015866%60%2C%6015875%60%2C%6015887%60%2C%6015893%60%2C%6015897%60%2C%6015899%60%2C%6015902%60%2C%6015907%60%2C%6015917%60%2C%6015926%60%2C%6015927%60%2C%6015930%60%2C%6015932%60%2C%6015933%60%2C%6015935%60%2C%6015936%60%2C%6015943%60%2C%6015945%60%2C%6015948%60%2C%6015953%60%2C%6015954%60%2C%6016042%60%2C%6016045%60%2C%6016053%60%2C%6016054%60%2C%6016055%60%2C%6016057%60%2C%6016058%60%2C%6016063%60%2C%6016077%60%2C%6016078%60%2C%6016083%60%2C%6016086%60%2C%6016094%60%2C%6016097%60%2C%6016098%60%2C%6016106%60%2C%6016107%60%2C%6016129%60%2C%6016130%60%2C%6016139%60%2C%6016144%60%2C%6016169%60%2C%6016184%60%2C%6016209%60%2C%6016224%60%2C%6016235%60%2C%6016237%60%2C%6016249%60%2C%6016251%60%2C%6016255%60%2C%6016261%60%2C%6016262%60%2C%6016267%60%2C%6016273%60%2C%6016288%60%2C%6016289%60%2C%6016298%60%2C%6016308%60%2C%6016309%60%2C%6016317%60%2C%6011038%60%5D)",
        "fields%5BoutboundRoutes%5D": "name%2CcallProviderServer%2CtenantOwner%2CtechPrefix%2CsipUser%2Cenabled%2CallowInternationalCalls%2ClocalAreaCode%2Cmode",
        "page%5Blimit%5D": "100"
    }

def headers_servidor_callix():
    return {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }