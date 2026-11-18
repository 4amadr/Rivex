# Callix v1 - Código Desativado (Bloqueio reCAPTCHA)

Este diretório armazena os módulos e funções da integração Callix que deixaram de funcionar devido ao bloqueio implementado pela Callix (exigência de `Recaptcha` no endpoint `/api/v4/auth/session` - HTTP 401 `Recaptcha is needed`) e à ausência de resposta da equipe de suporte/desenvolvimento da Callix.

**Status:** Desativado temporariamente. Não importar em produção.

## Arquivos guardados aqui
- `callix_get_clients.py`: `CallixGetClients` (consulta `sub_accounts` via `TOKEN_CALLIX`) e `GetTokenCallix` (login v4 com `captchaToken` + criação/listagem de `api-tokens`).
- `sincronizar_clientes.py`: `SincroniaCallix` (sincronização remota de clientes + coleta automática de tokens via `GetTokenCallix`).
- `callix_clients.py`: `limpar_cliente`, `get_clientes_servidor_callix`, `separar_clientes` (parser da resposta de `sub_accounts`).
- `callix_v1_auth_legacy.py`: métodos legados de login v4 (`login_callix`), agressividade v4 antiga, rota tech antiga, URLs e payloads de login/token.
