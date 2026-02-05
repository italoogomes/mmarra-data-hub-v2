# -*- coding: utf-8 -*-
"""
Script para Treinar Modelos de Previsão de Demanda

Usa os dados extraídos do Sankhya para treinar o modelo Prophet.

Uso:
    python scripts/treinar_modelos.py
"""

import sys
from pathlib import Path

# Adicionar src ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Função principal para treinar modelos."""

    # 1. Carregar dados de vendas
    vendas_path = ROOT_DIR / "src/data/raw/vendas/vendas.parquet"

    if not vendas_path.exists():
        logger.error(f"Arquivo não encontrado: {vendas_path}")
        return

    logger.info(f"Carregando dados de: {vendas_path}")
    df = pd.read_parquet(vendas_path)

    logger.info(f"Registros carregados: {len(df)}")
    logger.info(f"Colunas: {df.columns.tolist()}")
    logger.info(f"Período: {df['DTNEG'].min()} a {df['DTNEG'].max()}")

    # 2. Identificar produtos mais vendidos
    logger.info("\n--- TOP 10 PRODUTOS MAIS VENDIDOS ---")
    top_produtos = df.groupby('CODPROD').agg({
        'QTDNEG': 'sum',
        'DESCRPROD': 'first'
    }).sort_values('QTDNEG', ascending=False).head(10)

    for idx, (codprod, row) in enumerate(top_produtos.iterrows(), 1):
        logger.info(f"{idx}. Produto {codprod}: {row['DESCRPROD'][:50]} - {row['QTDNEG']:.0f} unidades")

    # 3. Importar modelo
    try:
        from src.agents.scientist.forecasting import DemandForecastModel
    except ImportError as e:
        logger.error(f"Erro ao importar modelo: {e}")
        logger.error("Instale as dependências: pip install prophet")
        return

    # 4. Treinar modelo para o produto mais vendido
    codprod_top = top_produtos.index[0]
    descr_top = top_produtos.loc[codprod_top, 'DESCRPROD']

    logger.info(f"\n--- TREINANDO MODELO PARA PRODUTO {codprod_top} ---")
    logger.info(f"Descrição: {descr_top}")

    model = DemandForecastModel()

    resultado_treino = model.fit(
        df=df,
        codprod=codprod_top,
        date_col="DTNEG",
        value_col="QTDNEG"
    )

    if not resultado_treino.get("success"):
        logger.error(f"Erro no treinamento: {resultado_treino.get('error')}")
        return

    logger.info(f"Treinamento concluído: {resultado_treino.get('training_rows')} registros")

    # 5. Gerar previsão
    logger.info("\n--- PREVISÃO PARA OS PRÓXIMOS 30 DIAS ---")

    previsao = model.get_forecast_summary(periods=30)

    if previsao.get("success"):
        prev = previsao["previsao"]
        tend = previsao["tendencia"]

        logger.info(f"Período: {previsao['periodo']['inicio']} a {previsao['periodo']['fim']}")
        logger.info(f"Previsão total: {prev['total']:.0f} unidades")
        logger.info(f"Média diária: {prev['media_diaria']:.1f} unidades")
        logger.info(f"Intervalo de confiança ({prev['intervalo_confianca']['nivel']}): "
                   f"{prev['intervalo_confianca']['minimo']:.0f} - {prev['intervalo_confianca']['maximo']:.0f}")
        logger.info(f"Tendência: {tend['direcao']} ({tend['variacao_pct']:.1f}%)")

        # Picos previstos
        if previsao.get("picos_previstos"):
            logger.info("\nPicos previstos:")
            for pico in previsao["picos_previstos"][:3]:
                logger.info(f"  - {pico['data']} ({pico['dia_semana']}): {pico['previsao']:.0f} unidades")

        # Avaliação do modelo
        if previsao.get("avaliacao"):
            aval = previsao["avaliacao"]
            logger.info(f"\nAvaliação do modelo:")
            logger.info(f"  MAPE: {aval.get('mape', 'N/A')}")
            logger.info(f"  MAE: {aval.get('mae', 'N/A')}")
            logger.info(f"  R²: {aval.get('r2', 'N/A')}")
    else:
        logger.error(f"Erro na previsão: {previsao.get('error')}")
        return

    # 6. Salvar modelo
    logger.info("\n--- SALVANDO MODELO ---")
    try:
        path_salvo = model.save()
        logger.info(f"Modelo salvo em: {path_salvo}")
    except Exception as e:
        logger.warning(f"Não foi possível salvar o modelo: {e}")

    logger.info("\n✅ Treinamento concluído com sucesso!")

    # Retornar previsão para uso em outros scripts
    return previsao


if __name__ == "__main__":
    main()
