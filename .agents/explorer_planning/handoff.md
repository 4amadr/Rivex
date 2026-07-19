# Handoff Report: Vonix Dialer Pipeline Analysis

Detailed read-only analysis of the Vonix dialer pipeline architecture, interface contracts, bugs, and tests.

---

## 1. Observation

### A. Codebase Architecture & Data Flow Mapping
The pipeline processes Vonix dialer data in a linear ETL loop:
1. **Config & Token Collection**: `PipelineVonix` initializes configurations and fetches the CSRF authenticity token from the Vonix login page (`/login/signin`) using `ExecucaoVonix.token_pronto()`.
2. **Client Discovery**: The client IDs are fetched from the Vonix dashboard page (`/`) via `ExecucaoVonix.get_clientes()` (which internally uses POST login then GET dashboard).
3. **Queue Selection (Server Context)**: (Currently Broken) The server requires a POST filtering request to `/login/set_show_queue` with the target `queue_id[]` (client ID) to filter subsequent data calls.
4. **Data Collection**: Raw HTML pages are requested for total calls, completed calls, abandoned calls, discarded calls, and agent tables, using dates and parameters.
5. **Data Cleaning**: `cleaning_vonix.py` parses HTML pages using BeautifulSoup to extract statistics:
   - Call counts (extracted via regex matching/string splicing from `div.box-title` inside `#maincontent`).
   - Agressiveness and tech parameters (extracted from the LCR profile form `/admin/queue_edit/{cliente}`).
   - Agent tables (extracted from grid tables).
6. **Database Load**: (Currently Broken/Missing) Cleansed dicts/lists are sent to `DatabaseRivex.envio_banco()` to be inserted/updated (`ON CONFLICT`) into PostgreSQL tables.

### B. Interface Contracts

#### 1. Collection Module (`src/rivex/enviroments/discadores/vonix/fluxo_coleta.py`)
- **`ExecucaoVonix.__init__(self, login, senha, data, url_base)`**
  - **Parameters**: 
    - `login` (str)
    - `senha` (str)
    - `data` (str, formatted as `DD/MM/YYYY`)
    - `url_base` (str)
  - **Attributes**: 
    - `self.session` (`requests.Session`)
    - `self.url` (`GerarUrlVonix`)
    - `self.http_requisitions` (`HttpRequisitions`)
- **`ExecucaoVonix.token_pronto(self) -> str`**
  - Fetches the login page cookie and returns the `authenticity_token` string.
- **`ExecucaoVonix.login_vonix(self, token: str) -> requests.Response`**
  - Authenticates session using POST payload.
- **`ExecucaoVonix.get_clientes(self, token: str) -> str`**
  - Performs login and fetches dashboard page, returning its HTML content.
- **`ExecucaoVonix.get_filtragem(self, equipe: str, token: str) -> requests.Response`**
  - Sends POST request to select a client context.
- **`ExecucaoVonix.get_chamadas(self, tipo_chamada: str | None = None) -> requests.Response`**
  - Fetches calls report HTML. `tipo_chamada` can be `None`, `"completed"`, `"abandon"`, or `"discard"`.
- **`ExecucaoVonix.get_agentes(self) -> requests.Response`**
  - Fetches agent table HTML.
- **`ExecucaoVonix.coleta_de_agressividade_vonix(self, cliente: str, token: str) -> requests.Response`**
  - Fetches LCR and aggressiveness page HTML.

#### 2. Cleaning Module (`src/rivex/data_processing/Vonix/cleaning_vonix.py`)
- **`gerar_lista_de_clientes(html: str) -> list[str]`**
  - Returns a list of cleaned queue/client IDs (e.g. `['tcrepresentacao', 'realpromotora']`).
- **`limpar_chamadas(html: str) -> str`**
  - Parses call count from raw calls page HTML. Returns string representation of count (e.g. `'259'`).
- **`get_agressividade(html: str) -> str`**
  - Extracts current queue speed input value (e.g., `'1.5'`).
- **`get_tech(html: str) -> str`**
  - Extracts the selected tech/LCR prefix numeric code (e.g., `'123401'`).
