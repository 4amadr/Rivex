# Project Execution Plan - Vonix Pipeline Fixes

This plan outlines the steps, roles, and milestones for fixing, implementing, and optimizing the Vonix dialer pipeline.

## Project Phases

### Phase 1: Planning and Setup (Orchestration Setup)
- [x] Create BRIEFING.md and ORIGINAL_REQUEST.md
- [ ] Initialize global `PROJECT.md` (architecture, interface contracts, milestones table)
- [ ] Initialize `plan.md`

### Phase 2: Parallel Tracks Launch
We will spawn two parallel tracks:
1. **E2E Testing Track**: Delegated to E2E Testing Orchestrator. Goal: Develop, document, and build the E2E test harness and test cases (Tiers 1-4). Output: `TEST_READY.md` and `TEST_INFRA.md`.
2. **Implementation Track**: Delegated to Sub-Orchestrators. Goal: Complete codebase fixes for Milestones 1 to 5.

### Phase 3: Milestones Decomposition (Implementation Track)
- **Milestone 1**: Fix client data retrieval (fluxo_coleta.py, cleaning_vonix.py, pipeline_vonix.py).
- **Milestone 2**: Fix agent loop queue context filtering.
- **Milestone 3**: Gracefully handle zero consumption/empty data days (cleaning_vonix.py, fluxo_limpeza.py).
- **Milestone 4**: Fix PostgreSQL database module (`database.py`) and integrate load step in pipeline.
- **Milestone 5**: Optimize code, resolve naming conflicts (e.g. `dict_agentes`), remove unused files (`cleaner.py`, `faxina.py`), use logging.

### Phase 4: Final Integration and Adversarial Hardening (Milestone 6)
- **Phase 4A**: Once `TEST_READY.md` is available and Milestones 1-5 are done, run the complete E2E test suite and iterate on any bug fixes.
- **Phase 4B (Adversarial Coverage Hardening)**: Generate and run Tier 5 adversarial tests using Challenger. Fix code paths based on findings until Challenger confirms no remaining coverage gaps.

## Verification Procedures
- Run all unit and E2E tests.
- Run forensic integrity auditing on final code to ensure no hardcoding or dummy implementations.
