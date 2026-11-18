def payload_login_ipbox(login, senha):
    payload_login = {
        'doLogin': '1',
        'login': f'{login}',
        'senha': f'{senha}',
        'Login': 'Entrar'
    }
    return payload_login

payload_get_clientes = {
    'tipo': 'A',
    'selectActive': 'Y'
}

def headers_ipbox():
    return {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0'
    }

def headers_api_telefonia(token):
    return {
  'Authorization': f'{token}',
  'Content-Type': 'application/x-www-form-urlencoded'
}

def payload_api_telefonia(data, cliente):
    cliente = cliente.strip()
    # Retorna um dicionário puro em vez de uma string com '&'
    return {"de": f"{data}000000", "ate": f"{data}235959", "operacao": cliente}

def payload_get_clientes_painel_de_estado():
    return {"selectActive": "Y"}