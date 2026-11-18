# Rivex

> Plataforma de automação ETL para coleta, higienização e carga de dados operacionais de **discadores telefônicos** e **operadoras de telefonia** diretamente no **PostgreSQL**.

---

## O que é o Rivex?

O **Rivex** substitui o processo manual de extração de indicadores operacionais de telefonia (que antes consumia cerca de **4 horas por ciclo** com consolidação manual em planilhas) por pipelines automatizados em Python.

O sistema executa a coleta diretamente via **APIs REST**, **Server SDK** e **requisições HTTP autenticadas**, padroniza as métricas de chamadas, agentes, agressividade e consumo tarifário, e realiza o carregamento idempotente (`UPSERT`) no **PostgreSQL**.

---

## Sistemas Suportados

Atualmente, o orquestrador principal (`main.py`) suporta **3 discadores** e **1 operadora de telefonia**:

| Categoria | Sistema | Flag CLI (`--pipeline`) | Método de Coleta | Destino no PostgreSQL |
|-----------|---------|-------------------------|------------------|-----------------------|
| **Discador** | **Callix** | `callix` | API REST v1 + Server SDK v1 + API v4 (paralelo via `ThreadPoolExecutor`) | `clientes.clientes_callix`, `clientes.vw_clientes_ativos`, `dados_discador.chamadas_cliente_callix`, `dados_discador.chamadas_agente_callix` |
| **Discador** | **IPBox** | `ipbox` | Sessão HTTP + Parsing HTML (`BeautifulSoup`) + Relatório JSON | `dados_discador.chamadas_cliente_ipbox`, `dados_discador.chamadas_agente_ipbox` |
| **Discador** | **Vonix** | `vonix` | Requisições HTTP + Parsing HTML (`BeautifulSoup`) + Descoberta de filas/operadores | `dados_discador.chamadas_cliente_vonix`, `dados_discador.chamadas_agente_vonix` |
| **Operadora** | **Agitel** | `agitel` | Scraping HTTP autenticado (`SipClient`) + Parsing HTML (`BeautifulSoup`) | `dados_operadora.dados_operadora_agitel` |

---

## Evolução do Projeto (O que é novo vs. O que foi descontinuado)

### O que há de novo
- **Coleta Callix 100% via API e Server SDK (sem navegador):** autenticação temporária de sessão via `/sdk/v1/server/user-session` e extração das rotas v4 (`accounts`, `campaigns`, `audit-logs`, `outbound-routes`, `campaign-completed-calls`, `user-performance-histories`) com encerramento automático de sessão (`DELETE /api/v4/auth/session`) e tratamento de *rate limit* (`HTTP 429`).
- **Extração paralela no Callix:** coleta simultânea de múltiplos ambientes clientes com `ThreadPoolExecutor(max_workers=5)` e *fallback* automático para a view `clientes.vw_clientes_ativos` caso a API central esteja indisponível.
- **Integração do discador IPBox (`PipelineIpbox`):** coleta automatizada de chamadas, agressividade e produtividade de agentes por cliente/equipe.
- **Integração da operadora Agitel (`ExecAgitel`):** extração diária de minutagem e custo por `tech` e persistência no schema `dados_operadora`.
- **Descoberta de filas e operadores no Vonix:** novos módulos para mapeamento de filas (`vonix_queue_discovery.py`) e extração de operadores ativos por cliente (`/admin/agent_list`).
- **CLI unificada e agendamento (`main.py` e `run_rivex.bat`):** execução individual por pipeline ou completa (`--pipeline all`).
- **Logging ETL estruturado com proteção de segredos:** separação de logs em `Log/extract`, `Log/transform` e `Log/load`, com mascaramento automático (`***OCULTO***`) de tokens, senhas e chaves de API.
- **Suíte de testes automatizados (`pytest`):** cobertura de fluxos de limpeza, sincronização de tokens, *rate limit* e empacotamento.

### O que não é mais utilizado
- **Selenium e WebDriver removidos:** o projeto não utiliza mais automação de navegador nem inspeção manual via DevTools para extrair tokens ou métricas do Callix.
- **Scrapers legados de operadoras descontinuados:** os módulos antigos de `Pentagono`, `Ultracom` e `Gerax/GSolutions`, bem como o arquivo estático `settings.py`, foram removidos do fluxo ativo em favor da arquitetura modular por pipeline.

---

## Arquitetura do Projeto

```text
Rivex/
├── main.py                                  # Ponto de entrada CLI (--pipeline callix|ipbox|vonix|agitel|all)
├── run_rivex.bat                            # Script de execução agendada (Windows Task Scheduler)
├── requirements.txt                         # Dependências Python fixadas
├── .env.example                             # Modelo de variáveis de ambiente
├── src/
│   └── rivex/
│       ├── pipeline/
│       │   ├── pipeline_discador/
│       │   │   ├── pipeline_callix.py       # Orquestração ETL do Callix (paralelo + SDK)
│       │   │   ├── pipeline_ipbox.py        # Orquestração ETL do IPBox
│       │   │   └── pipeline_vonix.py        # Orquestração ETL do Vonix
│       │   └── pipeline_operadora/
│       │       └── pipeline_agitel.py       # Orquestração ETL da operadora Agitel
│       ├── environments/
│       │   ├── discadores/
│       │   │   ├── Callix/                  # Coleta API v1, Server SDK v4 e sincronia de clientes/tokens
│       │   │   ├── IPBox/                   # Sessão HTTP, payloads e coleta de relatórios IPBox
│       │   │   └── vonix/                   # Coleta HTTP, limpeza e descoberta de filas Vonix
│       │   └── operadoras/
│       │       └── agitel/                  # Extração de consumo SIP da Agitel
│       ├── data_processing/                 # Higienização e transformação de dados (Callix, IPBox, Vonix, Agitel)
│       ├── database/                        # Conexão PostgreSQL e repositórios (DDL + UPSERT)
│       └── utils/                           # Cliente HTTP resiliente, datas, BeautifulSoup e logging ETL
└── tests/                                   # Testes unitários e E2E com pytest
```

