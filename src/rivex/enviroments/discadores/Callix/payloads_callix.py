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