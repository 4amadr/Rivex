import pandas as pd
from pathlib import Path
from datetime import datetime


class CallixCSVConverter:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def to_dataframe(self, dados: list[dict]) -> pd.DataFrame:
        if not dados:
            raise ValueError("Lista de dados vazia, nada para converter.")
        return pd.DataFrame(dados)

    def save_csv(self, dados: list[dict], filename: str | None = None) -> Path:
        df = self.to_dataframe(dados)

        if not filename:
            hoje = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"callix_{hoje}.csv"

        path = self.output_dir / filename
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path
