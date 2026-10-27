# Auditoria rápida da coleta VonixCC

Data da auditoria: 23/10/2026  
Escopo: análise estática dos componentes Vonix do Rivex e tentativa de observação no ambiente. Não houve alteração no pipeline, nos dados do Vonix nem criação de commit.

## Resultado executivo

O intervalo de **35 segundos** está aplicado uma vez **depois de toda a coleta, processamento e gravação de cada cliente**, e não entre as requisições desse cliente. O valor vem de `TEMPO_VONIX`, com padrão `35`, em `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py:32`, e é efetivado por `time.sleep(...)` na linha 120.

A sessão HTTP já é reutilizada pelo código via uma única instância de `requests.Session()` por `ExecucaoVonix`; não há evidência de paginação, lote, coleta incremental nem uso de exportação no fluxo atual. A redução para 30 s e 25 s **não foi executada**, pois o navegador recusou a autorização de rede para o domínio antes de carregar o ambiente. Logo, não seria uma auditoria; seria ficção com `time.sleep`.

## Evidências e classificação

- **Confirmado no código**: evidência direta em arquivos do Rivex revisados.
- **Não confirmado ao vivo**: dependeria de resposta do ambiente Vonix, que não foi acessada nesta execução.
- **Hipótese/recomendação**: proposta que precisa de medição controlada antes de virar alteração.

## Como a coleta funciona

### Fluxo confirmado no código

1. `PipelineVonix` carrega `LOGIN_VONIX`, `SENHA_VONIX`, `URL_BASE_VONIX6` e `TEMPO_VONIX`.
2. `ExecucaoVonix` cria uma `requests.Session()` única, que carrega cookies entre requisições.
3. A inicialização faz `GET /login/signin`, extrai `authenticity_token`, envia o login e lê a página principal para obter clientes.
4. Para cada cliente válido, a rotina seleciona a fila e coleta quatro visões de chamadas, agentes, configuração de agressividade e rotas técnicas.
5. O Rivex interpreta o corpo das respostas como HTML com BeautifulSoup, processa os dados e persiste no banco.
6. Somente então chama `time.sleep(TEMPO_VONIX)` antes do próximo cliente.

