# -*- coding: utf-8 -*-
"""
Script de Teste - Agente Cientista

Testa os modelos de ML com dados reais do Data Lake.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 60)
print("TESTE DO AGENTE CIENTISTA - MMarra Data Hub")
print("=" * 60)
print()

# =============================================================================
# 1. Verificar dependencias
# =============================================================================
print("[1] VERIFICANDO DEPENDENCIAS")
print("-" * 40)

try:
    import sklearn
    print(f"  scikit-learn: {sklearn.__version__} - OK")
except ImportError:
    print("  scikit-learn: NAO INSTALADO")
    print("  Instale com: pip install scikit-learn")

try:
    from prophet import Prophet
    print(f"  prophet: OK")
    PROPHET_OK = True
except ImportError:
    print("  prophet: NAO INSTALADO")
    print("  Instale com: pip install prophet")
    PROPHET_OK = False

print()

# =============================================================================
# 2. Carregar dados
# =============================================================================
print("[2] CARREGANDO DADOS")
print("-" * 40)

data_dir = Path(__file__).parent.parent.parent / "src" / "data" / "raw"

# Carregar vendas
vendas_dir = data_dir / "vendas"
vendas_files = list(vendas_dir.glob("*.parquet")) if vendas_dir.exists() else []

if vendas_files:
    arquivo = max(vendas_files, key=lambda x: x.stat().st_mtime)
    df_vendas = pd.read_parquet(arquivo)
    print(f"  Vendas: {len(df_vendas)} registros de {arquivo.name}")
else:
    df_vendas = pd.DataFrame()
    print("  Vendas: SEM DADOS")

print()

# =============================================================================
# 3. Testar Deteccao de Anomalias (Isolation Forest)
# =============================================================================
print("[3] TESTANDO DETECCAO DE ANOMALIAS")
print("-" * 40)

try:
    from src.agents.scientist.anomaly import AnomalyDetector, AlertGenerator

    if not df_vendas.empty:
        detector = AnomalyDetector()

        # Treinar
        print("  Treinando detector...")
        result = detector.fit(df_vendas, entity_type="vendas")

        if result.get("success"):
            print(f"  Treinamento OK:")
            print(f"    - Amostras: {result.get('n_samples')}")
            print(f"    - Features: {result.get('features')}")
            print(f"    - Anomalias: {result.get('n_anomalias')} ({result.get('anomaly_rate', 0):.1f}%)")

            # Obter resumo
            summary = detector.get_anomalies_summary()

            if summary.get("success"):
                print(f"\n  Resumo das anomalias:")
                print(f"    - Total: {summary.get('total_anomalias')}")
                por_sev = summary.get('por_severidade', {})
                print(f"    - Criticas: {por_sev.get('critica', 0)}")
                print(f"    - Altas: {por_sev.get('alta', 0)}")
                print(f"    - Medias: {por_sev.get('media', 0)}")

                # Gerar alertas
                alert_gen = AlertGenerator()
                alertas = alert_gen.generate_alerts(summary, min_severity="alta")
                print(f"\n  Alertas gerados: {alertas.get('total_alertas', 0)}")
        else:
            print(f"  ERRO: {result.get('error')}")
    else:
        print("  Sem dados para testar")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 4. Testar Segmentacao de Clientes (K-Means RFM)
# =============================================================================
print("[4] TESTANDO SEGMENTACAO DE CLIENTES")
print("-" * 40)

try:
    from src.agents.scientist.clustering import CustomerSegmentation

    if not df_vendas.empty:
        segmenter = CustomerSegmentation()

        # Treinar
        print("  Segmentando clientes...")
        result = segmenter.fit(df_vendas)

        if result.get("success"):
            print(f"  Segmentacao OK:")
            print(f"    - Clientes: {result.get('n_customers')}")
            print(f"    - Segmentos: {result.get('n_clusters')}")

            # Obter resumo
            summary = segmenter.get_segmentation_summary()

            if summary.get("success"):
                print(f"\n  Segmentos identificados:")
                for seg in summary.get("segmentos", []):
                    print(f"    - {seg['nome']}: {seg['quantidade_clientes']} clientes ({seg['percentual_receita']:.1f}% receita)")

                # Insights
                insights = summary.get("insights", [])
                if insights:
                    print(f"\n  Insights:")
                    for insight in insights[:2]:
                        print(f"    - {insight}")
        else:
            print(f"  ERRO: {result.get('error')}")
    else:
        print("  Sem dados para testar")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 5. Testar Segmentacao de Produtos
# =============================================================================
print("[5] TESTANDO SEGMENTACAO DE PRODUTOS")
print("-" * 40)

try:
    from src.agents.scientist.clustering import ProductSegmentation

    if not df_vendas.empty:
        segmenter = ProductSegmentation()

        # Treinar
        print("  Segmentando produtos...")
        result = segmenter.fit(df_vendas)

        if result.get("success"):
            print(f"  Segmentacao OK:")
            print(f"    - Produtos: {result.get('n_products')}")
            print(f"    - Segmentos: {result.get('n_clusters')}")

            # Obter resumo
            summary = segmenter.get_segmentation_summary()

            if summary.get("success"):
                print(f"\n  Segmentos identificados:")
                for seg in summary.get("segmentos", []):
                    print(f"    - {seg['nome']}: {seg['quantidade_produtos']} produtos ({seg['percentual_receita']:.1f}% receita)")

                # Curva ABC
                abc = summary.get("curva_abc", {})
                if abc:
                    print(f"\n  Curva ABC:")
                    for classe in ["classe_A", "classe_B", "classe_C"]:
                        if classe in abc:
                            print(f"    - {classe}: {abc[classe]['quantidade']} produtos ({abc[classe]['percentual_produtos']:.1f}%)")
        else:
            print(f"  ERRO: {result.get('error')}")
    else:
        print("  Sem dados para testar")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 6. Testar Previsao de Demanda (Prophet)
# =============================================================================
print("[6] TESTANDO PREVISAO DE DEMANDA")
print("-" * 40)

if not PROPHET_OK:
    print("  Prophet nao instalado - pulando teste")
else:
    try:
        from src.agents.scientist.forecasting import DemandForecastModel

        if not df_vendas.empty:
            # Pegar um produto com historico
            top_produtos = df_vendas.groupby("CODPROD")["QTDNEG"].sum().nlargest(5)
            codprod = top_produtos.index[0]

            print(f"  Produto selecionado: {codprod}")
            print(f"  Historico: {len(df_vendas[df_vendas['CODPROD'] == codprod])} registros")

            model = DemandForecastModel()

            # Treinar
            print("  Treinando modelo Prophet...")
            result = model.fit(df_vendas, codprod=codprod)

            if result.get("success"):
                print(f"  Treinamento OK: {result.get('training_rows')} registros")

                # Obter previsao
                summary = model.get_forecast_summary(periods=30)

                if summary.get("success"):
                    previsao = summary.get("previsao", {})
                    tendencia = summary.get("tendencia", {})

                    print(f"\n  Previsao para 30 dias:")
                    print(f"    - Total previsto: {previsao.get('total', 0):.0f} unidades")
                    print(f"    - Media diaria: {previsao.get('media_diaria', 0):.1f} unidades")
                    print(f"    - Tendencia: {tendencia.get('direcao', 'N/A')} ({tendencia.get('variacao_pct', 0):.1f}%)")

                    # Intervalo de confianca
                    ic = previsao.get("intervalo_confianca", {})
                    print(f"    - Intervalo ({ic.get('nivel', '80%')}): {ic.get('minimo', 0):.0f} - {ic.get('maximo', 0):.0f}")
            else:
                print(f"  ERRO: {result.get('error')}")
        else:
            print("  Sem dados para testar")

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()

print()
print("=" * 60)
print("TESTE CONCLUIDO")
print("=" * 60)
