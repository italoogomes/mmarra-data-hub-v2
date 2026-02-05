# -*- coding: utf-8 -*-
"""
Inicia o Dashboard Web do MMarra Data Hub.

Uso:
    python scripts/iniciar_dashboard.py
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def main():
    dashboard_path = ROOT_DIR / "dashboard" / "app.py"

    if not dashboard_path.exists():
        print(f"Erro: Dashboard não encontrado em {dashboard_path}")
        return 1

    print("=" * 60)
    print("MMarra Data Hub - Dashboard Web")
    print("=" * 60)
    print(f"Iniciando servidor Streamlit...")
    print(f"Acesse: http://localhost:8501")
    print("=" * 60)
    print("Pressione Ctrl+C para parar o servidor")
    print()

    # Iniciar Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", "8501",
        "--server.headless", "true"
    ])

    return 0


if __name__ == "__main__":
    sys.exit(main())
