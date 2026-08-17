# Vonix Dialer Pipeline Investigation Report

## Executive Summary
This report presents a read-only codebase investigation of the Vonix dialer integration inside the Rivex application. It identifies all `print()` statements across target files, tracks namespace overlaps for `dict_agentes`, exposes unused files and classes, lists duplicate imports, describes automatic queue discovery, catalogs timing delays, and identifies the appropriate locations for new unit tests.

---

## 1. Print Statement Inventory
We scanned the target files for occurrences of `print()` statements. They are cataloged below with exact line numbers and contents:

### 1.1 `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py`
* **Line 44**: `print(f"Nome do cliente após limpeza: {nome_cliente}")`
* **Line 57**: `print(tabela)`

### 1.2 `src/rivex/environments/discadores/vonix/fluxo_coleta.py`
* **None**: No `print()` statements exist in this file.

### 1.3 `src/rivex/environments/discadores/vonix/fluxo_limpeza.py`
* **Line 61**: `print('Sem consumo na fila: ', equipe)`

### 1.4 `src/rivex/data_processing/Vonix/cleaning_vonix.py` *(Note: Target path `src/rivex/environments/discadores/vonix/cleaning_vonix.py` does not exist; the actual implementation file is `src/rivex/data_processing/Vonix/cleaning_vonix.py`)*
* **None**: No `print()` statements exist in this file.

### 1.5 `src/rivex/database/database.py`
* **Line 116**: `print("Conectado ao banco de dados")`
* **Line 138**: `print("Enviando dados de chamadas para o banco de dados")`
* **Line 140**: `print("Chamadas enviadas para o banco de dados!")`
* **Line 143**: `print(f"Erro ao enviar chamadas para o banco de dados! {erro_de_envio_de_chamadas}")`
* **Line 148**: `print("Dados de agentes enviados para o banco de dados!")`
* **Line 151**: `print(f"Erro ao enviar dados de agentes para o banco de dados {erro_envio_dados_agentes}")`
* **Line 162**: `print(erro_banco)`
* **Line 166**: `print("Enviando dados de consumo de clientes para o banco de dados")`
* **Line 179**: `print("Conexão fechada com o DB")`

### 1.6 `src/rivex/environments/discadores/vonix/vonix_queue_discovery.py` *(Bonus: Checked for completeness)*
* **Line 168**: `print(f"{'='*60}")`
* **Line 169**: `print(f"RESUMO DE FILAS DO VONIX")`
* **Line 170**: `print(f"{'='*60}")`
* **Line 171**: `print(f"  Total de filas:      {len(todas)}")`
* **Line 172**: `print(f"  Filas ativas:        {len(ativas)}")`
* **Line 173**: `print(f"  Filas automáticas:   {len(automaticas)}")`
* **Line 174**: `print(f"  Filas inativas:      {len(todas) - len(ativas)}")`
* **Line 175**: `print()`
* **Line 177**: `print("FILAS AUTOMÁTICAS (para coleta):")`
* **Line 179**: `print(f"  {f['id']:<35} {f['nome']}")`

---

## 2. Tracking `dict_agentes` Dictionary and Function Namespace
A significant namespace conflict occurs because the identifier `dict_agentes` is used for two entirely different entities in the codebase:
1. **A hardcoded lookup dictionary** mapping team names to agent IDs in `src/rivex/environments/discadores/vonix/equipes_vonix.py`.
2. **A parsing function** in `src/rivex/data_processing/Vonix/cleaning_vonix.py` that processes HTML responses to extract agent information.

### 2.1 Occurrences and Import Flow
* **`src/rivex/environments/discadores/vonix/equipes_vonix.py`**:
  * Defines the global dictionary variable:
    ```python
    dict_agentes = {
        'Tc Representação': ['tcrepresentacao', 'tcrepresentacao01', 'tcrepresentacao02', 'tcrepresentacao03', 'tcrepresentacao04'],
        'Assis e mollerke': ['assismollerke'],
        'Real promotora': ['realpromotora', 'realpromotora2']
    }
    ```
* **`src/rivex/data_processing/Vonix/cleaning_vonix.py`**:
  * Defines the parsing function:
    ```python
    def dict_agentes(html):
        ...
    ```
  * Also uses it as a local variable inside the helper function `gerar_dados_agentes`:
    ```python
    dict_agentes = {
        "agente": agente_nome,
        "chamadas": chamadas_val
    }
    ```
