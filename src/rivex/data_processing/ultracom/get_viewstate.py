from bs4 import BeautifulSoup
from bs4.element import Tag


def parsear_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def find_viewstate(soup: BeautifulSoup) -> Tag | None:
    return soup.find(
        "input",
        attrs={"name": "javax.faces.ViewState"}
    )


def valor_viewstate(viewstate: Tag) -> str:
    valor = viewstate.get("value")

    if valor is None:
        raise ValueError("Campo javax.faces.ViewState sem atributo 'value'.")

    return valor


def extrair_viewstate(html: str) -> str:
    soup = parsear_html(html)

    viewstate = find_viewstate(soup)

    if viewstate is None:
        raise ValueError("javax.faces.ViewState não encontrado.")

    return valor_viewstate(viewstate)