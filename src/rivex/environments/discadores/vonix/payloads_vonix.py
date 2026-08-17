import os

def payload_de_login(username, password, token):
    payload_login = {
        'authenticity_token': token,
        'return_to': '',
        'username': username,
        'password': password,
        'commit': 'Entrar'
    }

    return payload_login

def payload_de_filtragem(token, queue_client):
    # para aplicar o filtro
    payload_filtro = {
        'authenticity_token': token,
        'return_to': '/overview',
        'queue_id[]': queue_client # queue_client representa uma equipe entre os clientes
        }
    
    return payload_filtro 

def headers():
    return {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }

def payload_de_chamadas(data, tipo_de_chamada: str | None = None):

    if tipo_de_chamada is None:
        tipo_de_chamada = ""

    payload = {
        'interval[select]': 'custom',
        'interval[start_date]': data,
        'interval[start_time]': '00:00:00',
        'interval[end_date]': data,
        'interval[end_time]': '23:59:59',

        'terminal': '',
        'agent': '',
        'queue[direction]': 'ALL',
        'sort': '',

        'to_excel': '0',
        'to_csv': '0',

        'x': '10',
        'y': '10',

        'locality': '',
        'call_type_id': '',
        'carrier_id': '',
        'trunking_id': '',

        'directions[]': 'AUTO',

        'waits': 'Igual',
        'call_waiting': '',

        'duration': 'Igual',
        'duration_call': '',

        'status[select]': tipo_de_chamada,
        'substatus[select]': ''
    }

    return payload

def payload_de_agentes(data):
    payload_agentes = {
        'interval[select]': 'custom',
        'interval[start_date]': data,
        'interval[end_date]': data,
    }
    return payload_agentes
    
def payload_de_agressividade(token):
    payload = {
        'authenticity_token': token
    }
    return payload