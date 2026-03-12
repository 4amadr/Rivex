def payload_request(requisicao, data, filtro):
    if requisicao == "user_performance_reports":
        querystring = {
            "filter[date]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z"
        }
    else:
        querystring = {
            "filter[started_at]": f"{data}T00:00:00.000Z,{data}T23:59:59.999Z",
        }
    print("Querystring enviada:", querystring)
    
    if filtro:
        querystring.update(filtro)
        
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

def params_para_agressividade(data):
    params = {
            "sorting": "-createdAt",
            "createdAt": f"{data},{data}",
            "page[limit]": 100,
            "page[offset]": 0
        }
    return params
