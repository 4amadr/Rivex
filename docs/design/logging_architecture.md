# Design Doc: Arquitetura Centralizada de Logging do Rivex

**Veredito do teste de três condições:** Justificado porque (1) o formato de diretórios/arquivos e o contrato de redação de credenciais são caros de reverter após automações/monitoramento dependerem deles, (2) cruzam todos os módulos (`extract`, `transform`, `load`, `pipeline`, `system`) e (3) a motivação de proteção de credenciais e isolamento por serviço não seria óbvia apenas lendo os *call sites*.

---

## 1. Problema e Requisitos

### Contexto
O projeto acumulava `print()` esparsos em pipelines e banco de dados, configurações locais duplicadas (`_configurar_logger()`, `logging.basicConfig`) apontando para pastas legadas (`Log/ipbox_log`, `Log/vonix_log`, `Log/req-log`, `logging_execution/`), e ausência de redação consistente em URLs, strings livres e mensagens de erro.

### Requisitos
- **REQ-1 (Limpeza total):** Nenhum `print()` ou configuração paralela de `logging` (`basicConfig`, `FileHandler` ad-hoc) deve existir fora de `src/rivex/utils/logging_config/`.
- **REQ-2 (Estrutura hierárquica):** Todos os logs em arquivo devem residir em `logging_execution/` divididos por etapa/serviço (`extract/{callix,ipbox,vonix}`, `transform/{callix,ipbox,vonix}`, `load/{callix,ipbox,vonix,database}`, `pipeline/{executions,errors}`, `system/{scheduler,database}`).
- **REQ-3 (Nomenclatura padrão):** Cada arquivo deve seguir `log_<categoria>_<servico>_<YYYY-MM-DD>_<HHMMSS>.log`.
- **REQ-4 (Proteção de credenciais):** Headers, payloads, URLs (query string e credenciais URI) e mensagens em texto livre devem mascarar chaves sensíveis (`authorization`, `token`, `password`, `senha`, `secret`, `api_key`, `userSessionToken`, `cookie`) com `***OCULTO***`.
- **REQ-5 (Logs explicativos e de erro):** Eventos devem incluir contexto operacional (serviço, método/operação, status, duração em ms, cliente, contagens) e espelhar registros `ERROR+` em `pipeline/errors/`.
- **REQ-6 (Criação sob demanda):** Arquivos não devem ser criados vazios caso o serviço ou fluxo de erro não seja acionado na execução.

### Estimativa de Volume (Back-of-the-Envelope)
- **Assunções:** 3 discadores (`callix`, `ipbox`, `vonix`), média de ~30 clientes ativos por discador, 1 execução diária agendada via `run_rivex.bat`.
- **Volume por execução:** ~15–20 requisições HTTP por cliente × 30 clientes ≈ 500–600 linhas de log em `extract/`, ~60 linhas em `transform/`, ~30 linhas em `load/` e ~100 linhas em `pipeline/executions/`. Total ≈ **< 1.000 linhas/dia (~150–250 KB/dia)**.
- **Retenção anual estimada:** ~90 MB/ano em disco local; custo de armazenamento desprezível, dominado apenas por I/O de abertura de arquivos se não houver rotação/limpeza periódica.

---

## 2. Design Proposto

### Contrato Público (`src/rivex/utils/logging_config`)
- `build_log_filepath(categoria, servico, base_dir, execution_dt) -> Path`
- `get_service_logger(categoria, servico, level, base_dir, execution_dt, mirror_errors=True) -> logging.Logger`
- Facades tipadas por camada:
  - `ExtractLogger(servico)` — `registrar_requisicao(...)`, `registrar_falha(...)`
  - `TransformLogger(servico)` — `registrar_limpeza_chamadas(...)`, `registrar_limpeza_agente(...)`, `registrar_erro_transformacao(...)`
  - `LoadLogger(servico)` — `registrar_envio_db(...)`, `registrar_erro_db(...)`
  - `PipelineLogger(servico)` — `inicio(...)`, `etapa(...)`, `aviso(...)`, `erro(...)`, `fim(...)`
  - `SystemLogger(servico)` — `info(...)`, `aviso(...)`, `erro(...)`
  - `LoggingDatabaseConfig(servico)` — compatibilidade com módulos de banco existentes.
- Redação (`redaction.py`): `redact_value`, `redact_url`, `redact_text`, `SensitiveDataFilter`.

### Internals
1. Cada logger recebe nome `rivex.<categoria>.<servico>` com `propagate = False`, evitando duplicação no root logger.
2. `logging.FileHandler(..., encoding="utf-8", delay=True)` garante criação preguiçosa do arquivo somente no primeiro registro emitido.
3. `SensitiveDataFilter` é anexado a todos os handlers (serviço e `pipeline/errors`) para atuar como última linha de defesa sobre `record.msg` e `record.args`.
4. Todos os loggers de serviço compartilham o handler de `pipeline/errors` (nível `ERROR`), centralizando falhas de toda a execução em um único arquivo para triagem rápida.