---

## Como Funciona Cada Pipeline

### 1. Callix (`PipelineCallix`)
1. **Descoberta e Sincronia (`SincroniaCallix`):** consulta as subcontas no servidor central (`/api/v1/sub_accounts`), atualiza o status (`ativo`) em `clientes.clientes_callix` e, para clientes ativos sem token, autentica via HTTP (`/api/v4/auth/session`) para buscar ou gerar o token em `/api/v4/entities/api-tokens`. Se a API central falhar, utiliza a view local `clientes.vw_clientes_ativos`.
2. **Extração Paralela (`coletar_clientes_paralelo`):** executa até 5 clientes em paralelo combinando:
   - **API v1 (`CallixAPICollector`):** campanhas e métricas agregadas de chamadas.
   - **Server SDK + API v4 (`CAllixRequisition`):** cria sessão temporária para um usuário elegível (`/sdk/v1/server/user-session`), coleta rotas de saída (`tech`), agressividade, histórico de performance por agente e encerra a sessão no bloco `finally`.
3. **Transformação e Carga:** higieniza os dados (`cleaner_callix_api.py` e `cleaner_callix_req.py`), empacota via `CallixClientData` e executa `UPSERT` em `dados_discador.chamadas_cliente_callix` e `dados_discador.chamadas_agente_callix`.

### 2. IPBox (`PipelineIpbox`)
1. **Autenticação e Listagem (`IpboxInit`):** inicia sessão HTTP no servidor IPBox e obtém o HTML com a relação de clientes ativos.
2. **Coleta (`IpboxClientConfig`):** extrai o relatório geral de agentes em JSON e, para cada cliente, coleta os dados brutos de chamadas, agressividade e operadores.
3. **Transformação e Carga (`limpeza_ipbox.py` + `DatabaseIpbox`):** filtra os agentes pertencentes à equipe de cada cliente, normaliza os indicadores e grava em `dados_discador.chamadas_cliente_ipbox` e `dados_discador.chamadas_agente_ipbox`.

### 3. Vonix (`PipelineVonix`)
1. **Autenticação (`ExecucaoVonix`):** obtém o token de sessão HTTP e lista os clientes disponíveis, filtrando contas administrativas/manuais.
2. **Coleta e Higienização (`cleaning_vonix.py` / `LimpezaVonix`):** consulta chamadas totais, completas (`completed`), abandonadas (`abandon`) e recusadas (`discard`), além de agentes, agressividade e associação de `tech`.
3. **Carga (`DatabaseVonix`):** persiste os registros em `dados_discador.chamadas_cliente_vonix` e `dados_discador.chamadas_agente_vonix`.

### 4. Agitel (`ExecAgitel`)
1. **Coleta (`SipClient`):** autentica no portal SIP da Agitel e extrai o relatório de consumo por cliente na data selecionada.
2. **Transformação e Carga (`agitel_data_cleaning.py` + `DatabaseAgitel`):** extrai `tech`, `custo` e `minutagem` via `BeautifulSoup` e realiza `UPSERT` em `dados_operadora.dados_operadora_agitel`.

---

## Configuração do Ambiente

### 1. Pré-requisitos
- **Python 3.11+**
- **PostgreSQL** acessível com os schemas `clientes`, `dados_discador` e `dados_operadora`

### 2. Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto (baseado em `.env.example`):

```env
# Banco de Dados PostgreSQL
HOST_DB=
PORT_DB=
DATABASE_CONTECH=
USER_DB=
SENHA_DB=

# Callix
URL_CALLIX_GERAL=
USUARIO_CALLIX_GERAL=
SENHA_CALLIX_GERAL=
TOKEN_CALLIX=

# IPBox
URL_IPBOX=
IPBOX_LOGIN=
IPBOX_PASSWORD=
IPBOX_TOKEN=

# Vonix
URL_BASE_VONIX6=
LOGIN_VONIX=
SENHA_VONIX=
TEMPO_VONIX=35

# Agitel
AGITEL_URL=
AGITEL_USER=
AGITEL_PASSWORD=
```

---

## Execução

### Via linha de comando (`main.py`)

```bash
# Executar apenas um pipeline específico
python main.py --pipeline callix
python main.py --pipeline ipbox
python main.py --pipeline vonix
python main.py --pipeline agitel

# Executar todos os pipelines em sequência
python main.py --pipeline all
```

### Via script agendado no Windows (`run_rivex.bat`)

```bat
run_rivex.bat
```
Executa `.venv\Scripts\python.exe main.py --pipeline all` e redireciona a saída para `logs\rivex_cron.log`.

---

## Testes

Para executar a suíte de testes automatizados com `pytest`:

```bash
.venv\Scripts\python.exe -m pytest -v
```

---

## Tecnologias Utilizadas

- **Python** — linguagem principal e concorrência (`ThreadPoolExecutor`)
- **Requests** — cliente HTTP com sessão, controle de *rate limit* (`429`) e *retries*
- **BeautifulSoup4** — parsing e higienização de relatórios HTML (Vonix, IPBox e Agitel)
- **Pandas / NumPy** — manipulação e apoio analítico de dados
- **Psycopg2** — driver PostgreSQL com operações transacionais e `UPSERT`
- **Pytest** — testes unitários e de integração

---

## Autor

**Victor Amador Viegas**  
Desenvolvedor — Projeto Rivex
