# Relatório de Mudanças e Refatoração do Pipeline Vonix

Este relatório detalha as melhorias arquiteturais, correções de bugs, refatoração de código e segurança operacional implementadas no pipeline do discador Vonix do Rivex.

---

## 1. Causas Raiz e Resoluções (R1 a R4)

### R1 — Correção na Coleta de Dados de Clientes
* **Causa Raiz:** No arquivo `fluxo_coleta.py`, a propriedade de URL `self.url` era incorretamente referenciada como `self.url_base`, resultando em falhas nas requisições HTTP e erros de atributo. Adicionalmente, a extração de clientes em `cleaning_vonix.py` não identificava corretamente os IDs de fila por causa de falhas no processamento dos prefixos das tags `li`.
* **Solução:** Corrigidas as referências de atributos de URL na classe `ExecucaoVonix`. O parser em `cleaning_vonix.py` foi atualizado com expressões regulares robustas para extrair IDs de clientes removendo com precisão o prefixo `container_` das tags HTML.

### R2 — Correção no Loop de Contexto de Agentes
* **Causa Raiz:** O pipeline não atualizava o contexto do cliente/fila ativo no servidor Vonix durante a iteração. O Vonix exige que uma requisição POST seja enviada para o endpoint `/login/set_show_queue` antes de extrair dados específicos da fila. A ausência desta requisição fazia com que todas as coletas subsequentes no loop retornassem dados do primeiro cliente (ou cliente padrão).
* **Solução:** Integrada a chamada `self.vonix_execucao.get_filtragem(cliente, token)` no início de cada iteração do loop de clientes em `pipeline_vonix.py`, garantindo que o contexto seja atualizado a cada cliente.

### R3 — Tratamento de Consumo Zero (Zero-Consumption)
* **Causa Raiz:** Páginas HTML sem atividade (como filas vazias ou fora de operação) continham tags ausentes ou dados em branco, gerando exceções de tipo (`TypeError`) ou de atributo (`AttributeError`) quando o pipeline tentava realizar parsing.
* **Solução:** Toda a lógica de extração e conversão em `cleaning_vonix.py` foi encapsulada em blocos `try/except` robustos. Adicionou-se validações contra objetos `None` e strings vazias, retornando valores padrão seguros: `"0"` para chamadas totais/completas/abandonadas/recusadas, agressividade e tech, `""` para nome do cliente, e listas vazias `[]` para os dados de agentes.

### R4 — Implementação de Carga no Banco de Dados
* **Causa Raiz:** Erros de sintaxe SQL e divergência de quantidade de colunas inseridas em relação às definidas nas tabelas do PostgreSQL em `database.py`. Também faltava a integração da abertura e fechamento de conexões dentro do orquestrador do pipeline.
* **Solução:** A sintaxe dos comandos `INSERT INTO ... ON CONFLICT DO UPDATE` foi corrigida em `database.py`. As conversões de tipo necessárias (ex: `int` para tech e contadores, `float` para agressividade, e `datetime.date` para datas) foram devidamente aplicadas em `pipeline_vonix.py` antes do envio.

---

## 2. Detalhes das Alterações de Refatoração (R5)

### Substituição de Print Statements por Logging
* **Modificações:** Todos os comandos `print()` foram substituídos por chamadas de log padronizadas (usando `logging.getLogger(__name__)`).
* **Arquivos Modificados:**
  - `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py` (`logger.info` para nome do cliente e tabela de agentes).
  - `src/rivex/database/database.py` (usando o logger `log` já existente no arquivo para emitir `log.info` em sucessos e `log.error` em erros).
  - `src/rivex/enviroments/discadores/vonix/vonix_queue_discovery.py` (`logger.info` para apresentação do resumo de filas descobertas).

### Resolução de Colisão de Nomes (`dict_agentes`)
* **Modificações:** A função utilitária de extração de dados de agentes `dict_agentes` causava uma colisão de escopo com o dicionário de configurações hardcoded `dict_agentes` definido em `equipes_vonix.py`.
* **Ações:** 
  1. A função em `cleaning_vonix.py` foi renomeada para `extrair_dados_agentes()`.
  2. As chamadas a essa função foram atualizadas em `pipeline_vonix.py` e em `tests/e2e/test_e2e_suite.py`.
  3. O dicionário de configuração `dict_agentes` em `equipes_vonix.py` permaneceu inalterado.

