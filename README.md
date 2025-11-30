# 📊 Rivex - Automação de Coleta de Dados

> **Propriedade Exclusiva:** Ferramenta de uso interno restrito.
> **Status:** Em Desenvolvimento (Alpha).

## 📝 Sobre o Projeto

O **Rivex** é uma solução de automação desenvolvida para otimizar o fluxo de trabalho do setor de dados da empresa. O foco principal é a extração e consolidação de métricas de operadoras de telefonia e discadores distribuídos aos clientes.

O objetivo central é a eficiência operacional: a implementação destes scripts reduziu o tempo de coleta manual de dados de **3 horas para aproximadamente 40 minutos**.

---

## ⚙️ Funcionalidades Técnicas

A ferramenta atua em duas frentes principais de coleta de dados, gerando saídas em formato `.csv` para análise posterior.

### 1. Operadoras (Web Scraping)
Utilizando **Selenium**, o sistema automatiza a navegação em portais de operadoras que não disponibilizam API pública.
* **Dados Coletados:**
    * Volume de Chamadas.
    * Minutagem Total.
    * Chamadas Saintes (Tarifadas).
    * Identificação do Cliente.

### 2. Discadores
Coleta de métricas de performance dos discadores utilizados pelos clientes.
* **KPIs Coletados:**
    * Chamadas Totais.
    * Chamadas Completas.
    * Chamadas Recusadas.
    * Chamadas Abandonadas.

---

## 🏗️ Status e Ambientes Suportados

Atualmente, o projeto encontra-se em fase de refatoração e expansão.

* **Ambientes Estáveis:**
    * ✅ Callix
    * ✅ Maxima VoIP
* **Execução:**
    * Devido à natureza modular do desenvolvimento atual, a execução deve ser realizada **script por script** (módulos individuais).
    * ⚠️ **Nota:** O orquestrador central (`main.py`) está em desenvolvimento e não deve ser utilizado em produção no momento.

---

## 🚀 Instruções de Uso

1.  Certifique-se de que as dependências do projeto estão instaladas.
2.  Execute o script específico da operadora ou discador desejado (ex: `python operadora_callix.py`).
3.  O arquivo `.csv` será gerado no diretório de saída configurado.

---

**Desenvolvido por:** Equipe de Dados / Victor Amador
