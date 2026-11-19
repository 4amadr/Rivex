import pytest
import re
import os
from unittest.mock import MagicMock, patch
import psycopg2
from psycopg2 import OperationalError

# Source imports
from src.rivex.environments.discadores.vonix.fluxo_coleta import ExecucaoVonix, GerarUrlVonix
from src.rivex.data_processing.Vonix.cleaning_vonix import (
    get_html,
    get_token,
    remover_javascript,
    get_lista_clientes,
    limpar_nome_lista,
    gerar_lista_de_clientes,
    entrar_na_div,
    remover_texto_chamadas,
    chamadas_em_texto,
    limpar_chamadas,
    filtra_agressividade,
    get_agressividade,
    get_techs_texto,
    get_tech_selecionada,
    transformar_nome_cliente,
    get_cliente_nome,
    get_tech_numerico,
    get_tech,
    encontrar_tabela_agentes,
    gerar_lista_infos_agentes,
    gerar_dados_agentes,
    extrair_dados_agentes,
)
from src.rivex.database.database import DatabaseRivex
from src.rivex.pipeline.pipeline_discador.pipeline_vonix import PipelineVonix

# Global mocks
@pytest.fixture(autouse=True)
def mock_sleep():
    """Disable time.sleep for all tests to speed up execution."""
    with patch('time.sleep', return_value=None) as _mock:
        yield _mock

def make_mock_response(status_code, text):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = text
    return mock_resp

# ==============================================================================
# TIER 1: FEATURE COVERAGE (30 tests)
# ==============================================================================

# Feature 1: Client List (5 tests)
def test_t1_client_list_single():
    html = '<li id="container_client_one">Client One</li>'
    clients = gerar_lista_de_clientes(html)
    assert clients == ["client_one"]

def test_t1_client_list_multiple():
    html = '<li id="container_client_a">Client A</li><li id="container_client_b">Client B</li>'
    clients = gerar_lista_de_clientes(html)
    assert clients == ["client_a", "client_b"]

def test_t1_client_list_no_clients():
    html = '<div>No clients listed here</div>'
    clients = gerar_lista_de_clientes(html)
    assert clients == []

def test_t1_client_list_javascript_removed():
    html = '<script>var x = 1;</script><li id="container_client_js">Client JS</li>'
    clients = gerar_lista_de_clientes(html)
    assert clients == ["client_js"]

def test_t1_client_list_raw_helpers():
    html = get_html('<li id="container_x">X</li>')
    raw_list = get_lista_clientes(html)
    assert raw_list == ["container_x"]
    clean_list = limpar_nome_lista(raw_list)
    assert clean_list == ["x"]