### Limpeza e Depreciação de Arquivos Não Utilizados
* **Modificações:**
  - O arquivo `fluxo_limpeza.py` contendo a classe não utilizada `LimpezaVonix` foi esvaziado e marcado com um comentário de depreciação. Seus imports foram removidos de `main.py` e `pipeline_vonix.py`.
  - Os utilitários mortos `cleaner.py` e `faxina.py` sob `src/rivex/utils/infra_utils/` também foram esvaziados e marcados para futura deleção física pela equipe de infraestrutura.
  - O import duplicado `from dotenv import load_dotenv` no arquivo `main.py` (antiga linha 19) foi devidamente removido.

### Limpeza de Wildcard Imports (`*`)
* **Modificações:** Os imports genéricos foram substituídos por referências explícitas:
  - Em `pipeline_vonix.py`, as dependências foram especificadas diretamente:
    ```python
    from src.rivex.enviroments.discadores.vonix.fluxo_coleta import ExecucaoVonix
    from src.rivex.data_processing.Vonix.cleaning_vonix import (
        extrair_dados_agentes,
        limpar_chamadas,
        get_agressividade,
        get_cliente_nome,
        get_tech,
        gerar_lista_de_clientes
    )
    from src.rivex.utils.infra_utils.date_config import DateConfig
    ```
  - Em `fluxo_coleta.py`, os wildcards de payloads e cleaning foram limpos:
    ```python
    from src.rivex.enviroments.discadores.vonix.payloads_vonix import (
        payload_de_login,
        payload_de_filtragem,
        payload_de_chamadas,
        payload_de_agentes,
        payload_de_agressividade,
        headers
    )
    from src.rivex.data_processing.Vonix.cleaning_vonix import get_html, get_token
    ```

---

## 3. Avaliações Técnicas e Decisões de Projeto

### Integração do `vonix_queue_discovery.py`
* **Avaliação:** O módulo `vonix_queue_discovery.py` faz scraping de checkboxes dinâmicos para mapear as filas ativas direto da página do Vonix. 
* **Decisão:** Optou-se por mantê-lo como uma classe utilitária separada e opcional ao invés de acoplá-lo diretamente no loop de orquestração do pipeline nesta etapa. Isso evita riscos de perda de controle ou instabilidade em produção caso a estrutura de nomes de filas sofra mudanças no servidor da Vonix, mantendo o controle explícito por meio do mapeamento do banco de dados/equipes. É uma excelente ferramenta recomendada para auditorias e sincronizações secundárias.

### Uso do `time.sleep(4)`
* **Avaliação:** Durante a execução do pipeline por cliente, ocorrem até 7 requisições HTTP seguidas ao servidor Vonix.
* **Decisão:** A manutenção do atraso de 4 segundos é estritamente necessária. A VonixCC possui mecanismos de rate limit e proteção contra abusos que bloqueiam temporariamente o IP de origem caso muitas conexões simultâneas ou consecutivas ocorram em menos de um segundo. O intervalo garante a longevidade operacional do script sem interrupções por WAF ou bloqueios.

---

## 4. Diagrama de Fluxo de Dados (Data Flow)

O pipeline segue o fluxo linear abaixo para cada cliente:

```
[1. Login & Token] 
       | (Obtém authenticator token de login.signin)
       v
[2. Filtragem de Fila] 
       | (Envia POST /login/set_show_queue para definir o cliente/contexto ativo)
       v
[3. Coleta HTML] 
       | (Coleta chamadas, agentes ativos e configurações de agressividade)
       v
[4. Limpeza de Dados] 
       | (beautifulsoup4 processa os dados brutos e gera dicionários normalizados)
       v
[5. Inserção DB (Upsert)]
       | (DatabaseRivex realiza insert ON CONFLICT DO UPDATE no PostgreSQL)
       v
[FIM (Fechar Conexão)]
```

---

## 5. Recomendações de Engenharia

1. **Testes Contínuos:** Manter a execução de testes automatizados (`pytest`) integrada em esteiras de CI/CD para detectar quebras nos parsers de BeautifulSoup sempre que o layout do painel Vonix for atualizado.
2. **Utilização de Session Mocks:** Nos testes de coleta, garantir que todas as requisições HTTP utilizem mock (como feito com `requests-mock`), mantendo os testes unitários rápidos e desacoplados de conexões externas.
3. **Mapeamento Dinâmico de Filas:** Programar uma fase futura para migrar o pipeline de listas de clientes estáticas para o uso híbrido de `VonixQueueDiscovery` cruzando dados com tabelas dinâmicas de configuração de banco de dados.
