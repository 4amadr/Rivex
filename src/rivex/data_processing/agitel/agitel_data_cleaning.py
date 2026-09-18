"""
Extração de dados da tabela "Minutagem da Revenda" do painel Agitel (Softswitch).

Observação sobre o HTML de origem: a coluna "Lucro" (6ª coluna) da tabela vem com
a tag de fechamento errada (ex: `<td class="text-center text-danger">0,00</th>`),
o que faz o parser aninhar as colunas seguintes dentro dela. Isso não afeta as
colunas usadas aqui (Cliente, Minutos e Custo), pois todas ficam ANTES da coluna
quebrada e mantêm abertura/fechamento corretos. Por isso a extração é feita
sempre pela posição (índice) da célula dentro da linha, e não por contagem total
de <td>.
"""
import re
from bs4 import BeautifulSoup

def passar_para_html(pagina_inicial):
    """Função já existente: faz o parser do HTML com BeautifulSoup."""
    return BeautifulSoup(pagina_inicial, "html.parser")


# --------------------------------------------------------------------------
# Helpers internos
# --------------------------------------------------------------------------

def _localizar_linhas_de_clientes(soup):
    """
    Localiza a tabela "Minutagem da Revenda" e retorna apenas as linhas (<tr>)
    que representam clientes -- descarta cabeçalho e a linha de "Total".

    A linha de "Total" também tem class="cinza1", então não dá pra filtrar só
    pela classe da linha. O filtro real é: uma linha de cliente tem pelo menos
    5 células <td> (Cliente, VOIP/VOIP, Minutos, Valor Venda, Custo); a linha
    de Total usa <th> em vez de <td> nessas colunas, então cai fora sozinha.
    """
    titulo = soup.find(lambda tag: tag.name == "th" and "Minutagem da Revenda" in tag.get_text())
    if titulo is None:
        return []

    tabela = titulo.find_parent("table")
    if tabela is None:
        return []

    linhas_validas = []
    for linha in tabela.find_all("tr", class_=["cinza1", "cinza2"]):
        colunas = linha.find_all("td")
        if len(colunas) >= 5:
            linhas_validas.append(colunas)

    return linhas_validas


def _separar_tech_e_cliente(texto_bruto):
    """
    Separa a tech e o nome do cliente.

    A tech deve possuir exatamente 6 dígitos, podendo estar no formato:

        1404#01 -> 140401
        1030#01 -> 103001
        2516#01 -> 251601

    O caractere '#' é removido.

    Caso a tech não possua exatamente 6 dígitos,
    retorna 0.

    Exemplos:
        "1404#01 - Cliente X" -> (140401, "Cliente X")
        "1030#01 - Cliente Y" -> (103001, "Cliente Y")
        "Callix_Manual"       -> (0, "Callix_Manual")
    """

    texto = texto_bruto.strip()

    if " - " not in texto:
        return 0, texto

    tech_bruta, nome = texto.split(" - ", 1)

    # Remove somente o caractere '#'
    tech = tech_bruta.replace("#", "").strip()

    # Garante que todos os caracteres restantes sejam números
    if not tech.isdigit():
        return 0, nome.strip()

    # A tech precisa possuir exatamente 6 dígitos
    if len(tech) != 6:
        return 0, nome.strip()

    return int(tech), nome.strip()



# --------------------------------------------------------------------------
# As 4 funções pedidas
# --------------------------------------------------------------------------

def get_cliente(pagina_inicial):
    """Retorna [{'cliente': nome}, ...] -- só o nome do cliente, sem a tech."""
    soup = passar_para_html(pagina_inicial)
    resultado = []
    for colunas in _localizar_linhas_de_clientes(soup):
        _, nome = _separar_tech_e_cliente(colunas[0].get_text())
        resultado.append({"cliente": nome})
    return resultado


def get_tech(pagina_inicial):
    """Retorna [{'cliente': nome, 'tech': tech}, ...] -- a numeração antes do nome."""
    soup = passar_para_html(pagina_inicial)
    resultado = []
    for colunas in _localizar_linhas_de_clientes(soup):
        tech, nome = _separar_tech_e_cliente(colunas[0].get_text())
        resultado.append({"cliente": nome, "tech": tech})
    return resultado


def get_custo(pagina_inicial):
    """Retorna [{'cliente': nome, 'custo': valor}, ...]."""
    soup = passar_para_html(pagina_inicial)
    resultado = []
    for colunas in _localizar_linhas_de_clientes(soup):
        _, nome = _separar_tech_e_cliente(colunas[0].get_text())
        custo = colunas[4].get_text(strip=True)
        resultado.append({"cliente": nome, "custo": custo})
    return resultado


def get_minutagem(pagina_inicial):
    """Retorna [{'cliente': nome, 'minutagem': valor}, ...]."""
    soup = passar_para_html(pagina_inicial)
    resultado = []
    for colunas in _localizar_linhas_de_clientes(soup):
        _, nome = _separar_tech_e_cliente(colunas[0].get_text())
        minutagem = colunas[2].get_text(strip=True)
        resultado.append({"cliente": nome, "minutagem": minutagem})
    return resultado


# --------------------------------------------------------------------------
# Bônus: as 4 informações já juntas por cliente (útil pro pipeline do Rivex)
# --------------------------------------------------------------------------

def get_dados_clientes(pagina_inicial):
    """
    Retorna uma lista única com tudo junto por cliente:
    [{'tech': ..., 'cliente': ..., 'minutagem': ..., 'custo': ...}, ...]
    """
    soup = passar_para_html(pagina_inicial)
    resultado = []
    for colunas in _localizar_linhas_de_clientes(soup):
        tech, nome = _separar_tech_e_cliente(colunas[0].get_text())
        resultado.append({
            "tech": tech,
            "cliente": nome,
            "minutagem": colunas[2].get_text(strip=True),
            "custo": colunas[4].get_text(strip=True),
        })
    return resultado


def dados_empacotados(dados_consumo, data):
    custo_corrigido = float(dados_consumo["custo"].replace(".", "").replace(",", "."))
    minutagem_corrigida = float(dados_consumo["minutagem"].replace(".", "").replace(",", "."))
    return {
        'tech': dados_consumo['tech'],
        'data': data,
        'custo': custo_corrigido,
        'minutagem': minutagem_corrigida
    }
