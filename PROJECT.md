# Project: Rivex Vonix Pipeline Fixes

## Architecture
The Rivex Vonix Dialer Pipeline consists of four main functional blocks:
1. **Data Collection (`fluxo_coleta.py`)**: Responsible for establishing a session, logging into Vonix, selecting the current client/queue context via the `/login/set_show_queue` endpoint, and retrieving raw HTML call reports, agent tables, and aggressiveness/tech details.
2. **Data Cleaning (`cleaning_vonix.py`)**: Responsible for parsing raw HTML reports using BeautifulSoup, extracting call statistics (total, completed, abandoned, refused), agent performance lists, aggressiveness, and tech prefixes, and formatting them into structured dictionaries.
3. **Database Layer (`database.py`)**: Responsible for connecting to PostgreSQL, preparing SQL statements with `ON CONFLICT DO UPDATE` upsert logic, creating schemas/tables, and executing batch insertions.
4. **Orchestration (`pipeline_vonix.py`)**: Responsible for opening a database connection, retrieving the client list, iterating through clients to set context, collect, clean, and insert into the database, and closing the connection.

## Code Layout
- `src/rivex/enviroments/discadores/vonix/` — Vonix collection endpoints, discovery, configuration.
- `src/rivex/data_processing/Vonix/` — HTML parsing and data extraction logic.
- `src/rivex/database/` — Database DDL, upserts, connection management.
- `src/rivex/pipeline/pipeline_discador/` — ETL pipeline orchestrators.
- `tests/` — Unit and integration tests.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Fix Client Data Retrieval | Fix wrong url property reference in `fluxo_coleta.py`, and extract client list correctly in `cleaning_vonix.py` | None | PLANNED |
| 2 | Fix Agent Loop Context | Add `/login/set_show_queue` context selection POST request inside client loop in `pipeline_vonix.py` | M1 | PLANNED |
| 3 | Handle Zero Consumption | Prevent `AttributeError` on empty HTML by returning `0` and empty lists | None | PLANNED |
| 4 | Database Load Implementation | Correct column counts and SELECT syntax in `database.py`, integrate DB connection and insertion in `pipeline_vonix.py` | M1, M2, M3 | PLANNED |
| 5 | Code Optimization and Cleanup | Resolve `dict_agentes` name collision, delete unused files (`cleaner.py`, `faxina.py`), remove duplicate imports in `main.py`, replace prints with logging | M4 | PLANNED |
| 6 | E2E Integration and Hardening | Pass 100% of Tiers 1-4 tests and perform Tier 5 adversarial coverage hardening | M1-M5, E2E Test Suite | PLANNED |

## Interface Contracts

### Collection ↔ Cleaning
- `ExecucaoVonix.get_clientes(token) -> str (HTML)`
- `gerar_lista_de_clientes(html) -> list[str]`
- `ExecucaoVonix.get_chamadas(tipo_chamada) -> Response`
- `limpar_chamadas(html) -> str (integer value)`
- `ExecucaoVonix.get_agentes() -> Response`
- `dict_agentes(html) -> list[dict]`
- `ExecucaoVonix.coleta_de_agressividade_vonix(cliente, token) -> Response`
- `get_agressividade(html) -> str (float value)`
- `get_tech(html) -> str (numeric string)`
- `get_cliente_nome(html) -> str`

### Pipeline ↔ Database
- `DatabaseRivex.abrir_banco() -> (cursor, connection)`
- `DatabaseRivex.envio_banco(chamadas: dict, desempenho_do_agente: list[dict], cursor) -> bool`
- `DatabaseRivex.fechar_db(cursor, connection)`

#### Output Schema for `chamadas_clientes` (dictionary passed to `envio_banco`)
- `tech_clientes`: integer (e.g. `123401`)
- `cliente_nome`: text
- `data`: date (`YYYY-MM-DD` format or datetime.date)
- `discador`: text (static `'vonix'`)
- `chamadas` (total): integer
- `completas`: integer
- `recusadas`: integer
- `abandonadas`: integer
- `agressividades`: float

#### Output Schema for `chamadas_agente` (individual dicts in list passed to `envio_banco`)
- `tech`: integer (same as above)
- `cliente_nome`: text
- `data`: date
- `discador`: text (static `'vonix'`)
- `nome_agente`: text
- `chamadas_agente`: integer