* **`src/rivex/environments/discadores/vonix/fluxo_coleta.py`**:
  * Imports the dictionary from `equipes_vonix`:
    ```python
    from src.rivex.environments.discadores.vonix.equipes_vonix import dict_agentes
    ```
  * However, `dict_agentes` is **not used** anywhere else in `fluxo_coleta.py`.
* **`src/rivex/pipeline/pipeline_discador/pipeline_vonix.py`**:
  * Has wildcard imports from both files:
    ```python
    from src.rivex.environments.discadores.vonix.fluxo_coleta import *
    from src.rivex.data_processing.Vonix.cleaning_vonix import *
    ```
  * Because `fluxo_coleta` imports `dict_agentes` (the dictionary) and `cleaning_vonix` defines `dict_agentes` (the function), Python's import order causes the **function to shadow and overwrite the dictionary** in `pipeline_vonix.py`.
  * Consequently, line 56 uses the **function**:
    ```python
    tabela = dict_agentes(agentes.text)
    ```
* **`tests/teste_discovery_vonix.py`**:
  * Imports and iterates over the **dictionary** to cross-reference discovered queues:
    ```python
    from src.rivex.environments.discadores.vonix.equipes_vonix import dict_agentes
    for nome, filas in dict_agentes.items():
        ...
    ```
* **`tests/e2e/test_e2e_suite.py`**:
  * Imports and tests the **function**:
    ```python
    from src.rivex.data_processing.Vonix.cleaning_vonix import dict_agentes
    ```

---

## 3. Structure and Usage of `fluxo_limpeza.py`
The file `src/rivex/environments/discadores/vonix/fluxo_limpeza.py` contains a single class `LimpezaVonix` with the following structure:

```python
class LimpezaVonix:
    def encontrar_tabela(self, html_selecionado): ...
    def nova_chamadas(self, html): ...
    def extrair_chamadas_agentes(self, html): ...
    def agressividade(self, html_agressividade): ...
    def limpeza_de_dados_vonix(self, html_chamadas_totais, html_chamadas_completas, html_chamadas_recusadas, html_chamadas_abandonadas, html_agentes, html_agressividade, equipe, data): ...
```

### 3.1 Codebase Usage Analysis
* **`main.py`**: Imports the class:
  ```python
  from src.rivex.environments.discadores.vonix.fluxo_limpeza import LimpezaVonix
  ```
  But it is **never instantiated or used** anywhere in `main.py`.
* **`src/rivex/pipeline/pipeline_discador/pipeline_vonix.py`**:
  ```python
  from src.rivex.environments.discadores.vonix.fluxo_limpeza import *
  ```
  However, no classes or functions from `fluxo_limpeza.py` are referenced or called. The pipeline calls functional cleaners from `cleaning_vonix.py` (like `limpar_chamadas` and `dict_agentes`) instead.
* **Conclusion**: The entire class `LimpezaVonix` in `fluxo_limpeza.py` is **completely dead code** and is not used in the active data pipelines.

---

## 4. Cleaner and Faxina Utilities
We verified the paths and existence of the two helper cleaning scripts:
* **`src/rivex/utils/infra_utils/cleaner.py`**: **Exists**. Contains the `nuke_zombies()` function which scans the repository recursively and deletes packaging folders (`.egg-info`, `build`, `dist`) while ignoring `.venv`.
* **`src/rivex/utils/infra_utils/faxina.py`**: **Exists**. Contains the `limpar_sujeira()` function, performing similar cleanup operations using `os.walk`.
* **Usage**: Both files are standalone utilities designed to be run as scripts (`__main__` entry point). Neither is imported or used by any other module or file in the codebase.

---

## 5. Duplicate Imports in `main.py`
In `main.py`, the module `dotenv.load_dotenv` is imported twice:
* **Line 4**: `from dotenv import load_dotenv`
* **Line 19**: `from dotenv import load_dotenv`

This redundancy should be cleaned up.

---

## 6. Vonix Queue Discovery Analysis
The file `src/rivex/environments/discadores/vonix/vonix_queue_discovery.py` defines the class `VonixQueueDiscovery`, which is designed to dynamically scrape queue identifiers and names from the Vonix dashboard.

