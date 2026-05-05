def payload_login_pentagono(login, senha):
    payload_login = {
        'action': 'login',
        'username': f'{login}',
        'password': f'{senha}',
    }
    return payload_login

def headers_pentagono():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',  # ← header crítico para endpoints AJAX
        'Referer': 'https://sip8.pentagonotelecom.com.br/relatorioAgrupadoLinhas',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    }

def payloads_relatorio(data):
    payloads_cdr = {
        'DATAI_TMP': data,
        'DATAF_TMP': data,
        'SORT_DIRECTION': 'DESC',
        'SORT_TAG': 'data_index',
        'PAGE': '1',
        'txtDataI': data,
        'txtDataF': data,
        'txtTipo': '0',
    }
    return payloads_cdr # já vai retornar todos os clientes
