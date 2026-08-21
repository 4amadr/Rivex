# src/rivex/settings.py
from pathlib import Path

# Este arquivo fica em src/rivex/, então a raiz do projeto é 2 níveis acima
PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_DIR = PROJECT_ROOT / "Log"