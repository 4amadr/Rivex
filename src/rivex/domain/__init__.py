from src.rivex.domain.exceptions import (
    ErroAutenticacao,
    ErroConfiguracao,
    ErroHttpDiscador,
    RivexError,
)
from src.rivex.domain.registros import (
    ClienteRegistro,
    OperadorRegistro,
    PipelineProtocol,
    ResumoExecucao,
    gerar_id_cliente,
)

__all__ = [
    "ClienteRegistro",
    "ErroAutenticacao",
    "ErroConfiguracao",
    "ErroHttpDiscador",
    "OperadorRegistro",
    "PipelineProtocol",
    "ResumoExecucao",
    "RivexError",
    "gerar_id_cliente",
]
