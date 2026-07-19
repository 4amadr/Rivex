import pytest
from src.rivex.data_processing.Vonix.cleaning_vonix import (
    gerar_lista_de_clientes,
    extrair_mapa_clientes,
    limpar_chamadas,
    get_agressividade,
    get_cliente_nome,
    get_tech,
    get_html,
    extrair_dados_agentes
)

def test_gerar_lista_de_clientes_happy_path():
    html_content = """
    <html>
        <body>
            <ul>
                <li id="container_cliente_a">Cliente A</li>
                <li id="container_cliente_b">Cliente B</li>
                <li id="not_a_container">Other Item</li>
            </ul>
        </body>
    </html>
    """
    lista, mapa = gerar_lista_de_clientes(html_content)
    assert lista == ["cliente_a", "cliente_b"]
    assert isinstance(mapa, dict)

def test_gerar_lista_de_clientes_none_input():
    with pytest.raises(TypeError):
        gerar_lista_de_clientes(None)

def test_gerar_lista_de_clientes_empty_string():
    lista, mapa = gerar_lista_de_clientes("")
    assert lista == []
    assert mapa == {}

def test_gerar_lista_de_clientes_whitespace_only():
    lista, mapa = gerar_lista_de_clientes("   \n\t   ")
    assert lista == []
    assert mapa == {}

def test_gerar_lista_de_clientes_no_matching_tags():
    html_content = """
    <html>
        <body>
            <div id="container_div">Div instead of li</div>
            <li id="other_id">LI without container_ prefix</li>
        </body>
    </html>
    """
    lista, mapa = gerar_lista_de_clientes(html_content)
    assert lista == []

def test_gerar_lista_de_clientes_invalid_types():
    assert gerar_lista_de_clientes(123) == ([], {})
    assert gerar_lista_de_clientes(["html"]) == ([], {})
    assert gerar_lista_de_clientes({"html": "content"}) == ([], {})

def test_gerar_lista_de_clientes_prefix_vs_substring():
    html_content = """
    <html>
        <body>
            <ul>
                <li id="container_queue_container_test">Queue Name</li>
            </ul>
        </body>
    </html>
    """
    lista, mapa = gerar_lista_de_clientes(html_content)
    assert lista == ["queue_container_test"]

def test_extrair_mapa_clientes_com_tech():
    """Testa extração de tech e nome do span _stat_route."""
    html_content = """
    <html>
        <body>
            <span class="value audio-queue-stats-routes" id="tcrepresentacao02_stat_route">1404#01 - TC Representação</span>
            <span class="value audio-queue-stats-routes" id="assismollerke_stat_route">1160#01 - Assis e Mollerke</span>
            <span class="value audio-queue-stats-routes" id="19itelinkmanual_stat_route">Manual</span>
        </body>
    </html>
    """
    soup = get_html(html_content)
    mapa = extrair_mapa_clientes(soup)
    
    assert mapa["tcrepresentacao02"]["tech"] == "140401"
    assert mapa["tcrepresentacao02"]["nome"] == "TC Representação"
    assert mapa["assismollerke"]["tech"] == "116001"
    assert mapa["assismollerke"]["nome"] == "Assis e Mollerke"
    assert mapa["19itelinkmanual"]["tech"] == "0"
    assert mapa["19itelinkmanual"]["nome"] == "Manual"

def test_extrair_mapa_clientes_vazio():
    soup = get_html("")
    mapa = extrair_mapa_clientes(soup)
    assert mapa == {}

def test_zero_consumption_limpar_chamadas_empty():
    assert limpar_chamadas("") == "0"

def test_zero_consumption_limpar_chamadas_none():
    assert limpar_chamadas(None) == "0"

def test_zero_consumption_get_agressividade_empty():
    assert get_agressividade("") == "0"

def test_zero_consumption_get_cliente_nome_empty():
    assert get_cliente_nome("") == ""

def test_zero_consumption_get_tech_empty():
    assert get_tech("") == "0"

def test_zero_consumption_extrair_dados_agentes_empty():
    assert extrair_dados_agentes("") == []

def test_zero_consumption_gerar_lista_de_clientes_empty():
    lista, mapa = gerar_lista_de_clientes("")
    assert lista == []
    assert mapa == {}
