from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import date
from typing import Any, Callable, Iterator, TypeVar

T = TypeVar("T")


class CronometroPipelines:
    """Centraliza a contagem de tempo de execução por pipeline e do total consolidado.

    Projetado para escalonar automaticamente conforme novas pipelines forem adicionadas:
    qualquer nome de pipeline registrado via ``medir_pipeline`` ou ``registrar`` passa a
    compor o dicionário de tempos individuais e a soma total.
    """

    def __init__(self, relogio: Callable[[], float] = time.perf_counter):
        self._relogio = relogio
        self._tempos: dict[str, float] = {}

    @contextmanager
    def medir_pipeline(self, nome: str) -> Iterator[None]:
        """Mede o tempo de execução (em segundos) de uma pipeline dentro de um bloco ``with``."""
        inicio = self._relogio()
        try:
            yield
        finally:
            duracao = max(0.0, self._relogio() - inicio)
            self.registrar(nome, duracao)

    def registrar(self, nome: str, duracao_segundos: float) -> float:
        """Registra (ou acumula, se chamada novamente) a duração em segundos de uma pipeline."""
        chave = nome.strip().lower()
        if not chave:
            raise ValueError("O nome da pipeline não pode ser vazio.")
        if duracao_segundos < 0:
            raise ValueError("A duração da execução não pode ser negativa.")
        valor = round(float(duracao_segundos), 2)
        self._tempos[chave] = valor
        return valor

    def obter_tempo(self, nome: str) -> float | None:
        """Retorna o tempo registrado (em segundos) de uma pipeline específica."""
        return self._tempos.get(nome.strip().lower())

    def obter_tempos(self) -> dict[str, float]:
        """Retorna um dicionário {pipeline: duracao_segundos} com todas as pipelines medidas."""
        return dict(self._tempos)

    @property
    def tempo_total(self) -> float:
        """Soma dos tempos de execução de todas as pipelines medidas (em segundos)."""
        return round(sum(self._tempos.values()), 2)

    def gerar_resumo(self, data_ref: date) -> dict[str, Any]:
        """Retorna o payload consolidado pronto para log ou persistência no banco."""
        return {
            "data": data_ref,
            "tempos": self.obter_tempos(),
            "total": self.tempo_total,
        }


def medir_tempo_execucao(
    func: Callable[..., T],
    *args: Any,
    relogio: Callable[[], float] = time.perf_counter,
    **kwargs: Any,
) -> tuple[T, float]:
    """Executa uma função qualquer e retorna ``(resultado, duracao_segundos)``."""
    inicio = relogio()
    resultado = func(*args, **kwargs)
    duracao = round(max(0.0, relogio() - inicio), 2)
    return resultado, duracao
