from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro, gerar_id_cliente
from src.rivex.utils.logging_config import TransformLogger


class CallixClientData:
    """Empacota métricas tratadas do Callix nos modelos Pydantic canônicos."""

    def __init__(
        self,
        cliente: str,
        chamadas: int,
        aceitas: int,
        recusadas: int,
        abandonadas: int,
        agressividade: float,
        data: date,
        agentes_info: list[dict],
        tech: int | str,
        operadores_contratados: int = 0,
        valor_cliente: Decimal | float = Decimal("0.00"),
        rota_cliente: Optional[str] = None,
        cliente_id: Optional[int] = None,
    ):
        if not cliente:
            raise ValueError(f"Campo cliente vazio para a tech: {tech}.")
        self.id = cliente_id if cliente_id is not None else gerar_id_cliente()
        self.cliente = cliente
        self.tech = int(tech)
        self.chamadas = chamadas
        self.aceitas = aceitas
        self.recusadas = recusadas
        self.abandonadas = abandonadas
        self.agressividade = agressividade
        self.operadores_contratados = operadores_contratados
        self.valor_cliente = valor_cliente
        self.rota_cliente = rota_cliente
        self.log_transform = TransformLogger("callix")
        self.data = data
        self.agentes_info = agentes_info

    def pacote_chamadas(self) -> ClienteRegistro:
        pacote = ClienteRegistro(
            id=self.id,
            discador="Callix",
            tech=self.tech,
            cliente=self.cliente,
            data=self.data,
            chamadas=self.chamadas,
            aceitas=self.aceitas,
            recusadas=self.recusadas,
            abandonadas=self.abandonadas,
            agressividade=self.agressividade,
            operadores_contratados=self.operadores_contratados,
            lucro_empresa=self.valor_cliente,
            rota_cliente=self.rota_cliente,
        )
        self.log_transform.registrar_limpeza_chamadas(pacote)
        return pacote

    def pacote_agentes(self) -> list[OperadorRegistro]:
        if not self.agentes_info:
            lista_vazia = [
                OperadorRegistro(
                    id=self.id,
                    discador="Callix",
                    tech=self.tech,
                    cliente=self.cliente,
                    data=self.data,
                    nome_operador="sem agente",
                    chamada_aceita=0,
                )
            ]
            self.log_transform.registrar_limpeza_agente([a.model_dump() for a in lista_vazia])
            return lista_vazia

        lista_agentes = [
            OperadorRegistro(
                id=self.id,
                discador="Callix",
                tech=self.tech,
                cliente=self.cliente,
                data=self.data,
                nome_operador=dicionario_agente.get("agente") or "Desconhecido",
                chamada_aceita=dicionario_agente.get("Chamadas atendidas", 0),
            )
            for dicionario_agente in self.agentes_info
        ]
        self.log_transform.registrar_limpeza_agente([a.model_dump() for a in lista_agentes])
        return lista_agentes
