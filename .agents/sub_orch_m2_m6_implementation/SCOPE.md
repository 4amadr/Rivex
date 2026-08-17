# Scope: Milestones 2-6 - Implementation, Database, and Cleanup

## Architecture
- Module: `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py`
- Module: `src/rivex/database/database.py`
- Module: `src/rivex/environments/discadores/vonix/fluxo_coleta.py`
- Module: `src/rivex/environments/discadores/vonix/fluxo_limpeza.py`
- Module: `src/rivex/environments/discadores/vonix/equipes_vonix.py`
- Module: `main.py`

## Milestones
| # | Name | Scope | Status |
|---|------|-------|--------|
| 2.1 | `cliente_nome` in Cleanup Dict | Include `cliente_nome` (using the extracted `nome_cliente` value) inside the dict returned by `execucao_limpeza_chamadas_vonix` | PLANNED |
| 2.2 | Schema Creation | Execute `CREATE SCHEMA IF NOT EXISTS dados_discador;` inside `DatabaseRivex.envio_banco` before creating tables, and `CREATE SCHEMA IF NOT EXISTS dados_operadora;` inside `enviar_banco_operadoras` | PLANNED |
| 2.3 | Resolve Naming Collision | Rename `dict_agentes` dictionary in `equipes_vonix.py` to `mapeamento_equipes_vonix`, update reference in `tests/teste_discovery_vonix.py`, and remove unused imports of `dict_agentes` from `fluxo_coleta.py` and `main.py` | PLANNED |
| 2.4 | Remove Unused Code & Files | Delete `LimpezaVonix` class from `fluxo_limpeza.py`; delete unused files `cleaner.py` and `faxina.py` under `src/rivex/utils/infra_utils/`; remove duplicate `load_dotenv` import from `main.py` | PLANNED |
| 2.5 | Print to Logging | Replace `print()` statements with `logging` calls consistently across `pipeline_vonix.py`, `database.py`, `fluxo_coleta.py`, and `cleaning_vonix.py` | PLANNED |
| 2.6 | Verification | Run all tests (unit and E2E) and pass them with a CLEAN Forensic Audit | PLANNED |

## Interface Contracts
- `execucao_limpeza_chamadas_vonix(...) -> dict` contains key `"cliente_nome"`.
- `DatabaseRivex` creates schemas dynamically on startup.
- Logging setup is imported and used in place of print.
