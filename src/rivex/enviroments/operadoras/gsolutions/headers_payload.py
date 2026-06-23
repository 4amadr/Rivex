def header_geral():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    }
    return headers

def payload_de_login(usuario, password):
    payload_login = {
        'login': f'{usuario}',
        'senha': f'{password}',
        'Submit': "Entrar"
    }
    return payload_login

def payload_filtragem_custos(data):
    filtragem = {
        'filtro': 1,  # seleção personalizada
        'periodopre': 0,
        'data_inicio': f'{data}',  # formato DD-MM-AAAA
        'horario_inicio': 00,
        'data_fim': f'{data}',  # formato DD-MM-AAAA
        'horario_fim': 23,
        'cliente_filtro': '',
        'tipochamadas': 'todas',
        'action': 'Filtrar'
    }
    return filtragem

def payload_get_id_cliente():
    payload = {
        'nome_cliente ': ""
    }
    return payload

def payload_chamadas_tarifadas(id_cliente, data):
    payload = {
        'customer_id': f'{id_cliente}',
        'startDate': f'{data}',
        'finalDate': f'{data}',
        'sipcode': 200,
        'tipo_exibicao': 'tela',
        'checkbox_columns': '1',
        'exibir_totais': '1',
        'action': 'Buscar'
    }
    return payload