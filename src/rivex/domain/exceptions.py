class RivexError(Exception):
    """Exceção base para falhas de domínio e infraestrutura do Rivex."""


class ErroConfiguracao(RivexError):
    """Variáveis de ambiente obrigatórias ausentes ou inválidas."""


class ErroAutenticacao(RivexError):
    """Falha ao autenticar no discador ou sessão expirada/inválida."""


class ErroTechNaoEncontrada(RivexError):
    """Falha ao resolver uma tech válida e imutável para a equipe."""


class ErroHttpDiscador(RivexError):
    """Erro HTTP retornado pelo discador após esgotar tentativas aplicáveis."""

    def __init__(self, status_code: int, url: str, mensagem: str = ""):
        self.status_code = status_code
        self.url = url
        self.mensagem = mensagem
        detalhe = f"HTTP {status_code} em {url}"
        if mensagem:
            detalhe = f"{detalhe}: {mensagem}"
        super().__init__(detalhe)
