# Rivex

> Automação de coleta de dados de discadores telefônicos com envio direto para banco de dados relacional.

---

## O que é o Rivex?

O **Rivex** é uma automação desenvolvida para substituir o processo manual de coleta de dados operacionais de discadores telefônicos. Antes do Rivex, esse processo exigia que um operador acessasse manualmente cada sistema, copiasse os dados e os organizasse em planilhas Excel — uma tarefa que consumia cerca de **4 horas por ciclo** e estava sujeita a erros humanos.

Com o Rivex, esse mesmo processo passa a durar aproximadamente **25 minutos**, com dados estruturados, padronizados e armazenados diretamente em banco de dados, sem intervenção manual.

---

## Discadores suportados

| Discador | Método de coleta |
|----------|-----------------|
| **Vonix** | Requisições HTTP + HTML parsing |
| **Callix** | API REST + Selenium |

---

## Como funciona

### Vonix

1. A automação realiza login no ambiente do discador via requisições HTTP.
2. Coleta dados de **chamadas**, **agentes ativos** e **agressividade por fila**.
3. Os dados retornam em formato HTML e são limpos com a biblioteca **BeautifulSoup**.
4. Os dados tratados são enviados para o banco de dados **PostgreSQL**.

### Callix

O fluxo do Callix é dividido em duas etapas:

**Etapa 1 — Coleta de tokens e endereços dos clientes**
1. O **Selenium** acessa a página do discador automaticamente.
2. Navega cliente a cliente para extrair os tokens de autenticação e os endereços de ambiente.
3. Essas informações são armazenadas no **PostgreSQL** para uso nas etapas seguintes.

**Etapa 2 — Coleta de dados operacionais**
1. Com os tokens e endereços coletados, a automação acessa a **API** de cada cliente individualmente.
2. Coleta dados de **chamadas** e **campanhas** (incluindo IDs de campanha).
3. Utiliza as ferramentas de **DevTools do navegador** para capturar dados de **agentes logados** e **agressividades** — informações que dependem do ID de campanha para serem acessadas.
4. Todos os dados são tratados com **Pandas** e enviados para o **PostgreSQL**.

---

## Resultado

| | Processo manual | Com o Rivex |
|---|---|---|
| **Tempo de coleta** | ~4 horas | ~25 minutos |
| **Erros humanos** | Possíveis | Eliminados |
| **Armazenamento** | Planilhas Excel | Banco de dados PostgreSQL |
| **Escalabilidade** | Limitada | Automatizável por demanda |

---

## Tecnologias utilizadas

- **Python** — linguagem principal da automação
- **Requests** — requisições HTTP para coleta de dados via API e login
- **BeautifulSoup** — limpeza e extração de dados em formato HTML
- **Selenium** — navegação automatizada em ambientes web
- **Pandas** — tratamento e padronização dos dados coletados
- **PostgreSQL** — armazenamento estruturado dos dados

---

## Status do projeto

🚧 **Em desenvolvimento ativo.**

O projeto está sendo desenvolvido individualmente. A estrutura atual cobre a coleta dos discadores **Vonix** e **Callix**. As próximas etapas incluem a integração com as operadoras de telefonia associadas a esses discadores.

---

## Autor

**Victor Amador Viegas**  
Desenvolvedor — Projeto Rivex