O valor padrão de 35 s pode ser sobrescrito sem mudança de código com `TEMPO_VONIX`; a redução não é aplicada automaticamente. A documentação do Python confirma que `time.sleep` suspende a thread chamadora pelo período solicitado, que pode ser maior conforme o agendamento do sistema: [time.sleep](https://docs.python.org/3/library/time.html#time.sleep).

### Local exato do timer

| Arquivo | Linhas | Comportamento confirmado |
| --- | ---: | --- |
| `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py` | 32–33 | Lê `TEMPO_VONIX`, padrão `35`, e converte para inteiro. |
| `src/rivex/pipeline/pipeline_discador/pipeline_vonix.py` | 98–120 | Loop sequencial por cliente; pausa ocorre depois de `db_vonix(...)`. |

Não foi localizado outro timer de 35 s nos módulos de coleta Vonix. Portanto, reduzir esse valor reduz apenas o tempo ocioso entre clientes, não a duração das oito requisições da própria coleta.

## Requisições previstas pelo código

Os itens abaixo são **confirmados no código, mas não observados no ambiente ao vivo**. Métodos e parâmetros foram extraídos de `fluxo_coleta.py` e `payloads_vonix.py`.

| Etapa | Método | Endpoint relativo | Parâmetros/corpo relevante | Formato tratado pelo Rivex |
| --- | --- | --- | --- | --- |
| Preparação | GET | `/login/signin` | nenhum | HTML; campo `authenticity_token` |
| Autenticação | POST | `/login/signin` | token, `username`, `password`, `commit=Entrar` | resposta HTTP; sessão preservada |
| Clientes | GET | `/` | nenhum | HTML; lista/filtros de filas |
| Seleção de fila | POST | `/login/set_show_queue` | token, `return_to=/overview`, `queue_id[]` | resposta HTTP; muda o escopo da fila da sessão |
| Chamadas totais | GET | `/calls` | filtros de data do dia, `directions[]=AUTO`, status vazio | HTML |
| Chamadas aceitas | GET | `/calls` | mesmos filtros, `status[select]=completed` | HTML |
| Chamadas abandonadas | GET | `/calls` | mesmos filtros, `status[select]=abandon` | HTML |
| Chamadas recusadas | GET | `/calls` | mesmos filtros, `status[select]=discard` | HTML |
| Agentes | GET | `/agents/calls_overview` | intervalo customizado com data inicial/final | HTML |
| Agressividade | GET | `/admin/queue_edit/{cliente}` | `authenticity_token` como query parameter no código | HTML; input `dialer_dial_speed` |
| Rotas técnicas | GET | `/admin/routes` | nenhum | HTML |

Após a inicialização, a coleta de cada cliente prevê **8 requisições sequenciais**: 1 seleção de fila, 4 consultas de chamadas, 1 de agentes, 1 de agressividade e 1 de rotas. A estimativa é estrutural; contagem, URLs finais, redirects, códigos HTTP, latências e tamanhos de resposta continuam **não confirmados ao vivo**.

### Paginação, lote e exportação

- **Paginação:** não há parâmetros como `page`, `offset`, `limit` ou `per_page` nos payloads inspecionados. Não se pode concluir que o Vonix não pagina; apenas que o Rivex não solicita paginação explicitamente.
- **Lote:** não há endpoint ou payload de múltiplas filas. A fila é alterada a cada cliente por `queue_id[]`, e as consultas posteriores dependem desse estado de sessão.
- **Exportação:** o payload de `/calls` inclui `to_excel=0` e `to_csv=0`. Isso é apenas um indício de recurso potencial; não confirma que `1` produza uma exportação válida, nem que seja eficiente ou permitido.
- **API estruturada:** o pipeline trata as respostas como HTML (`response.text` e BeautifulSoup), sem uso de JSON. Nenhuma API formal foi confirmada.

## Coleta de leitura e medições solicitadas

**Resultado: não executada.** A abertura de `http://contech6.vonixcc.com.br` no navegador foi recusada pela política de autorização de rede. Não houve login, consulta, criação de sessão, seleção de cliente ou requisição ao Vonix.

Como consequência, não há dados reais para preencher, e este relatório deliberadamente não inventa números:

| Métrica | Resultado |
| --- | --- |
| Cliente autorizado consultado | Não acessado |
| Duração da coleta | Não medida |
| Número de requisições observadas | Não medido |
| Latência por endpoint | Não medida |
| Códigos HTTP / redirects | Não observados |
| Integridade dos dados | Não verificável |
| HTTP 429, timeout ou erro de autenticação | Não observados; nenhum teste chegou ao servidor |

Por segurança, não houve tentativa alternativa de contornar a recusa do navegador. As credenciais foram apenas verificadas quanto à presença no `.env`; não foram exibidas, gravadas ou usadas em outro canal.

## Avaliação do timer: 35 s, 30 s e 25 s

| Configuração | Status nesta auditoria | Estabilidade / integridade |
| --- | --- | --- |
| 35 s | Configuração padrão identificada no código; não medida ao vivo | Não confirmada nesta execução |
| 30 s | Não testada | Não confirmada |
| 25 s | Não testada | Não confirmada |

Não é possível aprovar a redução com base só no código. O tratamento atual tampouco interrompe explicitamente em 429: `analista_de_erros` só lança para 404 e 5xx; outros códigos não-200 são registrados, mas podem seguir até a etapa de parsing. Isso torna ainda mais importante observar status e integridade antes de reduzir o intervalo.

## Estratégia recomendada

### Agora

1. **Manter 35 s em produção** até haver medição autorizada no ambiente.
2. Quando o acesso for liberado, medir **um único cliente autorizado por vez**, sem concorrência: baseline em 35 s, depois 30 s e apenas então 25 s.
3. Em cada rodada, registrar duração ponta a ponta, oito status HTTP, latência por endpoint, quantidade de registros extraídos e comparação dos campos persistidos. Interromper imediatamente com falha de login, 429, timeout, crescimento relevante de erros ou divergência nos dados.

### Melhor alternativa provável (hipótese a validar)

A alternativa mais segura e de menor risco é **preservar a mesma `requests.Session` durante a execução** — algo que o código já faz — e introduzir uma medição/validação explícita antes de mexer no intervalo. Sessões do Requests preservam cookies e usam pool de conexões, portanto evitam novo handshake/conexão desnecessária entre requisições ao mesmo host: [Requests — Session Objects](https://requests.readthedocs.io/en/stable/user/advanced/#session-objects).

O segundo maior candidato a ganho é investigar uma exportação única por fila ou uma API oficial, se o ambiente confirmar um formato completo e estável. Esse caminho pode reduzir as quatro chamadas repetidas a `/calls`, mas hoje é só hipótese; o código envia `to_excel=0` e `to_csv=0`, sem implementar exportação. Não recomendo ativá-lo sem confirmação ao vivo de escopo, volume, consistência e impacto no servidor.

### Recomendação final

**Não reduzir nem eliminar permanentemente o timer nesta auditoria.** O único ganho comprovável no código ao reduzir 35 → 30 → 25 é diminuir o tempo ocioso pós-cliente em 5 s e depois 10 s, respectivamente; não há evidência operacional de que o Vonix aceite essa cadência sem efeito colateral. Autorize novamente o acesso de rede ao ambiente e execute o protocolo sequencial acima. Se as três rodadas forem íntegras e sem 429, timeout ou regressão de latência, 25 s passa a ser um candidato razoável; eliminar a pausa permanece sem evidência e não foi testado.

## Limitações

- A autorização do navegador para o domínio foi recusada, portanto a inspeção HTTP ao vivo e os testes solicitados não ocorreram.
- Não foram acessados cookies, tokens ou senhas em relatórios/logs.
- Os endpoints, métodos e payloads listados refletem o código atual, não uma confirmação do contrato remoto.
- Arquivos não relacionados à coleta Vonix não foram inspecionados para esta auditoria.
