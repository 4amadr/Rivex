def clientes_ativos_callix(clientes_json):
    """
    Retorna uma lista com o nome dos clientes ativos no servidor.
    """

    return [
        cliente['attributes']['name']
        .replace('Contech - ', '')
        .replace('contech - ', '')
        .replace('Contech- ', '')
        .replace('contech- ', '')
        .strip()
        for cliente in clientes_json['data']
    ]