### 6.1 Attributes
* `PREFIXOS_INATIVOS = ['zz', 'Zz', 'ZZ', '- equipe de teste']`
* `SUFIXO_MANUAL = 'manual'`

### 6.2 Methods and Architecture
1. **`__init__(self, session, url_base)`**: Receives a logged-in `requests.Session` and base URL.
2. **`descobrir_filas(self, forcar_reload=False)`**: Requests `url_base/` and searches for the checkbox form `<form action="/login/set_show_queue">`. Iterates through `<input name="queue_id[]">` checkboxes to construct a list of `{'id': ..., 'name': ...}`.
3. **`filas_ativas(self, incluir_manuais=True, forcar_reload=False)`**: Filters out queues matching `PREFIXOS_INATIVOS` or containing the word `'inativos'`.
4. **`filas_automaticas(self, forcar_reload=False)`**: Filters out manual queues (calls `filas_ativas` with `incluir_manuais=False`).
5. **`buscar_fila(self, termo)`**: Helper to search queues by ID/Name.
6. **`ids_das_filas(self, apenas_ativas=True, incluir_manuais=True)`**: Returns flat list of queue string IDs.
7. **`resumo(self)`**: Prints a command-line summary table of the discovered queues.

---

## 7. Analysis of `time.sleep`
The codebase uses `time.sleep` in several loops and utilities. We cataloged them below:
* **`src/rivex/pipeline/pipeline_discador/pipeline_vonix.py` (Line 125)**: `time.sleep(4)` — **This is the specific sleep duration per client in the Vonix integration loop**, used to respect Vonix's rate limits.
* **`src/rivex/pipeline/pipeline_discador/pipeline_ipbox.py` (Line 81)**: `time.sleep(5)`
* **`src/rivex/pipeline/pipeline_operadora/pipeline_agitel.py` (Line 60)**: `time.sleep(5)`
* **`src/rivex/utils/selenium/fast_selenium.py` (Line 93)**: `time.sleep(2)`
* **`src/rivex/utils/utils_system/server_retry.py` (Line 20)**: `time.sleep(atraso)`

---

## 8. Wildcard Imports
Wildcard imports (`from ... import *`) are prevalent in the Vonix integration files and are responsible for namespace shadowing.

### 8.1 In `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py`:
* `from src.rivex.environments.discadores.vonix.fluxo_coleta import *`
* `from src.rivex.environments.discadores.vonix.fluxo_limpeza import *`
* `from src.rivex.data_processing.Vonix.cleaning_vonix import *`

### 8.2 In `src/rivex/environments/discadores/vonix/fluxo_coleta.py`:
* `from src.rivex.environments.discadores.vonix.payloads_vonix import *`
* `from src.rivex.data_processing.Vonix.cleaning_vonix import *`

These wildcards should be replaced with explicit imports to avoid collision and improve readability.

---

## 9. Test Suite Analysis & Zero-Consumption Tests Placement
We mapped the current test files inside `tests/` directory:
* **`tests/test_cleaning_vonix.py`**: Contains unit tests for `gerar_lista_de_clientes` using pytest.
* **`tests/test_fluxo_coleta.py`**: Unit tests checking the HTTP request URLs using patch/mock.
* **`tests/e2e/test_e2e_suite.py`**: Massive integration suite (886 lines, 71 tests) utilizing MagicMock patches on HTTP and database connections.
* **Ad-hoc scripts**: `teste_discovery_vonix.py`, `mapear_filas_vonix.py`, `listar_filas.py`, `coleta_vonix_completa.py`, `diagnostico_vonix.py`.

### 9.1 Placement Recommendation
Unit tests targeting zero-consumption scenarios (e.g., verifying that functions in `cleaning_vonix.py` handle empty strings, `None` arguments, and missing HTML nodes by returning empty defaults without crashing) should be placed in:
1. **`tests/test_cleaning_vonix.py`**: This is the existing unit test file for Vonix parsing/cleaning logic. Adding tests for `limpar_chamadas`, `get_agressividade`, `get_tech`, `get_cliente_nome`, and `dict_agentes` here maintains test suite structure and clarity.
2. Alternatively, if we wish to keep them completely separate, a new test file named **`tests/test_vonix_zero_consumption.py`** can be created.
