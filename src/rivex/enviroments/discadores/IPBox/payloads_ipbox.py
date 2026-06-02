from urllib.parse import urlencode, quote_plus, unquote_plus, quote
import re

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
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0'
    }

def payload_filtragem_clientes(cliente_id):
    payload_filtragem = {
        'act': 'alter',
        'obj_fila_id': f'{cliente_id}'
    }
    return payload_filtragem


def payload_relatorio_agentes(cliente_id):
    return {
        "relatid": cliente_id
    }

def headers_api_telefonia(token):
    return {
  'Authorization': f'{token}',
  'Content-Type': 'application/x-www-form-urlencoded'
}
    
def limpeza_sufixo_cliente(cliente):
    '''
    Remove sufixos numéricos de clientes do IPBox
    '''
    return re.sub(r'\s+\d+$', '', cliente).strip()

def payload_api_telefonia(data, cliente):
    cliente = limpeza_sufixo_cliente(cliente.strip())
    
    print('Cliente buscado: ', cliente)
    operacao = quote(cliente.strip(), safe='#')
    
    payload = (
        f'de={data}000000'
        f'&ate={data}235959'
        f'&operacao={operacao}'
    )
    
    return payload