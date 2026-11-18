# Agitel v1 - Código Desativado

Este diretório armazena a pipeline e os módulos da operadora **Agitel**, desativados e removidos da execução principal (`main.py`).

**Status:** Desativado. Não importar em produção.

## Conteúdo
- `pipeline_agitel.py`: orquestração `ExecAgitel`.
- `environments/`: `sip_client_scrap.py`, `headers_payload.py` (scraping HTTP do portal SIP Agitel).
- `data_processing/agitel_data_cleaning.py`: parsing HTML e higienização de minutagem/custo.
- `database/database_agitel.py`: persistência em `dados_operadora.dados_operadora_agitel`.
