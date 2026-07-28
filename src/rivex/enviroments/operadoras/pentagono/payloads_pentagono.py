def payload_login_pentagono(login, senha):
    payload_login = {
        'action': 'login',
        'username': f'{login}',
        'password': f'{senha}',
    }
    return payload_login

def headers_pentagono():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://plataforma7.geraxtelecom.com.br/security/login",
        "Origin": "https://plataforma7.geraxtelecom.com.br",
    }

def payloads_relatorio(data):
    return {
        "DATAI_TMP": data,
        "DATAF_TMP": data,
        "SORT_DIRECTION": "DESC",
        "SORT_CHANGE": "",
        "SORT_TAG": "data_index",
        "PAGE": "1",
        "txtDataI": data,
        "txtDataF": data,
        "txtTipo": "0",
        "txtFiltro": "",
    }
