# -*- coding: utf-8 -*-
"""
Detecta anomalias nos dados de vendas usando Isolation Forest.

Uso:
    python scripts/detectar_anomalias.py [--tipo vendas|estoque] [--top N]
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

# Adicionar diretório raiz do projeto ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detectar_anomalias_vendas(top_n: int = 20):
    """
    Detecta anomalias nas vendas.

    Args:
        top_n: Número de anomalias para exibir
    """
    print("=" * 70)
    print("DETECCAO DE ANOMALIAS - VENDAS")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Carregar dados
    vendas_path = ROOT_DIR / "src/data/raw/vendas/vendas.parquet"

    if not vendas_path.exists():
        logger.error(f"Arquivo não encontrado: {vendas_path}")
        logger.error("Execute primeiro: python scripts/extracao/extrair_vendas_completo.py")
        return None

    logger.info(f"Carregando dados de: {vendas_path}")
    df = pd.read_parquet(vendas_path)
    logger.info(f"Registros: {len(df):,}".replace(",", "."))

    # 2. Importar detector
    try:
        from src.agents.scientist.anomaly import AnomalyDetector, AlertGenerator
    except ImportError as e:
        logger.error(f"Erro ao importar: {e}")
        return None

    # 3. Treinar detector
    print("\n--- TREINANDO ISOLATION FOREST ---")

    detector = AnomalyDetector()
    result = detector.fit(df, entity_type="vendas")

    if not result.get("success"):
        logger.error(f"Erro no treinamento: {result.get('error')}")
        return None

    print(f"  Amostras: {result.get('n_samples', 0):,}".replace(",", "."))
    print(f"  Features: {result.get('n_features', 0)}")
    print(f"  Anomalias: {result.get('n_anomalias', 0)} ({result.get('anomaly_rate', 0):.1f}%)")

    # 4. Obter resumo
    print("\n--- RESUMO DAS ANOMALIAS ---")

    resumo = detector.get_anomalies_summary(top_n=top_n)

    if not resumo.get("success"):
        logger.error(f"Erro ao obter resumo: {resumo.get('error')}")
        return None

    # Exibir por severidade
    por_sev = resumo.get("por_severidade", {})
    print(f"\n  Por Severidade:")
    print(f"    Criticas: {por_sev.get('critica', 0)}")
    print(f"    Altas: {por_sev.get('alta', 0)}")
    print(f"    Medias: {por_sev.get('media', 0)}")
    print(f"    Baixas: {por_sev.get('baixa', 0)}")

    # 5. Exibir top anomalias
    top_anomalias = resumo.get("top_anomalias", [])

    if top_anomalias:
        print(f"\n--- TOP {len(top_anomalias)} ANOMALIAS ---")
        print(f"{'#':<3} {'NUNOTA':<12} {'CODPROD':<10} {'VALOR':>12} {'QTD':>8} {'SEVERIDADE':<10} {'SCORE':>8}")
        print("-" * 70)

        for i, anomalia in enumerate(top_anomalias, 1):
            nunota = anomalia.get('NUNOTA', 'N/A')
            codprod = anomalia.get('CODPROD', 'N/A')
            valor = anomalia.get('VLRNOTA', 0) or anomalia.get('VLRTOT', 0)
            qtd = anomalia.get('QTDNEG', 0)
            sev = anomalia.get('severidade', 'N/A')
            score = anomalia.get('score', 0)

            print(f"{i:<3} {str(nunota):<12} {str(codprod):<10} {valor:>12,.2f} {qtd:>8,.0f} {sev:<10} {score:>8.3f}".replace(",", "."))

    # 6. Gerar alertas
    print("\n--- GERANDO ALERTAS ---")

    alert_gen = AlertGenerator()
    alertas = alert_gen.generate_alerts(resumo, min_severity="alta")

    if alertas.get("total_alertas", 0) > 0:
        print(f"\n  Total de alertas (alta + critica): {alertas['total_alertas']}")

        # Formatar e salvar
        mensagem_md = alert_gen.format_for_notification(alertas, format_type="markdown")

        alerta_path = ROOT_DIR / "output" / "divergencias" / f"{datetime.now().strftime('%Y-%m-%d')}_anomalias_vendas.md"
        alerta_path.parent.mkdir(parents=True, exist_ok=True)
        alerta_path.write_text(mensagem_md, encoding='utf-8')
        print(f"  Alertas salvos em: {alerta_path}")
    else:
        print("  Nenhum alerta de alta severidade.")

    # 7. Salvar relatório completo
    relatorio_path = ROOT_DIR / "output" / "reports" / f"anomalias_vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    relatorio_path.parent.mkdir(parents=True, exist_ok=True)

    if top_anomalias:
        df_anomalias = pd.DataFrame(top_anomalias)
        df_anomalias.to_csv(relatorio_path, index=False, encoding='utf-8-sig')
        print(f"\n  Relatório CSV salvo em: {relatorio_path}")

    print("\n" + "=" * 70)
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return resumo


def main():
    parser = argparse.ArgumentParser(
        description="Detecta anomalias nos dados"
    )
    parser.add_argument(
        "--tipo", choices=["vendas", "estoque"], default="vendas",
        help="Tipo de dados para analisar (default: vendas)"
    )
    parser.add_argument(
        "--top", type=int, default=20,
        help="Número de anomalias para exibir (default: 20)"
    )

    args = parser.parse_args()

    if args.tipo == "vendas":
        resultado = detectar_anomalias_vendas(top_n=args.top)
    else:
        print("Tipo não implementado ainda.")
        return 1

    return 0 if resultado else 1


if __name__ == "__main__":
    sys.exit(main())