- **`get_cliente_nome(html: str) -> str`**
  - Extracts and returns a normalized alphabetical name of the client (e.g., `'TC Representacao'`).
- **`dict_agentes(html: str) -> list[dict]`**
  - Parses agent status grid table and returns a list of dictionaries with keys:
    - `"agente"` (str, e.g. `'Nome Agente (ramal)'`)
    - `"chamadas"` (str, e.g. `'259'`)

#### 3. Database Module (`src/rivex/database/database.py`)
- **`DatabaseRivex.abrir_banco(self) -> tuple[cursor, connection]`**
  - Connects to database and returns a DB cursor and connection object.
- **`DatabaseRivex.envio_banco(self, chamadas: dict, desempenho_do_agente: list[dict], cursor) -> bool`**
  - Executes inserts for both client statistics and agent data, then commits transaction.
- **`DatabaseRivex.fechar_db(self, cursor, conexao) -> None`**
  - Safely closes database connections.

---

### C. Bugs and Discrepancies
Based on `ORIGINAL_REQUEST.md`, several critical bugs, logic discrepancies, and syntax issues exist:

#### 1. In `fluxo_coleta.py` (Wrong Property Reference)
- **Line 57-60**:
  ```python
  def get_clientes_ambiente(self):
      return self.http_requisitions.requisicao_get(payload_get={},
                                                   headers={},
                                                   url=self.url.url_base)
  ```
  While `self.url.url_base` is accessible as a string property on `GerarUrlVonix`, the helper class defines a method `_url_base()` (line 18) meant to act as the getter. The reference is inconsistent with other helper calls (like `_url_login()`).

#### 2. In `pipeline_vonix.py` (Missing Client-Context Switching / Filter POST)
- **Line 62-73**:
  ```python
  def execucao_vonix(self):
      lista_clientes, token = self.inicial_config()
      for cliente in lista_clientes:
          response_dict = self.get_dados_sujos(cliente, token)
          ...
  ```
  The loop iterates over `lista_clientes` and directly calls `get_dados_sujos`. Crucially, it does **not** call `self.vonix_execucao.get_filtragem(cliente, token)` before fetching call or agent data. 
  Because Vonix is stateful and stores queue configuration in session cookies/server-side sessions, the server fails to filter. The pipeline retrieves call and agent HTML statistics only for the default (or last filtered) queue on every iteration, leading to repeated identical data for all clients.

#### 3. In `pipeline_vonix.py` (Missing Database Insertion Load Step)
- `execucao_vonix` calls cleaning functions:
  ```python
  aceitas = self.execucao_limpeza_chamadas_vonix(...)
  tabela = self.execucao_limpeza_agentes_vonix(...)
  ```
  However, it completely omits any call to `DatabaseRivex.envio_banco()` or any database-related logic. Collected and cleaned data is simply discarded at the end of each iteration.

#### 4. In `cleaning_vonix.py` (Zero Consumption Crash Points)
Days with zero consumption/no calls cause the HTML to lack key tags, leading to hard exceptions:
- **`limpar_chamadas`**:
  ```python
  def limpar_chamadas(html):
      chamadas_html = get_html(html)
      div_dados = entrar_na_div(chamadas_html)
      chamadas_com_texto = chamadas_em_texto(div_dados)
      return remover_texto_chamadas(chamadas_com_texto.text)
  ```
  If no calls occur, `<div class="box-title">` is absent. `chamadas_com_texto` becomes `None`, and calling `.text` on `None` throws:
  `AttributeError: 'NoneType' object has no attribute 'text'`.
- **`dict_agentes`**:
  ```python
  def dict_agentes(html):
      tabela = encontrar_tabela_agentes(html)
      lista_infos = gerar_lista_infos_agentes(tabela)
      return gerar_dados_agentes(lista_infos)
  ```
  If agents are inactive or the table is not found, `tabela` is `None`. `gerar_lista_infos_agentes` tries to call `tabela.find_all(...)`, throwing:
  `AttributeError: 'NoneType' object has no attribute 'find_all'`.

