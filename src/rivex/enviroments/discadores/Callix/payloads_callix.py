class PayloadsCallix:
    def payload_request(requisicao):
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
            
class HeadersCallix:
    def headers_callix(token):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        return headers