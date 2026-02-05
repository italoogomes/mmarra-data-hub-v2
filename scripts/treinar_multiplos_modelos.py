# -*- coding: utf-8 -*-
"""
Treina modelos Prophet para os TOP N produtos mais vendidos.

Uso:
    python scripts/treinar_multiplos_modelos.py [--top N] [--periodos DIAS]
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


def treinar_produtos(top_n: int = 20, periodos: int = 30):
    """
    Treina modelos Prophet para os TOP N produtos.

    Args:
        top_n: Número de produtos para treinar
        periodos: Dias de previsão
    """
    print("=" * 70)
    print(f"TREINAMENTO DE MODELOS PROPHET - TOP {top_n} PRODUTOS")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Carregar dados
    vendas_path = ROOT_DIR / "src/data/raw/vendas/vendas.parquet"

    if not vendas_path.exists():
        logger.error(f"Arquivo não encontrado: {vendas_path}")
        logger.error("Execute primeiro: python scripts/extracao/extrair_vendas_completo.py")
        return []

    logger.info(f"Carregando dados de: {vendas_path}")
    df = pd.read_parquet(vendas_path)
    logger.info(f"Registros: {len(df):,}".replace(",", "."))

    # 2. Identificar TOP N produtos
    logger.info(f"\n--- TOP {top_n} PRODUTOS MAIS VENDIDOS ---")

    # Garantir que DTNEG é datetime
    df['DTNEG'] = pd.to_datetime(df['DTNEG'], errors='coerce')

    # Calcular métricas por produto
    produtos_stats = df.groupby(['CODPROD', 'DESCRPROD']).agg({
        'QTDNEG': 'sum',
        'VLRTOT': 'sum',
        'DTNEG': ['min', 'max', 'count']
    }).reset_index()

    produtos_stats.columns = [
        'CODPROD', 'DESCRPROD', 'QTD_TOTAL', 'VALOR_TOTAL',
        'PRIMEIRA_VENDA', 'ULTIMA_VENDA', 'NUM_VENDAS'
    ]

    # Filtrar produtos com histórico suficiente (mínimo 30 dias)
    produtos_stats['DIAS_HISTORICO'] = (
        produtos_stats['ULTIMA_VENDA'] - produtos_stats['PRIMEIRA_VENDA']
    ).dt.days

    produtos_validos = produtos_stats[produtos_stats['DIAS_HISTORICO'] >= 30]

    # Ordenar por quantidade vendida
    top_produtos = produtos_validos.nlargest(top_n, 'QTD_TOTAL')

    print(f"\n{'#':<3} {'CODPROD':<10} {'DESCRICAO':<40} {'QTD':>10} {'VALOR':>15}")
    print("-" * 80)

    for idx, row in top_produtos.iterrows():
        desc = row['DESCRPROD'][:38] if row['DESCRPROD'] else 'N/A'
        print(f"{top_produtos.index.get_loc(idx)+1:<3} {int(row['CODPROD']):<10} {desc:<40} "
              f"{row['QTD_TOTAL']:>10,.0f} R$ {row['VALOR_TOTAL']:>12,.2f}".replace(",", "."))

    # 3. Importar modelo
    try:
        from src.agents.scientist.forecasting import DemandForecastModel
    except ImportError as e:
        logger.error(f"Erro ao importar modelo: {e}")
        logger.error("Instale as dependências: pip install prophet")
        return []

    # 4. Treinar cada produto
    resultados = []
    modelos_salvos = []

    print("\n" + "=" * 70)
    print("TREINAMENTO")
    print("=" * 70)

    for idx, row in top_produtos.iterrows():
        codprod = int(row['CODPROD'])
        descr = row['DESCRPROD'][:50] if row['DESCRPROD'] else 'N/A'
        posicao = top_produtos.index.get_loc(idx) + 1

        print(f"\n[{posicao}/{top_n}] Produto {codprod}: {descr}")
        print("-" * 60)

        try:
            model = DemandForecastModel()

            resultado_treino = model.fit(
                df=df,
                codprod=codprod,
                date_col="DTNEG",
                value_col="QTDNEG"
            )

            if not resultado_treino.get("success"):
                print(f"  [X] Erro: {resultado_treino.get('error')}")
                resultados.append({
                    'codprod': codprod,
                    'descricao': descr,
                    'sucesso': False,
                    'erro': resultado_treino.get('error')
                })
                continue

            # Gerar previsão
            previsao = model.get_forecast_summary(periods=periodos)

            if previsao.get("success"):
                prev = previsao["previsao"]
                tend = previsao["tendencia"]
                aval = previsao.get("avaliacao", {})

                print(f"  [OK] Treinado com {resultado_treino.get('training_rows', 0)} registros")
                print(f"       Previsão {periodos} dias: {prev['total']:.0f} unidades")
                print(f"       Tendência: {tend['direcao']} ({tend['variacao_pct']:.1f}%)")

                if aval.get('mape'):
                    print(f"       MAPE: {aval['mape']:.1f}%")

                # Salvar modelo
                try:
                    path_salvo = model.save()
                    modelos_salvos.append(path_salvo)
                    print(f"       Modelo salvo: {Path(path_salvo).name}")
                except Exception as e:
                    print(f"       [!] Não salvou: {e}")

                resultados.append({
                    'codprod': codprod,
                    'descricao': descr,
                    'sucesso': True,
                    'previsao_total': prev['total'],
                    'media_diaria': prev['media_diaria'],
                    'tendencia': tend['direcao'],
                    'variacao_pct': tend['variacao_pct'],
                    'mape': aval.get('mape'),
                    'mae': aval.get('mae'),
                    'r2': aval.get('r2')
                })
            else:
                print(f"  [X] Erro na previsão: {previsao.get('error')}")
                resultados.append({
                    'codprod': codprod,
                    'descricao': descr,
                    'sucesso': False,
                    'erro': previsao.get('error')
                })

        except Exception as e:
            print(f"  [X] Erro: {e}")
            resultados.append({
                'codprod': codprod,
                'descricao': descr,
                'sucesso': False,
                'erro': str(e)
            })

    # 5. Resumo final
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)

    sucessos = sum(1 for r in resultados if r.get('sucesso'))
    falhas = len(resultados) - sucessos

    print(f"Produtos processados: {len(resultados)}")
    print(f"Modelos treinados: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Modelos salvos em: src/agents/scientist/models/demand/")

    if modelos_salvos:
        print(f"\nArquivos gerados:")
        for path in modelos_salvos:
            print(f"  - {Path(path).name}")

    # Salvar relatório
    if resultados:
        df_resultado = pd.DataFrame(resultados)
        relatorio_path = ROOT_DIR / "output" / "reports" / f"treinamento_prophet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        relatorio_path.parent.mkdir(parents=True, exist_ok=True)
        df_resultado.to_csv(relatorio_path, index=False, encoding='utf-8-sig')
        print(f"\nRelatório salvo em: {relatorio_path}")

    print("=" * 70)
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return resultados


def main():
    parser = argparse.ArgumentParser(
        description="Treina modelos Prophet para os TOP N produtos"
    )
    parser.add_argument(
        "--top", type=int, default=20,
        help="Número de produtos para treinar (default: 20)"
    )
    parser.add_argument(
        "--periodos", type=int, default=30,
        help="Dias de previsão (default: 30)"
    )

    args = parser.parse_args()

    resultados = treinar_produtos(top_n=args.top, periodos=args.periodos)

    # Retornar 0 se pelo menos metade treinou com sucesso
    sucessos = sum(1 for r in resultados if r.get('sucesso'))
    return 0 if sucessos >= len(resultados) / 2 else 1


if __name__ == "__main__":
    sys.exit(main())