# Feature 2: Context Filtering (5 tests)
def test_t1_context_filtering_url_gen():
    url_gen = GerarUrlVonix("http://localhost:3000")
    assert url_gen._url_filtragem() == "http://localhost:3000/login/set_show_queue"

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t1_context_filtering_post(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(200, "Success")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    resp = exec_vonix.get_filtragem("queue_one", "token123")
    assert resp.status_code == 200

def test_t1_context_filtering_payload():
    from src.rivex.environments.discadores.vonix.payloads_vonix import payload_de_filtragem
    p = payload_de_filtragem("token123", "queue_one")
    assert p['authenticity_token'] == "token123"
    assert p['queue_id[]'] == "queue_one"

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t1_context_filtering_http_requisitions(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(200, "Posted")
    from src.rivex.utils.requests_utils.requests import HttpRequisitions
    hr = HttpRequisitions(sess_instance)
    resp = hr.requisicao_post({}, {}, "http://localhost:3000/post")
    assert resp.status_code == 200

def test_t1_context_filtering_headers():
    from src.rivex.environments.discadores.vonix.payloads_vonix import headers
    h = headers()
    assert "user-agent" in h

# Feature 3: Call Data Collection (5 tests)
def test_t1_call_data_clean_total():
    html = '<div id="maincontent"><div class="box-title">Calls (150)</div></div>'
    val = limpar_chamadas(html)
    assert val == "150"

def test_t1_call_data_clean_completed():
    html = '<div id="maincontent"><div class="box-title">Completed (85)</div></div>'
    val = limpar_chamadas(html)
    assert val == "85"

def test_t1_call_data_clean_abandoned():
    html = '<div id="maincontent"><div class="box-title">Abandoned (12)</div></div>'
    val = limpar_chamadas(html)
    assert val == "12"

def test_t1_call_data_clean_refused():
    html = '<div id="maincontent"><div class="box-title">Refused (3)</div></div>'
    val = limpar_chamadas(html)
    assert val == "3"

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t1_call_data_req_get(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.get.return_value = make_mock_response(200, "Call HTML")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    resp = exec_vonix.get_chamadas("completed")
    assert resp.status_code == 200

# Feature 4: Agent Table Parser (5 tests)
def test_t1_agent_parser_success():
    html = """
    <table class="grid">
        <tr class="item">
            <td class="item">Agent A</td>
            <td id="call_counter_AUTO_1"><a>10</a></td>
        </tr>
    </table>
    """
    agents = extrair_dados_agentes(html)
    assert len(agents) == 1
    assert agents[0]["agente"] == "Agent A"
    assert agents[0]["chamadas"] == "10"

def test_t1_agent_parser_shaded_row():
    html = """
    <table class="grid">
        <tr class="shaded">
            <td class="item">Agent Shaded</td>
            <td id="call_counter_AUTO_2"><a>5</a></td>
        </tr>
    </table>
    """
    agents = extrair_dados_agentes(html)
    assert len(agents) == 1
    assert agents[0]["agente"] == "Agent Shaded"
    assert agents[0]["chamadas"] == "5"

def test_t1_agent_parser_empty():
    html = '<table class="grid"></table>'
    agents = extrair_dados_agentes(html)
    assert agents == []

def test_t1_agent_parser_helpers():
    html = """
    <table class="grid">
        <tr class="item">
            <td class="item">Agent Test</td>
            <td id="call_counter_AUTO_3"><a>7</a></td>
        </tr>
    </table>
    """
    tabela = encontrar_tabela_agentes(html)
    infos = gerar_lista_infos_agentes(tabela)
    assert len(infos) == 1
    dados = gerar_dados_agentes(infos)
    assert dados[0]["agente"] == "Agent Test"

def test_t1_agent_parser_calls_count():
    html = """
    <table class="grid">
        <tr class="item">
            <td class="item">Agent C</td>
            <td id="call_counter_AUTO_4"><a>0</a></td>
        </tr>
    </table>
    """
    agents = extrair_dados_agentes(html)
    assert agents[0]["chamadas"] == "0"

# Feature 5: Aggressiveness Configuration (5 tests)
def test_t1_aggressiveness_get_speed():
    html = '<input id="dialer_dial_speed" value="2.5" />'
    speed = get_agressividade(html)
    assert speed == "2.5"

def test_t1_aggressiveness_get_tech():
    html = """
    <select id="queue_lcr_profile_id">
        <option selected="selected">777701 - Sip Trunk</option>
    </select>
    """
    tech = get_tech(html)
    assert tech == "777701"

def test_t1_aggressiveness_get_client_name():
    html = """
    <select id="queue_lcr_profile_id">
        <option selected="selected">777701 - Client Name Test</option>
    </select>
    """
    name = get_cliente_nome(html)
    assert name == "Client Name Test"

def test_t1_aggressiveness_transform_name():
    cleaned = transformar_nome_cliente("777701 - Client-A / B")
    assert cleaned == "ClientA B"

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t1_aggressiveness_coleta_req(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.get.return_value = make_mock_response(200, "Config HTML")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    resp = exec_vonix.coleta_de_agressividade_vonix("clientA", "token123")
    assert resp.status_code == 200

# Feature 6: Database Loading (5 tests)
@patch('src.rivex.database.database.psycopg2')
def test_t1_db_abrir_banco(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    cursor, conn = db.abrir_banco()
    assert cursor is not None
    assert conn is not None

@patch('src.rivex.database.database.psycopg2')
def test_t1_db_envio_banco(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    cursor = MagicMock()
    
    chamadas_dict = {
        "tech": 123401,
        "Cliente": "Client A",
        "Data": "2026-07-15",
        "Chamadas totais": 100,
        "Chamadas aceitas": 80,
        "Chamadas recusadas": 10,
        "Chamadas abandonadas": 10,
        "Agressividade": 2.5
    }
    agentes_list = [
        {
            "tech": 123401,
            "Cliente": "Client A",
            "Data": "2026-07-15",
            "Nome do agente": "Agent One",
            "Chamadas aceitas do agente": 30
        }
    ]
    
    db.connection = mock_conn
    res = db.envio_banco(chamadas_dict, agentes_list, cursor)
    assert res is True
    assert cursor.execute.called

def test_t1_db_fechar_db():
    db = DatabaseRivex()
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    db.fechar_db(mock_cursor, mock_conn)
    assert mock_cursor.close.called
    assert mock_conn.close.called

@patch('src.rivex.database.database.psycopg2')
def test_t1_db_enviar_operadoras(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    cursor = MagicMock()
    db.connection = mock_conn
    consumo_dict = {
        "tech": 123401,
        "cliente": "Client A",
        "discador": "vonix",
        "operadora": "carrierA",
        "data": "2026-07-15",
        "custo": 10.50,
        "minutagem": 150.2,
        "chamadas_tarifadas": 50
    }
    res = db.enviar_banco_operadoras(consumo_dict, cursor)
    assert res is True
    assert cursor.execute.called

@patch('src.rivex.database.database.psycopg2')
def test_t1_db_envio_banco_returns_true(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    db.connection = mock_conn
    res = db.envio_banco({}, [], MagicMock())
    assert res is True


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (30 tests)
# ==============================================================================

# Feature 1: Client List Boundary Cases (5 tests)
def test_t2_client_list_empty():
    assert gerar_lista_de_clientes("") == []

def test_t2_client_list_none():
    with pytest.raises(TypeError):
        gerar_lista_de_clientes(None)

def test_t2_client_list_no_containers():
    html = '<li>Item without container id</li>'
    assert gerar_lista_de_clientes(html) == []

def test_t2_client_list_duplicate_ids():
    html = '<li id="container_dup">D</li><li id="container_dup">D</li>'
    assert gerar_lista_de_clientes(html) == ["dup", "dup"]

def test_t2_client_list_malformed():
    html = '<li id="container_malformed">Missing closing tag'
    assert gerar_lista_de_clientes(html) == ["malformed"]

# Feature 2: Context Filtering Boundary Cases (5 tests)
@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t2_context_filtering_timeout(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(429, "Too Many Requests")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    with pytest.raises(TimeoutError):
        exec_vonix.get_filtragem("queue_one", "token123")

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t2_context_filtering_401(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(401, "Unauthorized")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    with pytest.raises(ValueError):
        exec_vonix.get_filtragem("queue_one", "token123")

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t2_context_filtering_403(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(403, "Forbidden")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    with pytest.raises(PermissionError):
        exec_vonix.get_filtragem("queue_one", "token123")

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t2_context_filtering_500(mock_session):
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(500, "Server Error")
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    with pytest.raises(ConnectionError):
        exec_vonix.get_filtragem("queue_one", "token123")

def test_t2_context_filtering_missing_env():
    with patch.dict(os.environ, {}, clear=True):
        p = PipelineVonix()
        assert p.login is None or p.login == ""

# Feature 3: Call Data Collection Boundary Cases (5 tests)
def test_t2_call_data_empty():
    assert limpar_chamadas("") == "0"

def test_t2_call_data_missing_maincontent():
    html = '<div class="box-title">Calls (100)</div>'
    assert limpar_chamadas(html) == "0"

def test_t2_call_data_missing_boxtitle():
    html = '<div id="maincontent">No calls box</div>'
    assert limpar_chamadas(html) == "0"

def test_t2_call_data_zero_consumption():
    html = '<div id="maincontent"><div class="box-title">Calls (0)</div></div>'
    assert limpar_chamadas(html) == "0"

def test_t2_call_data_no_numbers():
    html = '<div id="maincontent"><div class="box-title">Calls ()</div></div>'
    assert limpar_chamadas(html) == ""

# Feature 4: Agent Table Parser Boundary Cases (5 tests)
def test_t2_agent_table_empty():
    assert extrair_dados_agentes("") == []

def test_t2_agent_table_no_grid():
    html = '<table><tr class="item"><td>No grid class</td></tr></table>'
    assert extrair_dados_agentes(html) == []

def test_t2_agent_table_no_rows():
    html = '<table class="grid"></table>'
    assert extrair_dados_agentes(html) == []

def test_t2_agent_table_missing_columns():
    html = '<table class="grid"><tr class="item"></tr></table>'
    assert extrair_dados_agentes(html) == []

def test_t2_agent_table_missing_a_tag():
    html = """
    <table class="grid">
        <tr class="item">
            <td class="item">Agent A</td>
            <td id="call_counter_AUTO_1">No anchor tag</td>
        </tr>
    </table>
    """
    assert extrair_dados_agentes(html) == [{"agente": "Agent A", "chamadas": "0"}]

# Feature 5: Aggressiveness Configuration Boundary Cases (5 tests)
def test_t2_aggressiveness_empty():
    assert get_agressividade("") == "0"

def test_t2_aggressiveness_missing_speed():
    html = '<div>No speed input</div>'
    assert get_agressividade(html) == "0"

def test_t2_aggressiveness_missing_select():
    html = '<input id="dialer_dial_speed" value="1.0" />'
    assert get_tech(html) == "0"

def test_t2_aggressiveness_no_selected_option():
    html = """
    <select id="queue_lcr_profile_id">
        <option>777701 - Sip Trunk</option>
    </select>
    """
    assert get_tech(html) == "0"

def test_t2_aggressiveness_invalid_tech_format():
    html = """
    <select id="queue_lcr_profile_id">
        <option selected="selected">NoTech - Sip Trunk</option>
    </select>
    """
    assert get_tech(html) == ""

# Feature 6: Database Loading Boundary Cases (5 tests)
@patch('src.rivex.database.database.psycopg2.connect')
def test_t2_db_connection_failure(mock_connect):
    mock_connect.side_effect = OperationalError("Connection timeout")
    db = DatabaseRivex()
    with pytest.raises(OperationalError):
        db.abrir_banco()

@patch('src.rivex.database.database.psycopg2.connect')
def test_t2_db_unicode_decode(mock_connect):
    mock_connect.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid byte")
    db = DatabaseRivex()
    with pytest.raises(UnicodeDecodeError):
        db.abrir_banco()

@patch('src.rivex.database.database.psycopg2')
def test_t2_db_table_creation_fails(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    db.connection = mock_conn
    cursor = MagicMock()
    cursor.execute.side_effect = psycopg2.Error("DDL Error")
    
    # Check that it handles it and does not crash
    res = db.envio_banco({}, [], cursor)
    assert res is True

@patch('src.rivex.database.database.psycopg2')
def test_t2_db_insert_calls_fails(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    db.connection = mock_conn
    cursor = MagicMock()
    
    # Fail only on inserting data (second call to execute)
    def side_effect(sql, *args):
        if "INSERT INTO" in sql and "chamadas_cliente" in sql:
            raise psycopg2.Error("DML Error")
        return MagicMock()
    cursor.execute.side_effect = side_effect
    
    res = db.envio_banco({"tech": 1}, [], cursor)
    assert res is True

@patch('src.rivex.database.database.psycopg2')
def test_t2_db_insert_agents_fails(mock_psycopg2):
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    db = DatabaseRivex()
    db.connection = mock_conn
    cursor = MagicMock()
    
    def side_effect(sql, *args):
        if "INSERT INTO" in sql and "chamadas_agente" in sql:
            raise psycopg2.Error("DML Agent Error")
        return MagicMock()
    cursor.execute.side_effect = side_effect
    
    res = db.envio_banco({}, [{"tech": 1}], cursor)
    assert res is True


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (6 tests)
# ==============================================================================

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t3_client_list_and_context_filtering(mock_session):
    """Client list provides the target context identifier for filtering."""
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(200, "Context Applied")
    
    html = '<li id="container_client_beta">Beta Queue</li>'
    clients = gerar_lista_de_clientes(html)
    assert len(clients) == 1
    
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    resp = exec_vonix.get_filtragem(clients[0], "token_abc")
    assert resp.status_code == 200

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t3_context_filtering_and_call_data(mock_session):
    """Context selection followed by call data fetch under that context."""
    sess_instance = mock_session.return_value
    sess_instance.post.return_value = make_mock_response(200, "Filtered")
    sess_instance.get.return_value = make_mock_response(200, "Calls (42)")
    
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    filter_resp = exec_vonix.get_filtragem("client_beta", "token_abc")
    assert filter_resp.status_code == 200
    
    calls_resp = exec_vonix.get_chamadas("completed")
    val = limpar_chamadas(f'<div id="maincontent"><div class="box-title">{calls_resp.text}</div></div>')
    assert val == "42"

@patch('src.rivex.database.database.psycopg2')
def test_t3_call_data_and_database(mock_psycopg2):
    """Cleaned call metrics feeding directly into the database insertion layer."""
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    
    html = '<div id="maincontent"><div class="box-title">Calls (100)</div></div>'
    calls_count = int(limpar_chamadas(html))
    
    db = DatabaseRivex()
    db.connection = mock_conn
    cursor = MagicMock()
    
    chamadas_payload = {
        "tech": 555501,
        "Cliente": "Client Beta",
        "Data": "2026-07-15",
        "Chamadas totais": calls_count,
        "Chamadas aceitas": 90,
        "Chamadas recusadas": 5,
        "Chamadas abandonadas": 5,
        "Agressividade": 3.0
    }
    res = db.envio_banco(chamadas_payload, [], cursor)
    assert res is True
    assert cursor.execute.called

@patch('src.rivex.database.database.psycopg2')
def test_t3_agent_parser_and_database(mock_psycopg2):
    """Parsed agent rows mapped to the database insertion routine."""
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    
    html = """
    <table class="grid">
        <tr class="item">
            <td class="item">Agent Smith</td>
            <td id="call_counter_AUTO_5"><a>45</a></td>
        </tr>
    </table>
    """
    agents = extrair_dados_agentes(html)
    assert len(agents) == 1
    
    agent_db_payload = [
        {
            "tech": 555501,
            "Cliente": "Client Beta",
            "Data": "2026-07-15",
            "Nome do agente": agents[0]["agente"],
            "Chamadas aceitas do agente": int(agents[0]["chamadas"])
        }
    ]
    
    db = DatabaseRivex()
    db.connection = mock_conn
    cursor = MagicMock()
    res = db.envio_banco({}, agent_db_payload, cursor)
    assert res is True
    assert cursor.execute.called

def test_t3_aggressiveness_and_call_data():
    """Aggressiveness config features (tech prefix, client name) enriching call data."""
    config_html = """
    <input id="dialer_dial_speed" value="3.8" />
    <select id="queue_lcr_profile_id">
        <option selected="selected">999901 - Rich Client</option>
    </select>
    """
    calls_html = '<div id="maincontent"><div class="box-title">Calls (500)</div></div>'
    
    speed = float(get_agressividade(config_html))
    tech = int(get_tech(config_html))
    client_name = get_cliente_nome(config_html)
    calls = int(limpar_chamadas(calls_html))
    
    enriched_call_data = {
        "tech": tech,
        "Cliente": client_name,
        "Chamadas totais": calls,
        "Agressividade": speed
    }
    
    assert enriched_call_data["tech"] == 999901
    assert enriched_call_data["Cliente"] == "Rich Client"
    assert enriched_call_data["Chamadas totais"] == 500
    assert enriched_call_data["Agressividade"] == 3.8

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t3_client_list_and_aggressiveness(mock_session):
    """Retrieve client list and loop over each client to fetch aggressiveness speed details."""
    sess_instance = mock_session.return_value
    
    clients_html = '<li id="container_client_x">X</li><li id="container_client_y">Y</li>'
    clients = gerar_lista_de_clientes(clients_html)
    
    # Mock speed response for each client
    sess_instance.get.return_value = make_mock_response(200, '<input id="dialer_dial_speed" value="2.2" />')
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    
    speeds = {}
    for c in clients:
        resp = exec_vonix.coleta_de_agressividade_vonix(c, "token_123")
        speeds[c] = float(get_agressividade(resp.text))
        
    assert speeds["client_x"] == 2.2
    assert speeds["client_y"] == 2.2


# ==============================================================================
# TIER 4: REAL-WORLD WORKLOADS/SCENARIOS (5 tests)
# ==============================================================================

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
@patch('src.rivex.database.database.psycopg2')
def test_t4_scenario_happy_path(mock_psycopg2, mock_session):
    """Standard daily run Happy Path: Login, retrieve client list, iterate client loops, cleanup & store."""
    sess_instance = mock_session.return_value
    
    # 1. Login Cookie Request containing authenticity token
    login_page_html = '<input name="authenticity_token" value="session_token_999" />'
    
    # 2. Client list page containing containers
    clients_page_html = '<li id="container_customer_alpha">Alpha Customer</li>'
    
    # 3. Call and agent endpoints HTML
    calls_html = '<div id="maincontent"><div class="box-title">Calls (25)</div></div>'
    agents_html = """
    <table class="grid">
        <tr class="item">
            <td class="item">Agent John</td>
            <td id="call_counter_AUTO_1"><a>12</a></td>
        </tr>
    </table>
    """
    config_html = """
    <input id="dialer_dial_speed" value="1.5" />
    <select id="queue_lcr_profile_id">
        <option selected="selected">123401 - Alpha Customer</option>
    </select>
    """
    
    # Map get request targets
    def mock_get(url, *args, **kwargs):
        if "/login/signin" in url:
            return make_mock_response(200, login_page_html)
        elif "/calls" in url:
            return make_mock_response(200, calls_html)
        elif "/agents/calls_overview" in url:
            return make_mock_response(200, agents_html)
        elif "/admin/queue_edit" in url:
            return make_mock_response(200, config_html)
        # Dashboard client retrieval URL
        return make_mock_response(200, clients_page_html)
        
    sess_instance.get.side_effect = mock_get
    sess_instance.post.return_value = make_mock_response(200, "Post Success")
    
    # Mock Database
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Run the pipeline entry point directly
    pipeline = PipelineVonix()
    pipeline.execucao_vonix()
    
    # Verify DB operations called on cursor and connection
    assert mock_cursor.close.called
    assert mock_conn.close.called
    
    # Verify that the correct queries were executed
    execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
    assert any("CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente" in q for q in execute_calls)
    assert any("CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente" in q for q in execute_calls)
    assert any("INSERT INTO dados_discador.chamadas_cliente" in q for q in execute_calls)
    assert any("INSERT INTO dados_discador.chamadas_agente" in q for q in execute_calls)

    # Verify parameters sent to database insertion
    chamadas_insert_args = [
        call[0][1] for call in mock_cursor.execute.call_args_list 
        if call[0][0] and "INSERT INTO dados_discador.chamadas_cliente" in call[0][0]
    ]
    assert len(chamadas_insert_args) == 1
    assert chamadas_insert_args[0]["tech"] == 123401
    assert chamadas_insert_args[0]["Cliente"] == "Alpha Customer"
    assert chamadas_insert_args[0]["Chamadas totais"] == 25
    assert chamadas_insert_args[0]["Agressividade"] == 1.5

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
@patch('src.rivex.database.database.psycopg2')
def test_t4_scenario_holiday_no_calls(mock_psycopg2, mock_session):
    """Holiday run scenario: zero calls and no active agents, pipeline flows with zero/empty values."""
    sess_instance = mock_session.return_value
    
    login_page_html = '<input name="authenticity_token" value="holiday_token" />'
    clients_page_html = '<li id="container_customer_holiday">Holiday Customer</li>'
    calls_html = '<div id="maincontent"><div class="box-title">Calls (0)</div></div>'
    agents_html = '<table class="grid"></table>' # Empty agent table
    config_html = """
    <input id="dialer_dial_speed" value="0.0" />
    <select id="queue_lcr_profile_id">
        <option selected="selected">999999 - Holiday Customer</option>
    </select>
    """
    
    def mock_get(url, *args, **kwargs):
        if "/login/signin" in url:
            return make_mock_response(200, login_page_html)
        elif "/calls" in url:
            return make_mock_response(200, calls_html)
        elif "/agents/calls_overview" in url:
            return make_mock_response(200, agents_html)
        elif "/admin/queue_edit" in url:
            return make_mock_response(200, config_html)
        return make_mock_response(200, clients_page_html)
        
    sess_instance.get.side_effect = mock_get
    sess_instance.post.return_value = make_mock_response(200, "Post Success")
    
    # Mock Database
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    pipeline = PipelineVonix()
    pipeline.execucao_vonix()
    
    assert mock_cursor.close.called
    assert mock_conn.close.called

    execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
    assert any("INSERT INTO dados_discador.chamadas_cliente" in q for q in execute_calls)
    
    chamadas_insert_args = [
        call[0][1] for call in mock_cursor.execute.call_args_list 
        if call[0][0] and "INSERT INTO dados_discador.chamadas_cliente" in call[0][0]
    ]
    assert len(chamadas_insert_args) == 1
    assert chamadas_insert_args[0]["Chamadas totais"] == 0
    assert chamadas_insert_args[0]["Agressividade"] == 0.0

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
def test_t4_scenario_token_expiry_retry(mock_session):
    """Simulate authorization expired mid-run, forcing token re-acquisition."""
    sess_instance = mock_session.return_value
    
    # First login token fetch
    login_html = '<input name="authenticity_token" value="expired_token" />'
    
    def mock_get(url, *args, **kwargs):
        if "/login/signin" in url:
            return make_mock_response(200, login_html)
        return make_mock_response(200, "some content")
        
    sess_instance.get.side_effect = mock_get
    
    exec_vonix = ExecucaoVonix("user", "pass", "15/07/2026", "http://localhost:3000")
    t1 = exec_vonix.token_pronto()
    assert t1 == "expired_token"
    
    # Token expired! Refresh token simulation
    login_html = '<input name="authenticity_token" value="fresh_token" />'
    t2 = exec_vonix.token_pronto()
    assert t2 == "fresh_token"

@patch('src.rivex.utils.requests_utils.requests.requests.Session')
@patch('src.rivex.database.database.psycopg2')
def test_t4_scenario_special_characters(mock_psycopg2, mock_session):
    """Ensure client names with weird formatting/characters are cleaned properly in E2E path."""
    sess_instance = mock_session.return_value
    
    login_page_html = '<input name="authenticity_token" value="token" />'
    clients_page_html = '<li id="container_customer_accents">Custômer Accènts!</li>'
    calls_html = '<div id="maincontent"><div class="box-title">Calls (10)</div></div>'
    agents_html = '<table class="grid"></table>'
    config_html = """
    <input id="dialer_dial_speed" value="1.0" />
    <select id="queue_lcr_profile_id">
        <option selected="selected">543201 - Custômer Accènts!</option>
    </select>
    """
    
    def mock_get(url, *args, **kwargs):
        if "/login/signin" in url:
            return make_mock_response(200, login_page_html)
        elif "/calls" in url:
            return make_mock_response(200, calls_html)
        elif "/agents/calls_overview" in url:
            return make_mock_response(200, agents_html)
        elif "/admin/queue_edit" in url:
            return make_mock_response(200, config_html)
        return make_mock_response(200, clients_page_html)
        
    sess_instance.get.side_effect = mock_get
    sess_instance.post.return_value = make_mock_response(200, "Post Success")
    
    # Mock Database
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    pipeline = PipelineVonix()
    pipeline.execucao_vonix()

    assert mock_cursor.close.called
    assert mock_conn.close.called

    # Check that it inserted "Custômer Accènts" to database
    chamadas_insert_args = [
        call[0][1] for call in mock_cursor.execute.call_args_list 
        if call[0][0] and "INSERT INTO dados_discador.chamadas_cliente" in call[0][0]
    ]
    assert len(chamadas_insert_args) == 1
    assert chamadas_insert_args[0]["Cliente"] == "Custômer Accènts"
    
    # Let's verify standard regex cleaning behavior
    cleaned_name = transformar_nome_cliente("543201 - Custômer Accènts!")
    assert cleaned_name == "Custômer Accènts"

@patch('src.rivex.database.database.psycopg2.connect')
def test_t4_scenario_db_intermittent_disconnect(mock_connect):
    """Pipeline fails gracefully on database connection error."""
    mock_connect.side_effect = OperationalError("Database host not reachable")
    db = DatabaseRivex()
    with pytest.raises(OperationalError):
        db.abrir_banco()
