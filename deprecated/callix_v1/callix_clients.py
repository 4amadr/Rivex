import re

def limpar_cliente(cliente):
    # Remove "contech" seguido de hífen opcional e espaços, ignorando maiúsculas/minúsculas
    return re.sub(r'(?i)^contech\s*-\s*', '', cliente).strip()


def get_clientes_servidor_callix(clientes_json):
    lista_callix = []

    for cliente in clientes_json.get('data', []):
        attributes = cliente.get('attributes', {})

        nome = attributes.get('subdomain') or limpar_cliente(
            attributes.get('name', '')
        )

        status = attributes.get('status')

        lista_callix.append({
            "cliente": nome,
            "status": status
        })

    return lista_callix

def separar_clientes(lista_callix):
    """
    Separa os clientes ativos e inativos.

    Status 'active' ou 3 = ativo
    Status 'inactive' ou 4 = inativo
    """
    lista_ativos = []
    lista_inativos = []
    for usuario in lista_callix:
        if usuario['status'] in ('active', 3):
            lista_ativos.append(usuario['cliente'])
        else:
            lista_inativos.append(usuario['cliente'])
    return lista_ativos, lista_inativos
    
        