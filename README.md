# Rivex

> Plataforma de automação ETL para coleta, higienização, validação (Pydantic) e carga de dados operacionais de **discadores telefônicos** diretamente no **PostgreSQL**.

---

## O que é o Rivex?

O **Rivex** substitui o processo manual de extração de indicadores operacionais de telefonia por pipelines automatizados em Python.

O sistema executa a coleta via **APIs REST**, **Server SDK** e **requisições HTTP autenticadas**, valida os dados em modelos canônicos **Pydantic** (`ClienteRegistro` e `OperadorRegistro`) e realiza o carregamento idempotente (`UPSERT`) no **PostgreSQL**.

---

## Sistemas Suportados

Atualmente, o orquestrador principal (`main.py`) suporta **3 discadores**:

| Categoria | Sistema | Flag CLI (`--pipeline`) | Método de Coleta | Destino no PostgreSQL |
|-----------|---------|-------------------------|------------------|-----------------------|
| **Discador** | **Callix** | `callix` | API REST v1 + Server SDK v1 + API v4 (paralelo via `ThreadPoolExecutor`) | `clientes.clientes_callix`, `clientes.vw_clientes_ativos`, `dados_discador.chamadas_cliente_callix`, `dados_discador.chamadas_agente_callix` |
| **Discador** | **IPBox** | `ipbox` | Sessão HTTP + Parsing HTML (`BeautifulSoup`) + Relatório JSON | `dados_discador.chamadas_cliente_ipbox`, `dados_discador.chamadas_agente_ipbox` |
| **Discador** | **Vonix** | `vonix` | Requisições HTTP + Parsing HTML (`BeautifulSoup`) | `dados_discador.chamadas_cliente_vonix`, `dados_discador.chamadas_agente_vonix` |

> **Nota sobre `SincroniaCallix`:** o módulo de sincronização automática de tokens (`SincroniaCallix`, hoje em `deprecated/callix_v1/`) está **temporariamente suspenso devido a limitações impostas pela discadora responsável**. O pipeline do Callix lê os clientes ativos e tokens diretamente da view `clientes.vw_clientes_ativos`.

---

## Arquitetura do Projeto

```text
Rivex/
├── main.py                                  # Ponto de entrada CLI (--pipeline callix|ipbox|vonix|all --data YYYY-MM-DD)
├── run_rivex.bat                            # Script de execução agendada (Windows Task Scheduler)
├── requirements.txt                         # Dependências de produção
├── requirements-dev.txt                     # Dependências de desenvolvimento/testes
├── .env.example                             # Modelo de variáveis de ambiente
├── src/
│   └── rivex/
│       ├── config/                          # Carregamento e validação centralizada de Settings
│       ├── domain/                          # Modelos Pydantic (ClienteRegistro, OperadorRegistro), exceções e PipelineProtocol
│       ├── pipeline/
│       │   └── pipeline_discador/
│       │       ├── pipeline_callix.py       # Orquestração ETL do Callix (paralelo + SDK)
│       │       ├── pipeline_ipbox.py        # Orquestração ETL do IPBox
│       │       └── pipeline_vonix.py        # Orquestração ETL do Vonix
│       ├── environments/
│       │   └── discadores/
│       │       ├── Callix/                  # Coleta API v1, Server SDK v4, URLs e payloads
│       │       ├── IPBox/                   # Sessão HTTP, payloads e coleta de relatórios IPBox
│       │       └── vonix/                   # Coleta HTTP e payloads Vonix
│       ├── data_processing/                 # Higienização e transformação em modelos Pydantic (Callix, IPBox, Vonix)
│       ├── database/                        # Conexão PostgreSQL (context manager) e repositórios (DDL + UPSERT)
│       └── utils/                           # Cliente HTTP resiliente (retry 429/5xx), datas e logging ETL com redação
└── tests/                                   # Testes unitários com pytest
```

---

## Como Funciona Cada Pipeline

