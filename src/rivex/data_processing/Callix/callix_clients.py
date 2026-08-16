import re

def limpar_cliente(cliente):
    # Remove "contech" seguido de hífen opcional e espaços, ignorando maiúsculas/minúsculas
    return re.sub(r'(?i)^contech\s*-\s*', '', cliente).strip()


def get_clientes_callix(clientes_json):
    """
    Retorna uma lista com o nome dos clientes ativos no servidor.
    """
    return limpar_cliente(clientes_json['data']['attributes']['name'])


def get_status_cliente(clientes_json):
    return [{
        "cliente": get_clientes_callix(clientes_json),
        "status": estado['attributes']['status']}
        for estado in clientes_json['data']
    ]
    
def get_clientes_servidor_callix(clientes_json):
    lista_callix = []

    for cliente in clientes_json['data']:

        nome = limpar_cliente(
            cliente['attributes']['name']
        )

        status = cliente['attributes']['status']

        lista_callix.append({
            "cliente": nome,
            "status": status
        })

    return lista_callix

def separar_clientes(lista_callix):
    """
    Separa os clientes ativos e inativos.

    Status 3 = ativo
    Status 4 = inativo
    """
    lista_ativos = []
    lista_inativos = []
    for usuario in lista_callix:
        if usuario['status'] == 3:
            lista_ativos.append(usuario['cliente'])
        else:

            lista_inativos.append(usuario['cliente'])
    return lista_ativos, lista_inativos
    
        