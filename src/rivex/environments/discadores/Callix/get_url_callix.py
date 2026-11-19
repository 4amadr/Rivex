class UrlGetData:
    """URLs dos endpoints ativos da API v1, v4 e Server SDK do Callix."""

    def url_users_v1(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v1/users"

    def url_sdk_user_session(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/sdk/v1/server/user-session"

    def url_logout_v4(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v4/auth/session"

    def url_accounts(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v4/entities/accounts"

    def url_campanhas_v4(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v4/entities/campaigns"

    def url_chamadas_completas_v4(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v4/entities/campaign-completed-calls"

    def url_outbound_routes(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v4/entities/outbound-routes"

    def url_user_performance_histories(self, cliente: str) -> str:
        return f"https://{cliente}.callix.com.br/api/v4/entities/user-performance-histories"
