from __future__ import annotations

from datetime import date, timedelta


class DateConfig:
    @staticmethod
    def ontem() -> date:
        return date.today() - timedelta(days=1)

    @staticmethod
    def data_selecionadas(data_ref: date | None = None) -> str:
        ref = data_ref or DateConfig.ontem()
        return ref.strftime("%d/%m/%Y")

    @staticmethod
    def data_callix(data_ref: date | None = None) -> str:
        ref = data_ref or DateConfig.ontem()
        return ref.strftime("%Y-%m-%d")

    @staticmethod
    def data_ipbox(dias_atras: int = 1, data_ref: date | None = None) -> str:
        ref = data_ref or (date.today() - timedelta(days=dias_atras))
        return ref.strftime("%Y%m%d")

    @staticmethod
    def data_ipbox_payload(dias_atras: int = 1, data_ref: date | None = None) -> dict[str, str]:
        ref = data_ref or (date.today() - timedelta(days=dias_atras))
        data_formatada = ref.strftime("%Y%m%d")
        return {
            "de": f"{data_formatada}000000",
            "ate": f"{data_formatada}235959",
        }
