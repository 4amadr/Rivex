# Execution Plan — Vonix Pipeline Refactoring and Optimization

## Objectives
1. Replace all print() statements with logging using `logging.getLogger(__name__)`.
2. Rename `dict_agentes` to `extrair_dados_agentes` to avoid naming collision and update references.
3. Clean up `fluxo_limpeza.py` (remove `LimpezaVonix` or delete if unused).
4. Delete unused utility files `cleaner.py` and `faxina.py`.
5. Remove duplicate import of `load_dotenv` in `main.py`.
6. Evaluate `vonix_queue_discovery.py` and `time.sleep(4)`.
7. Remove wildcard imports in `pipeline_vonix.py` and other Vonix files.
8. Write unit tests for zero-consumption handling.
9. Generate `RELATORIO_MUDANCAS_VONIX.md` at project root.
10. Run pytest and verify imports.

## Decomposed Steps

### Phase 1: Exploration
- **Task**: Inspect all Vonix files, utilities, main, test suite, and queue discovery code.
- **Worker**: `teamwork_preview_explorer`
- **Output**: Detailed analysis report with precise file locations of print statements, imports, duplicate imports, and unused classes/files.

### Phase 2: Implementation
- **Task**: Implement code changes (logging, renaming, file deletions, wildcard cleanups, duplicate import removal, unit tests, and report generation).
- **Worker**: `teamwork_preview_worker`
- **Output**: Hand-off detailing code changes, test results, and file paths.

### Phase 3: Review and Verification
- **Task**: Independently review code changes and run tests.
- **Workers**:
  - `teamwork_preview_reviewer` (correctness, imports, layout)
  - `teamwork_preview_challenger` (verifying test suites, checking rate limit/discovery decisions)
  - `teamwork_preview_auditor` (integrity checks)
- **Output**: Approval verdicts.
