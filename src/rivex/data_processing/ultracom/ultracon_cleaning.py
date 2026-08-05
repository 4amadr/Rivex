from bs4 import BeautifulSoup

from bs4 import BeautifulSoup

def obter_chamadas_tarifadas(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")

    tabela = soup.find("tbody", id="frmAsrSub:listAsrs:tb")

    if not tabela:
        return 0

    for linha in tabela.find_all("tr"):
        colunas = linha.find_all("td")

        if len(colunas) < 3:
            continue

        sip_code = colunas[0].get_text(strip=True)
        sip_reason = colunas[1].get_text(strip=True)
        total = colunas[2].get_text(strip=True)

        if sip_code == "200" and sip_reason.upper() == "OK":
            return int(total)

    return 0

def get_minutagem(html: str) -> str:
    """
    Extrai o valor de minutagem total da página do portal SIP.
    Busca pelo elemento <td> do rodapé da tabela 'listCdrsTotal'
    que contém o tempo no formato HH:MM:SS.

    Args:
        html: String com o conteúdo HTML da página.

    Returns:
        String com a minutagem no formato HH:MM:SS.
        Ex: '94:49:23'

    Raises:
        ValueError: Se o elemento de minutagem não for encontrado no HTML.
    """
    soup = BeautifulSoup(html, "html.parser")

    # O valor fica no <td> do <tfoot> com o id que contém 'j_id171'
    # Usamos busca parcial no id pois ele pode variar entre sessões
    td = soup.find("td", id=lambda x: x and "listCdrsTotal" in x and "j_id171" in x)

    if not td:
        # Fallback: busca pelo rodapé da tabela e pega a 2ª célula de dados
        table = soup.find("table", id=lambda x: x and "listCdrsTotal" in x)
        if table:
            tfoot = table.find("tfoot")
            if tfoot:
                cells = tfoot.find_all("td")
                # células: [0] = label "Total", [1] = duração, [2] = preço
                if len(cells) >= 2:
                    td = cells[1]

    if not td:
        raise ValueError(
            "Elemento de minutagem não encontrado no HTML. "
            "Verifique se a página foi carregada corretamente."
        )

    return td.get_text(strip=True)


def get_custos(html: str) -> str:
    """
    Extrai o valor de custo total da página do portal SIP.
    Busca pelo elemento <td> do rodapé da tabela 'listCdrsTotal'
    que contém o valor monetário.

    Args:
        html: String com o conteúdo HTML da página.

    Returns:
        String com o custo no formato original encontrado na página.
        Ex: '433.72780'

    Raises:
        ValueError: Se o elemento de custo não for encontrado no HTML.
    """
    soup = BeautifulSoup(html, "html.parser")

    # O valor fica no <td> do <tfoot> com o id que contém 'j_id174'
    td = soup.find("td", id=lambda x: x and "listCdrsTotal" in x and "j_id174" in x)

    if not td:
        # Fallback: busca pelo rodapé da tabela e pega a 3ª célula de dados
        table = soup.find("table", id=lambda x: x and "listCdrsTotal" in x)
        if table:
            tfoot = table.find("tfoot")
            if tfoot:
                cells = tfoot.find_all("td")
                # células: [0] = label "Total", [1] = duração, [2] = preço
                if len(cells) >= 3:
                    td = cells[2]

    if not td:
        raise ValueError(
            "Elemento de custo não encontrado no HTML. "
            "Verifique se a página foi carregada corretamente."
        )

    return td.get_text(strip=True)


def minutagem(valor_hms: str) -> float:
    """
    Converte o valor de minutagem do formato HH:MM:SS para minutos,
    pronto para inserção em banco de dados.

    Args:
        valor_hms: String no formato HH:MM:SS retornada por get_minutagem().
                   Ex: '94:49:23'

    Returns:
        Float com o total em minutos, com 2 casas decimais.
        Ex: 5689.38  (94h * 60 + 49min + 23seg/60)

    Raises:
        ValueError: Se o formato da string não for HH:MM:SS.
    """
    partes = valor_hms.strip().split(":")

    if len(partes) != 3:
        raise ValueError(
            f"Formato inválido: '{valor_hms}'. Esperado HH:MM:SS."
        )

    try:
        horas = int(partes[0])
        minutos = int(partes[1])
        segundos = int(partes[2])
    except ValueError:
        raise ValueError(
            f"Valores não numéricos encontrados em '{valor_hms}'. Esperado HH:MM:SS."
        )

    total_minutos = (horas * 60) + minutos + round(segundos / 60, 6)

    return round(total_minutos, 2)


def custos(valor_str: str) -> float:
    """
    Converte o valor de custo para float com 2 casas decimais,
    pronto para inserção em banco de dados.
    Remove vírgulas (separador de milhar) e normaliza o ponto decimal.

    Args:
        valor_str: String com o custo retornada por get_custos().
                   Aceita formatos como '433.72780' ou '433,72780'.

    Returns:
        Float com o custo arredondado para 2 casas decimais.
        Ex: 433.73

    Raises:
        ValueError: Se o valor não puder ser convertido para número.
    """
    # Remove espaços e substitui vírgula por ponto (caso venha como separador decimal)
    valor_normalizado = valor_str.strip().replace(",", ".")

    try:
        valor_float = float(valor_normalizado)
    except ValueError:
        raise ValueError(
            f"Não foi possível converter '{valor_str}' para número. "
            "Verifique o formato do valor de custo."
        )

    return round(valor_float, 2)

def minutagem_pronta(html):
    minutagem_suja = get_minutagem(html)
    return minutagem(minutagem_suja)

def custos_prontos(html):
    custo_sujo = get_custos(html)
    return custos(custo_sujo)