# Rivex Vonix Dialer Pipeline: E2E Test Infrastructure

This document outlines the testing philosophy, feature inventory, test architecture, real-world application scenarios, and coverage thresholds for the Rivex Vonix Dialer Pipeline.

---

## 1. Test Philosophy

The Rivex Vonix pipeline is a mission-critical ETL component responsible for processing dialer and call metrics and loading them into a centralized PostgreSQL instance. In production, this pipeline operates against external HTTP APIs that might exhibit high latency, flakiness, or arbitrary changes in output formatting (e.g., raw HTML pages).

To ensure high reliability without depending on live third-party services or databases, our test suite leverages a mock-driven approach using `unittest.mock`. 
Key pillars of our test philosophy include:
- **Hermeticity**: Tests must run completely offline, isolated from database states and web server states.
- **Realism**: Mocks must accurately model HTTP response structures, status codes, HTML tables, authentication states, and PostgreSQL adapter behaviors.
- **Determinism**: The pipeline behavior under tests should be predictable and reproducible.
- **4-Tier Verification**: Testing is structured into layers that range from atomic feature checks to end-to-end integration workflows.

---

## 2. Feature Inventory

The suite verifies the following six core features of the Vonix Dialer Pipeline:

1. **Client List Extraction (`client_list`)**
   - Retrieves the list of active clients from the Vonix environment dashboard.
   - Parses the HTML to extract container element IDs (e.g., `container_CLIENT_NAME`) and formats them.

2. **Context Filtering (`context_filtering`)**
   - Sets the target queue/client context prior to pulling specific call data or agent statistics.
   - Communicates with the `/login/set_show_queue` POST endpoint to store session context.

3. **Call Data Collection (`call_data_collection`)**
   - Fetches historical raw call report HTML and extracts statistics: total calls, completed, abandoned, and refused calls.
   - Cleans raw HTML inputs using BeautifulSoup and handles formatting anomalies.

4. **Agent Table Parser (`agent_table_parser`)**
   - Parses agent tabular data from HTML (usually containing `grid` class tables).
   - Generates structured dictionaries mapping agent names to their specific call counts.

5. **Aggressiveness Configuration (`aggressiveness_configuration`)**
   - Retrieves the dialer aggressiveness configurations (speed metrics and tech prefix parameters) from the queue configuration page.
   - Handles floating-point speed parse logic and extracts associated telecommunications tech prefix identifiers.

6. **Database Loading (`database_loading`)**
   - Configures PostgreSQL connection options and structures SQL batch upserts (`ON CONFLICT DO UPDATE`).
   - Ensures data flows reliably into schema tables for client call summaries and individual agent performance without syntax mismatch or column count mismatches.

---

## 3. Test Architecture (4-Tier Approach)

Our pytest suite enforces a structured 4-tier testing pattern:

- **Tier 1: Feature Coverage (>=5 tests per feature, minimum 30 tests total)**
  - Basic validation of positive/happy path features under standard input and network scenarios.
  - Focuses on correctness of specific utility functions (`gerar_lista_de_clientes`, `limpar_chamadas`, `get_agressividade`, `dict_agentes`, etc.).

- **Tier 2: Boundary & Corner Cases (>=5 tests per feature, minimum 30 tests total)**
  - Stress testing of each feature under extreme or non-standard inputs.
  - Examples: parsing completely empty HTML files, dealing with missing authentication tags, dates in incorrect formats, zero-consumption days, and handling database timeout or connection pool failures gracefully.

- **Tier 3: Cross-Feature Combinations (>=6 tests total)**
  - Validates pairwise relationships between adjacent components in the ETL pipeline.
  - Examples: client list generation feeding into queue context filtering, call data collection feeding into database insertion parameters, configuration extraction combined with agent loop metrics, etc.

- **Tier 4: Real-world Workloads & Scenarios (>=5 tests total)**
  - Complete execution of the pipeline logic mimicking a real-world cron job or pipeline runs.
  - Simulates full ETL cycles starting from login and token retrieval, looping through multiple clients, executing GET/POST requests, parsing tables, and upserting records to PostgreSQL.

---

## 4. Real-world Application Scenarios

The test suite validates specific business scenarios encountered in daily operations:
1. **The Standard Daily Batch Run**: Happy path scenario simulating standard data load under normal conditions.
2. **Holiday/Zero-Volume Day**: Validates pipeline behaviour when dialers run but record zero calls across all queues (handles absence of elements).
3. **Partial Authentication Expiry**: Simulates a scenario where token validation fails mid-run, testing session token renewal and retry behavior.
4. **Mismatched Client Names**: Standardizes and cleans client IDs containing invalid unicode symbols or special ASCII characters.
5. **Database Intermittency**: Simulates brief connection drops or transactional timeouts, ensuring database operations retry or fail gracefully without data corruption.

---

## 5. Coverage Thresholds

The following coverage thresholds are established:
- **Overall Line Coverage**: >= 90% for Rivex Vonix modules.
- **Pass Rate**: 100% of defined tests in the E2E test suite must pass consistently.
- **Mock Enforcement**: 100% of tests must use mocked interfaces for `psycopg2` and `requests`. Any test attempting a live external network request or DB query will be flagged and failed.
