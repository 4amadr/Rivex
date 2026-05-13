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

def payload_config_cliente(id_cliente):
    payload_cliente = {
        'act': 'alter',
        'obj_fila_id': f'{id_cliente}'
    }
    return payload_cliente

def headers_ipbox():
    return {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
    }

def payload_filtragem_clientes(cliente_id):
    payload_filtragem = {
        'act': 'alter',
        'obj_fila_id': f'{cliente_id}'
    }
    return payload_filtragem

def payload_telefonia_ipbox(cliente_id, data):
    return {
        'ipoperid': f'{cliente_id}',
        'filaid': '0',
        'loteid': '0',
        'de': f'{data}',
        'ate': f'{data}',
    }

def payload_relatorio_agentes(cliente_id):
    return {
        "relatid": cliente_id
    }

def headers_api_telefonia(token):
    return {
  'Authorization': f'{token}',
  'Content-Type': 'application/x-www-form-urlencoded'
}

def payload_api_telefonia(data, cliente):
    de = f'{data}000000'
    ate = f'{data}235959'
    return {
        'de': de,
        'ate': ate,
        'operacao': cliente.strip()
    }

def payload_api_agentes(data):

    de = f'{data}000000'
    ate = f'{data}235959'

    payload = f'de={de}&ate={ate}'

    return payload