### 1. Callix (`PipelineCallix`)
1. **Leitura de Clientes Ativos (`DatabaseClientes`):** consulta `clientes.vw_clientes_ativos` e encerra a conexão antes da coleta HTTP.
2. **Extração Paralela (`coletar_clientes_paralelo`):** executa até 5 clientes em paralelo combinando:
   - **API v1 (`CallixAPICollector`):** campanhas e métricas agregadas de chamadas.
   - **Server SDK + API v4 (`CAllixRequisition`):** cria sessão temporária (`/sdk/v1/server/user-session`), coleta contas (`operadores_contratados`, `valor_operador`), rotas de saída (`tech`, `rota_cliente`), agressividade e histórico paginado de performance por agente, encerrando a sessão no bloco `finally`.
   - **Rate limit (`HTTP 429`):** aguarda 60 segundos (ou `Retry-After`) e realiza até 5 tentativas antes de falhar.
3. **Transformação e Carga:** valida nos modelos `ClienteRegistro` e `OperadorRegistro` e executa `UPSERT` em `dados_discador.chamadas_cliente_callix` e `dados_discador.chamadas_agente_callix`.

### 2. IPBox (`PipelineIpbox`)
1. **Autenticação e Listagem (`IpboxInit`):** inicia sessão HTTP autenticada no servidor IPBox e valida o retorno de login.
2. **Coleta (`IpboxClientConfig`):** extrai o relatório geral de agentes em JSON e, para cada cliente, coleta chamadas, agressividade e operadores contratados.
3. **Transformação e Carga (`limpeza_ipbox.py` + `DatabaseIpbox`):** associa agentes por igualdade normalizada, valida em `ClienteRegistro` / `OperadorRegistro` (com ID randômico de até 5 dígitos caso `tech` não seja encontrada) e persiste no PostgreSQL.

### 3. Vonix (`PipelineVonix`)
1. **Autenticação (`ExecucaoVonix`):** valida o login, obtém a lista de filas ativas e carrega `/admin/routes` uma única vez por execução.
2. **Coleta e Higienização (`cleaning_vonix.py`):** coleta chamadas totais, completas, abandonadas, recusadas, agentes e agressividade por fila, descartando coletas 100% duplicadas e atribuindo ID randômico de até 5 dígitos quando a `tech` não puder ser resolvida.
3. **Carga (`DatabaseVonix`):** persiste `ClienteRegistro` e `OperadorRegistro` no PostgreSQL.

---

## Configuração do Ambiente

### 1. Pré-requisitos
- **Python 3.11+**
- **PostgreSQL** acessível com os schemas `clientes` e `dados_discador`

### 2. Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 3. Variáveis de Ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto com base em `.env.example`.

---

## Execução

### Via linha de comando (`main.py`)

```bash
# Executar apenas um pipeline específico (padrão: data de ontem)
python main.py --pipeline callix
python main.py --pipeline ipbox
python main.py --pipeline vonix

# Executar todos os pipelines em sequência para uma data específica
python main.py --pipeline all --data 2026-11-17
```

### Via script agendado no Windows (`run_rivex.bat`)

```bat
run_rivex.bat
```
Executa `.venv\Scripts\python.exe main.py --pipeline all` e redireciona a saída para `logging_execution\system\scheduler\rivex_cron.log`.

---

## Testes

Para executar a suíte de testes automatizados com `pytest`:

```bash
.venv\Scripts\python.exe -m pytest -v
```

Os logs de execução em produção ficam em `logging_execution/` (divididos por `extract/`, `transform/`, `load/`, `pipeline/` e `system/`), com mascaramento automático (`***OCULTO***`) de tokens e credenciais.

---

## Tecnologias Utilizadas

- **Python** — linguagem principal e concorrência (`ThreadPoolExecutor`)
- **Pydantic** — validação estrita e contratos canônicos de dados
- **Requests** — cliente HTTP com sessão, retry de *rate limit* (`429`) e erros `>= 400`
- **BeautifulSoup4** — parsing e higienização de relatórios HTML (Vonix e IPBox)
- **Psycopg2** — driver PostgreSQL com operações transacionais e `UPSERT`
- **Pytest** — testes unitários e de integração

---

## Autor

**Victor Amador Viegas**  
Desenvolvedor — Projeto Rivex
