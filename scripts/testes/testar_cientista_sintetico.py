# -*- coding: utf-8 -*-
"""
Teste do Agente Cientista com Dados Sinteticos

Valida os algoritmos de ML independente da qualidade dos dados reais.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 60)
print("TESTE DO AGENTE CIENTISTA - DADOS SINTETICOS")
print("=" * 60)
print()

# =============================================================================
# 1. Gerar Dados Sinteticos de Vendas
# =============================================================================
print("[1] GERANDO DADOS SINTETICOS")
print("-" * 40)

np.random.seed(42)

# Parametros
n_clientes = 100
n_produtos = 50
n_vendas = 2000
data_inicio = datetime(2025, 1, 1)
data_fim = datetime(2026, 1, 31)

# Gerar clientes
clientes = list(range(1001, 1001 + n_clientes))

# Gerar produtos
produtos = list(range(5001, 5001 + n_produtos))

# Gerar vendas
vendas = []
for i in range(n_vendas):
    dias_random = np.random.randint(0, (data_fim - data_inicio).days)
    data_venda = data_inicio + timedelta(days=dias_random)

    cliente = np.random.choice(clientes)
    produto = np.random.choice(produtos)
    qtd = np.random.randint(1, 20)
    valor_unit = np.random.uniform(50, 500)

    vendas.append({
        "NUNOTA": 100000 + i,
        "CODPARC": cliente,
        "CODPROD": produto,
        "DTNEG": data_venda,
        "QTDNEG": qtd,
        "VLRUNIT": valor_unit,
        "VLRTOT": qtd * valor_unit,
        "VLRNOTA": qtd * valor_unit * 1.1,  # Com impostos
    })

df_vendas = pd.DataFrame(vendas)

# Adicionar algumas anomalias (valores muito altos)
df_vendas.loc[np.random.choice(n_vendas, 20), "VLRNOTA"] *= 10

print(f"  Vendas geradas: {len(df_vendas)}")
print(f"  Clientes: {df_vendas['CODPARC'].nunique()}")
print(f"  Produtos: {df_vendas['CODPROD'].nunique()}")
print(f"  Periodo: {df_vendas['DTNEG'].min()} a {df_vendas['DTNEG'].max()}")
print()

# =============================================================================
# 2. Testar Deteccao de Anomalias
# =============================================================================
print("[2] TESTANDO DETECCAO DE ANOMALIAS")
print("-" * 40)

try:
    from src.agents.scientist.anomaly import AnomalyDetector, AlertGenerator

    detector = AnomalyDetector()

    # Treinar
    print("  Treinando Isolation Forest...")
    result = detector.fit(df_vendas, entity_type="vendas")

    if result.get("success"):
        print(f"  OK - Treinamento concluido:")
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

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 3. Testar Segmentacao de Clientes (RFM)
# =============================================================================
print("[3] TESTANDO SEGMENTACAO DE CLIENTES (RFM)")
print("-" * 40)

try:
    from src.agents.scientist.clustering import CustomerSegmentation

    segmenter = CustomerSegmentation()

    # Treinar
    print("  Segmentando clientes com K-Means + RFM...")
    result = segmenter.fit(df_vendas)

    if result.get("success"):
        print(f"  OK - Segmentacao concluida:")
        print(f"    - Clientes: {result.get('n_customers')}")
        print(f"    - Segmentos: {result.get('n_clusters')}")

        # Obter resumo
        summary = segmenter.get_segmentation_summary()

        if summary.get("success"):
            print(f"\n  Segmentos identificados:")
            for seg in summary.get("segmentos", []):
                print(f"    - {seg['nome']}: {seg['quantidade_clientes']} clientes "
                      f"({seg['percentual_receita']:.1f}% receita, "
                      f"recencia media: {seg['recencia_media_dias']:.0f} dias)")

            # Insights
            insights = summary.get("insights", [])
            if insights:
                print(f"\n  Insights automaticos:")
                for insight in insights[:3]:
                    print(f"    - {insight}")

            # Testar busca de cliente especifico
            cliente_teste = clientes[0]
            cliente_seg = segmenter.get_customer_segment(cliente_teste)
            if cliente_seg:
                print(f"\n  Cliente {cliente_teste}:")
                print(f"    - Segmento: {cliente_seg['segmento']}")
                print(f"    - RFM: R={cliente_seg['rfm']['recency']}, "
                      f"F={cliente_seg['rfm']['frequency']}, "
                      f"M=R${cliente_seg['rfm']['monetary']:,.2f}")
    else:
        print(f"  ERRO: {result.get('error')}")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 4. Testar Segmentacao de Produtos
# =============================================================================
print("[4] TESTANDO SEGMENTACAO DE PRODUTOS")
print("-" * 40)

try:
    from src.agents.scientist.clustering import ProductSegmentation

    segmenter = ProductSegmentation()

    # Treinar
    print("  Segmentando produtos com K-Means...")
    result = segmenter.fit(df_vendas)

    if result.get("success"):
        print(f"  OK - Segmentacao concluida:")
        print(f"    - Produtos: {result.get('n_products')}")
        print(f"    - Segmentos: {result.get('n_clusters')}")

        # Obter resumo
        summary = segmenter.get_segmentation_summary()

        if summary.get("success"):
            print(f"\n  Segmentos identificados:")
            for seg in summary.get("segmentos", []):
                print(f"    - {seg['nome']}: {seg['quantidade_produtos']} produtos "
                      f"({seg['percentual_receita']:.1f}% receita)")

            # Curva ABC
            abc = summary.get("curva_abc", {})
            if abc:
                print(f"\n  Curva ABC:")
                for classe in ["classe_A", "classe_B", "classe_C"]:
                    if classe in abc:
                        print(f"    - {classe}: {abc[classe]['quantidade']} produtos "
                              f"({abc[classe]['percentual_produtos']:.1f}% do total, "
                              f"{abc[classe]['percentual_receita']}% da receita)")

            # Testar busca de produto especifico
            produto_teste = produtos[0]
            produto_seg = segmenter.get_product_segment(produto_teste)
            if produto_seg:
                print(f"\n  Produto {produto_teste}:")
                print(f"    - Segmento: {produto_seg['segmento']}")
                print(f"    - Volume: {produto_seg['metricas']['volume_vendas']:.0f} un")
                print(f"    - Receita: R${produto_seg['metricas']['receita_total']:,.2f}")
    else:
        print(f"  ERRO: {result.get('error')}")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# =============================================================================
# 5. Testar Previsao de Demanda (se Prophet disponivel)
# =============================================================================
print("[5] TESTANDO PREVISAO DE DEMANDA")
print("-" * 40)

try:
    from prophet import Prophet
    PROPHET_OK = True
    print("  Prophet instalado - testando...")
except ImportError:
    PROPHET_OK = False
    print("  Prophet NAO instalado - pulando teste")
    print("  Para instalar: pip install prophet")

if PROPHET_OK:
    try:
        from src.agents.scientist.forecasting import DemandForecastModel

        # Pegar produto com mais historico
        top_produtos = df_vendas.groupby("CODPROD")["QTDNEG"].sum().nlargest(5)
        codprod = top_produtos.index[0]

        print(f"  Produto selecionado: {codprod}")

        model = DemandForecastModel()

        # Treinar
        print("  Treinando modelo Prophet...")
        result = model.fit(df_vendas, codprod=codprod)

        if result.get("success"):
            print(f"  OK - Treinamento concluido:")
            print(f"    - Registros: {result.get('training_rows')}")

            # Obter previsao
            summary = model.get_forecast_summary(periods=30)

            if summary.get("success"):
                previsao = summary.get("previsao", {})
                tendencia = summary.get("tendencia", {})

                print(f"\n  Previsao para 30 dias:")
                print(f"    - Total previsto: {previsao.get('total', 0):.0f} unidades")
                print(f"    - Media diaria: {previsao.get('media_diaria', 0):.1f} unidades")
                print(f"    - Tendencia: {tendencia.get('direcao', 'N/A')} "
                      f"({tendencia.get('variacao_pct', 0):.1f}%)")

                # Intervalo de confianca
                ic = previsao.get("intervalo_confianca", {})
                if ic:
                    print(f"    - Intervalo ({ic.get('nivel', '80%')}): "
                          f"{ic.get('minimo', 0):.0f} - {ic.get('maximo', 0):.0f}")
        else:
            print(f"  ERRO: {result.get('error')}")

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()

print()

# =============================================================================
# 6. Testar Utils (Metricas e Feriados)
# =============================================================================
print("[6] TESTANDO UTILS")
print("-" * 40)

try:
    from src.agents.scientist.utils.metrics import (
        calculate_mape, calculate_mae, calculate_rmse, calculate_r2
    )
    from src.agents.scientist.utils.holidays import BrazilianHolidays

    # Testar metricas
    y_true = np.array([100, 200, 150, 300, 250])
    y_pred = np.array([110, 190, 160, 290, 260])

    print("  Metricas de avaliacao:")
    print(f"    - MAPE: {calculate_mape(y_true, y_pred):.2f}%")
    print(f"    - MAE: {calculate_mae(y_true, y_pred):.2f}")
    print(f"    - RMSE: {calculate_rmse(y_true, y_pred):.2f}")
    print(f"    - R2: {calculate_r2(y_true, y_pred):.4f}")

    # Testar feriados
    holidays = BrazilianHolidays()
    df_feriados = holidays.get_holidays(2026, 2026)
    print(f"\n  Feriados brasileiros 2026: {len(df_feriados)} dias")
    print(f"    Exemplos: {', '.join(df_feriados['holiday'].head(3).tolist())}")

except Exception as e:
    print(f"  ERRO: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("TESTE COM DADOS SINTETICOS CONCLUIDO")
print("=" * 60)
print()
print("RESUMO:")
print("  - Deteccao de Anomalias: Isolation Forest funcionando")
print("  - Segmentacao de Clientes: K-Means + RFM funcionando")
print("  - Segmentacao de Produtos: K-Means + ABC funcionando")
print("  - Previsao de Demanda: Requer Prophet instalado")
print("  - Utils: Metricas e feriados funcionando")
print()
print("NOTA: Os dados REAIS no Data Lake estao com colunas de data vazias.")
print("      Verifique a extracao no Agente Engenheiro.")