#### 5. In `database.py` (PostgreSQL Insert Mismatches & Syntax Errors)
- **`query_chamadas` (Line 41-51)**:
  ```sql
  INSERT INTO dados_discador.chamadas_cliente (tech_cliente, cliente_nome, data, discador, chamadas, completas, recusadas, abandonadas, agressividade)
  VALUES (%(tech)s, %(Cliente)s, %(Data)s, %(Chamadas totais)s, %(Chamadas aceitas)s, %(Chamadas recusadas)s, %(Chamadas abandonadas)s, %(Agressividade)s)
  ```
  The column list specifies **9 columns**, but the `VALUES` clause provides only **8 placeholders** (`discador` is missing its placeholder).
- **`query_agentes` (Line 52-58)**:
  ```sql
  INSERT INTO dados_discador.chamadas_agente (tech, cliente_nome, discador, data, nome_agente, chamadas_agente)
  SELECT %(tech)s, %(Cliente)s ,%(Data)s, %(Nome do agente)s, %(Chamadas aceitas do agente)s
  ```
  The column list specifies **6 columns**, but the `SELECT` clause lists only **5 values** (`discador` is missing). It also improperly uses `SELECT` instead of `VALUES` for parameter insertion.
- **Key Mismatch in `envio_banco`**:
  - `query_chamadas` expects keys: `tech`, `Cliente`, `Data`, `Chamadas totais`, `Chamadas aceitas`, `Chamadas recusadas`, `Chamadas abandonadas`, `Agressividade`.
  - But `execucao_limpeza_chamadas_vonix` returns keys: `"Tech"`, `"Data"`, `"chamadas"`, `"aceitas"`, `"recusadas"`, `"abandonadas"`, `"agressividade"` (Note the missing `Cliente` or `cliente_nome` entirely, case differences, and lack of `discador` value).
  - Similarly, the database execution loop for agents:
    ```python
    for agente in desempenho_do_agente:
        cursor.execute(self.query_agentes, agente)
    ```
    passes `agente` dict which only contains `{"agente": "...", "chamadas": "..."}`. The query expects `tech`, `Cliente`, `Data` on the same dictionary, causing immediate key lookup failures during execution.
- **`inserir_consumo` Syntax Errors (Line 71-102)**:
  - Missing comma between `%(discador)s` and `%(operadora)s` on line 87-88.
  - Missing comma after `discador = EXCLUDED.cliente` on line 97.
  - Logical mismatch: `discador = EXCLUDED.cliente` maps the wrong column value.

#### 6. Naming Collisions and Unused Code
- **Naming Collision**: Both `src/rivex/enviroments/discadores/vonix/equipes_vonix.py` and `src/rivex/data_processing/Vonix/cleaning_vonix.py` define `dict_agentes` (one as a dictionary mapping configuration, one as a cleanup function). When imported via wildcard (`*`), the function overwrites the dictionary, making the config lookup impossible.
- **Unused Class**: `fluxo_limpeza.py:LimpezaVonix` is defined but completely unused by the pipeline.
- **Unused Files**: `cleaner.py` and `faxina.py` are build utility scripts and do not belong in the source code directories.
- **Duplicate Imports**: `main.py` imports `load_dotenv` twice (Line 4 and Line 19).

### D. Test Review
- **`tests/test_http.py`**:
  Contains four test functions, but all are named `test_timeout_error`:
  ```python
  def test_timeout_error():
      with pytest.raises(TimeoutError):
          hr.analista_de_erros(429)

  def test_timeout_error():
      with pytest.raises(ValueError):
          hr.analista_de_erros(401)
  ...
  ```
  In Python and Pytest, defining functions with identical names in the same module overwrites previous definitions. Only the last test (checking 500 status code to ConnectionError) is actually registered and run by Pytest. The other three assertions are silently ignored.
- **No Zero Consumption/Mock Tests**:
  No tests exist to pass minimal or empty HTML bodies to the cleaning functions (e.g. `limpar_chamadas` or `dict_agentes`) to verify they return default values (`0` and `[]` respectively) rather than crashing.

---

## 2. Logic Chain