---

## 3. Alternativas e Trade-offs

| Alternativa | Melhor caso | Por que perdeu / Trade-off |
|---|---|---|
| **A. `logging` padrão + `SensitiveDataFilter` + facades (Escolhida)** | Zero dependências externas, compatível com Python 3.13 já instalado e com as facades existentes (`ExtractLogger`, `TransformLogger`, etc.). | Menos flexível que `structlog` para pipelines JSON puros, mas atende 100% dos requisitos sem alterar o ambiente. |
| **B. Adotar `structlog` com processadores JSON** | Melhor ergonomia para ingestão em ELK/Datadog/Loki e encadeamento de contexto (`bind`). | Introduz nova dependência no `.venv`/deploy e exigiria reescrever todos os formatters e contratos atuais para benefício não utilizado (logs locais em arquivo). |
| **C. Manter `FileHandler` por módulo (`pipeline_ipbox.py`, `pipeline_vonix.py`)** | Nenhuma camada central para manter. | Causa duplicação de código, caminhos inconsistentes (`Log/` vs `logging_execution/`) e vazamento de credenciais por falta de filtro único. |

---

## 4. Recomendação

Adotar a **Alternativa A** (`logging` da stdlib centralizado em `src/rivex/utils/logging_config/` com `SensitiveDataFilter` e `delay=True`), atendendo diretamente `REQ-1` a `REQ-6`.
- **O que mudaria a decisão:** Caso o Rivex passe a enviar logs para um coletor centralizado (Loki/Datadog/CloudWatch), recomenda-se adicionar um formatter JSON mantendo as mesmas facades.
- **Teto do design:** ~50.000 linhas por execução única ou concorrência multi-processo escrevendo no mesmo arquivo; o primeiro gargalo será contenção de lock de arquivo no Windows, resolvido com `RotatingFileHandler` ou `QueueHandler`.

---

## 5. Não-Objetivos (Non-Goals)

- Ingestão em tempo real para serviços externos (Datadog, Sentry, CloudWatch).
- Política automática de retenção/exclusão de arquivos antigos em `logging_execution/` (pode ser adicionada depois via cron/tarefa).
- Correção de testes legados pré-existentes que falham por refatorações anteriores não relacionadas a logging (`test_e2e_suite.py`, `test_callix_rate_limit.py`, `test_cleaning_vonix.py`, `test_http.py`).

---

## 6. Riscos e Mitigações (Análise por Inversão)

1. **Vazamento de nova chave de credencial não listada em `SENSITIVE_KEYS`:**
   - *Sinal de alerta:* Aparecimento de chaves com sufixos como `auth`, `key`, `pass` em texto claro nos logs de `extract/`.
   - *Mitigação:* `_is_sensitive_key` verifica substrings (`token`, `password`, `senha`, `secret`, `apikey`, `api_key`, `authorization`) além do conjunto exato, e `redact_text` mascara padrões `Bearer`/`key=value` e credenciais em URI.
2. **Acúmulo indefinido de arquivos `.log` em `logging_execution/`:**
   - *Sinal de alerta:* Diretório `logging_execution/` ultrapassar 500 MB ou > 5.000 arquivos.
   - *Mitigação:* Uso de `delay=True` evita arquivos vazios; retenção pode ser adicionada no scheduler sem alterar o contrato.
3. **Execuções múltiplas no mesmo segundo colidindo no mesmo arquivo:**
   - *Sinal de alerta:* Mensagens de dois processos diferentes intercaladas no mesmo `.log`.
   - *Mitigação:* Aceito para o caso de uso atual (execução sequencial via `main.py` / `run_rivex.bat`).

---

## 7. Rollout e Rollback

- **Rollout:** Implementado diretamente em `src/rivex/utils/logging_config/` com atualização dos pontos de chamada em `main.py`, `database/`, `environments/`, `data_processing/`, `utils/` e `pipeline/`. Validado por testes unitários em `tests/test_logging_config.py`.
- **Critério de Rollback:** Se qualquer pipeline falhar na inicialização com `PermissionError`/`FileNotFoundError` ou `ImportError` relacionado a logging em > 1 execução consecutiva dentro de 24h, reverter o commit de logging.
- **Ponto sem retorno:** Após scripts externos ou monitoramento passarem a consumir os caminhos de `logging_execution/<categoria>/<servico>/`.

---

## 8. Questões em Aberto

- Definir política de retenção (ex.: compactar ou remover logs em `logging_execution/` com mais de 30 ou 90 dias).
- Avaliar se `run_rivex.bat` deve redirecionar stdout/stderr para `logging_execution/system/scheduler/` em vez de `logs\rivex_cron.log`.
