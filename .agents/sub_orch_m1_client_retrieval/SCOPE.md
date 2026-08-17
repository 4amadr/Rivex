# Scope: Milestone 1 - Fix Client Data Retrieval

## Architecture
- Module: `src/rivex/environments/discadores/vonix/fluxo_coleta.py` (fetches raw HTML)
- Module: `src/rivex/data_processing/Vonix/cleaning_vonix.py` (cleans raw HTML client IDs)
- Module: `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py` (orchestrates loop)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1.1 | Fix url property reference | In `fluxo_coleta.py`, change `self.url.url_base` to calling `self.url._url_base()` | None | DONE |
| 1.2 | Update client list extraction | In `cleaning_vonix.py:gerar_lista_de_clientes()`, extract queue/client IDs from `<li id="container_...">` elements and return them to pipeline | None | DONE |

## Interface Contracts
- `ExecucaoVonix.get_clientes_ambiente() -> requests.Response`: must fetch url by calling `self.url._url_base()`.
- `gerar_lista_de_clientes(html: str) -> list[str]`: must return clean queue/client IDs (e.g. `['tcrepresentacao', 'realpromotora']`).
