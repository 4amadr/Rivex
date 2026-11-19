from __future__ import annotations

import random
from datetime import date
from decimal import Decimal
from typing import Any, Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def gerar_id_cliente() -> int:
    """Gera um ID numérico randômico de até 5 dígitos (10000 a 99999)."""
    return random.randint(10000, 99999)


class ClienteRegistro(BaseModel):
    """Contrato canônico de métricas consolidadas de um cliente/fila no discador."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(default_factory=gerar_id_cliente, ge=1, le=99999)
    discador: Literal["Callix", "IPBox", "Vonix"]
    tech: int = Field(..., ge=0)
    cliente: str = Field(..., min_length=1)
    data: date
    chamadas: int = Field(..., ge=0)
    aceitas: int = Field(..., ge=0)
    recusadas: int = Field(..., ge=0)
    abandonadas: int = Field(..., ge=0)
    agressividade: float = Field(..., ge=0.0)
    operadores_contratados: int = Field(default=0, ge=0)
    lucro_empresa: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    rota_cliente: Optional[str] = None

    @field_validator("cliente", mode="before")
    @classmethod
    def _normalizar_cliente(cls, valor: Any) -> str:
        if valor is None:
            raise ValueError("Campo 'cliente' não pode ser nulo.")
        texto = str(valor).strip()
        if not texto:
            raise ValueError("Campo 'cliente' não pode ser vazio.")
        return texto

    @field_validator("tech", mode="before")
    @classmethod
    def _normalizar_tech(cls, valor: Any) -> int:
        if valor is None or valor == "":
            return 0
        return int(valor)

    @field_validator("lucro_empresa", mode="before")
    @classmethod
    def _normalizar_lucro(cls, valor: Any) -> Decimal:
        if valor is None or valor == "":
            return Decimal("0.00")
        return Decimal(str(valor)).quantize(Decimal("0.01"))

    @model_validator(mode="after")
    def _garantir_tech_ou_id(self) -> "ClienteRegistro":
        if self.tech == 0:
            object.__setattr__(self, "tech", self.id)
        return self


class OperadorRegistro(BaseModel):
    """Contrato canônico de produtividade de um operador vinculado a um cliente."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(..., ge=1, le=99999)
    discador: Literal["Callix", "IPBox", "Vonix"]
    tech: int = Field(..., ge=0)
    cliente: str = Field(..., min_length=1)
    data: date
    nome_operador: str = Field(..., min_length=1)
    chamada_aceita: int = Field(..., ge=0)

    @field_validator("cliente", "nome_operador", mode="before")
    @classmethod
    def _normalizar_texto(cls, valor: Any) -> str:
        if valor is None:
            raise ValueError("Campo textual obrigatório não pode ser nulo.")
        texto = str(valor).strip()
        if not texto:
            raise ValueError("Campo textual obrigatório não pode ser vazio.")
        return texto

    @field_validator("tech", mode="before")
    @classmethod
    def _normalizar_tech(cls, valor: Any) -> int:
        if valor is None or valor == "":
            return 0
        return int(valor)

    @model_validator(mode="after")
    def _garantir_tech_ou_id(self) -> "OperadorRegistro":
        if self.tech == 0:
            object.__setattr__(self, "tech", self.id)
        return self


class ResumoExecucao(BaseModel):
    """Resumo estruturado da execução de uma pipeline."""

    pipeline: str
    total: int = 0
    persistidos: int = 0
    falhas: list[str] = Field(default_factory=list)
    erro_fatal: Optional[str] = None

    @property
    def teve_falha(self) -> bool:
        return self.erro_fatal is not None or len(self.falhas) > 0


@runtime_checkable
class PipelineProtocol(Protocol):
    """Contrato mínimo que toda pipeline de discador deve implementar."""

    nome: str

    def executar(self, data: date) -> ResumoExecucao:
        ...