1. **Session-Level Queues**: Vonix utilizes session cookies (specifically Rails sessions) to store which queue's statistics are active. We verified this in the test diagnostics (`diagnostico_vonix.py` and `coleta_vonix_completa.py`). When the pipeline makes requests to `/calls` and `/agents/calls_overview` without invoking `/login/set_show_queue` via POST, the server serves data for the default/last queue. Since the pipeline loop does not call `get_filtragem` for each client, it is guaranteed to retrieve duplicate data for all clients.
2. **Missing Database Integration**: In `pipeline_vonix.py`, the return values `aceitas` (client calls data) and `tabela` (agent data) are locally scoped and never passed to a database wrapper. Thus, the database pipeline step is fully disconnected.
3. **Database Insertion Crashes**: Comparing `DatabaseRivex` queries with the dictionaries returned by cleaning functions reveals a schema/key mismatch. 
   - `query_chamadas` specifies 9 columns but only 8 values. The `discador` column is missing a placeholder.
   - The dictionary returned from `execucao_limpeza_chamadas_vonix` lacks the `"cliente_nome"` and `"discador"` keys.
   - `query_agentes` specifies 6 columns but only 5 select parameters (missing `discador`), uses incorrect `SELECT` syntax, and expects client-level keys (`tech`, `Cliente`, `Data`) to reside in the individual agent dictionaries, which only contain agent-specific keys (`agente`, `chamadas`).
   - Consequently, running the database insertions will trigger SQL syntax exceptions and Python `KeyError` exceptions.
4. **Zero Consumption Crashes**: The BeautifulSoup lookup paths in `cleaning_vonix.py` call `.text` and `.find_all()` on the result of `find()` operations without checking if those results are `None`. On days with no dialer activity, these tags are missing, leading directly to `AttributeError` failures.
5. **Overwritten Tests**: Pytest parses modules sequentially and binds the function name to the last defined function object. Since all four test functions in `tests/test_http.py` share the exact name `test_timeout_error`, only one test execution occurs.

---

## 3. Caveats
- **Live Environment**: As this is a read-only investigation, we could not connect to a live Vonix server to run live API calls or check real-time rate limiting.
- **PostgreSQL Connection**: The credentials in `.env` were analyzed, but no direct database queries were executed on a live PostgreSQL database.
- **IPBox/Callix Codebase**: We focused exclusively on the Vonix dialer pipeline. Other dialers (IPBox, Callix) were only examined for directory layout compliance.

---

## 4. Conclusion
The Vonix pipeline contains structural flaws that prevent correct client execution and data insertion:
1. **Loop Filter Execution**: The pipeline must call `get_filtragem` at the start of each iteration to switch server context.
2. **Database Query Repairs**: Mismatched columns in `query_chamadas` and `query_agentes`, incorrect select syntax, and formatting in `inserir_consumo` must be corrected.
3. **Dictionary Context Aggregation**: The pipeline must construct/aggregate dictionaries matching SQL placeholders, ensuring client data (`tech`, `cliente_nome`, `data`, `discador`) is combined with agent data.
4. **Robust Soup Parsing**: Cleaning functions must verify element existence before calling properties/attributes to handle empty/zero data days gracefully.
5. **Fix Test Names**: `tests/test_http.py` must have unique test function names. New unit tests with minimal/empty HTML must be written to assert zero-consumption behavior.

---

## 5. Verification Method

### 1. Verification Commands
Run the following commands to check for syntax/import errors and run repaired tests:
- **Import Check**:
  ```powershell
  python -c "from src.rivex.pipeline.pipeline_discador.pipeline_vonix import PipelineVonix; print('Import OK')"
  ```
- **Run Pytest Suite**:
  ```powershell
  python -m pytest tests/
  ```

### 2. Files to Inspect
Inspect the corrected files post-implementation to verify schema compliance and function naming:
- `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py`
- `src/rivex/database/database.py`
- `src/rivex/data_processing/Vonix/cleaning_vonix.py`
- `tests/test_http.py`
- `src/rivex/enviroments/discadores/vonix/equipes_vonix.py`

### 3. Invalidation Conditions
The verification fails if:
- Pytest does not run at least 4 test cases for `test_http.py`.
- Running the pipeline loop generates `AttributeError` exceptions when processing simulated empty HTML content.
- Database execution triggers column count mismatch errors or `KeyError` exceptions when binding dictionary parameters.
