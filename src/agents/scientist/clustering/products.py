# -*- coding: utf-8 -*-
"""
Segmentacao de Produtos

Segmenta produtos por performance de vendas:
- Volume de vendas
- Margem de contribuicao
- Giro/Velocidade de venda

Categorias:
- Estrela: Alto volume, alta margem
- Vaca Leiteira: Alto volume, baixa margem
- Interrogacao: Baixo volume, alta margem
- Abacaxi: Baixo volume, baixa margem
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..config import CLUSTERING_CONFIG

logger = logging.getLogger(__name__)


class ProductSegmentation:
    """
    Segmenta produtos por performance.

    Metodos principais:
    - fit(): Segmenta produtos
    - get_segmentation_summary(): Retorna dict estruturado (para LLM)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o segmentador.

        Args:
            config: Configuracoes do K-Means (opcional)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn nao instalado")

        self.config = config or CLUSTERING_CONFIG.get("products", {})
        self.kmeans_config = CLUSTERING_CONFIG.get("kmeans", {})

        self.model: Optional[KMeans] = None
        self.scaler: Optional[StandardScaler] = None
        self.df_products: Optional[pd.DataFrame] = None
        self.segment_profiles: Dict[int, Dict] = {}
        self.metadata: Dict[str, Any] = {}

    def fit(
        self,
        df: pd.DataFrame,
        product_col: str = "CODPROD",
        quantity_col: str = "QTDNEG",
        value_col: str = "VLRTOT",
        cost_col: Optional[str] = None,
        n_clusters: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Segmenta produtos por performance.

        Args:
            df: DataFrame com dados de vendas
            product_col: Coluna de codigo do produto
            quantity_col: Coluna de quantidade
            value_col: Coluna de valor total
            cost_col: Coluna de custo (opcional, para calcular margem)
            n_clusters: Numero de clusters (None = automatico)

        Returns:
            Dict com metadados da segmentacao
        """
        # Calcular metricas por produto
        df_products = self._calculate_product_metrics(
            df, product_col, quantity_col, value_col, cost_col
        )

        if df_products.empty:
            return {
                "success": False,
                "error": "Nao foi possivel calcular metricas de produtos"
            }

        self.df_products = df_products

        # Determinar numero de clusters
        if n_clusters is None:
            n_clusters = self.config.get("default_n_clusters", 3)

        # Preparar features
        features = ["volume_vendas", "receita_total"]
        if "margem" in df_products.columns:
            features.append("margem")

        X = df_products[features].values

        # Normalizar
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Treinar K-Means
        self.model = KMeans(
            n_clusters=n_clusters,
            n_init=self.kmeans_config.get("n_init", 10),
            max_iter=self.kmeans_config.get("max_iter", 300),
            random_state=self.kmeans_config.get("random_state", 42)
        )

        self.df_products["cluster"] = self.model.fit_predict(X_scaled)

        # Calcular perfis
        self._calculate_segment_profiles()

        # Atribuir labels
        self._assign_segment_labels()

        # Metadados
        self.metadata = {
            "n_products": len(df_products),
            "n_clusters": n_clusters,
            "trained_at": datetime.now().isoformat(),
            "features": features,
        }

        return {
            "success": True,
            **self.metadata
        }

    def _calculate_product_metrics(
        self,
        df: pd.DataFrame,
        product_col: str,
        quantity_col: str,
        value_col: str,
        cost_col: Optional[str]
    ) -> pd.DataFrame:
        """Calcula metricas por produto."""
        df_copy = df.copy()

        # Agrupar por produto
        agg_dict = {
            quantity_col: "sum",
            value_col: "sum",
        }

        if cost_col and cost_col in df_copy.columns:
            agg_dict[cost_col] = "sum"

        products = df_copy.groupby(product_col).agg(agg_dict).reset_index()

        # Renomear colunas
        rename_map = {
            product_col: "codprod",
            quantity_col: "volume_vendas",
            value_col: "receita_total",
        }
        if cost_col:
            rename_map[cost_col] = "custo_total"

        products = products.rename(columns=rename_map)

        # Calcular margem se tiver custo
        if "custo_total" in products.columns:
            products["margem"] = (
                (products["receita_total"] - products["custo_total"]) /
                products["receita_total"] * 100
            ).fillna(0)

        # Calcular receita media por unidade
        products["receita_unitaria"] = (
            products["receita_total"] / products["volume_vendas"]
        ).fillna(0)

        return products

    def _calculate_segment_profiles(self) -> None:
        """Calcula perfil de cada segmento."""
        if self.df_products is None:
            return

        for cluster in self.df_products["cluster"].unique():
            segment = self.df_products[self.df_products["cluster"] == cluster]

            profile = {
                "n_products": len(segment),
                "volume_total": float(segment["volume_vendas"].sum()),
                "volume_mean": float(segment["volume_vendas"].mean()),
                "receita_total": float(segment["receita_total"].sum()),
                "receita_mean": float(segment["receita_total"].mean()),
            }

            if "margem" in segment.columns:
                profile["margem_mean"] = float(segment["margem"].mean())

            self.segment_profiles[cluster] = profile

    def _assign_segment_labels(self) -> None:
        """Atribui labels descritivos aos segmentos."""
        if not self.segment_profiles:
            return

        # Ordenar por receita total (descendente)
        sorted_clusters = sorted(
            self.segment_profiles.items(),
            key=lambda x: x[1]["receita_total"],
            reverse=True
        )

        labels = self.config.get("labels", {
            0: "Estrela",
            1: "Vaca Leiteira",
            2: "Abacaxi"
        })

        for i, (cluster, profile) in enumerate(sorted_clusters):
            label = labels.get(i, f"Categoria {i+1}")
            self.segment_profiles[cluster]["label"] = label

        # Adicionar label ao DataFrame
        label_map = {c: p["label"] for c, p in self.segment_profiles.items()}
        self.df_products["segment_label"] = self.df_products["cluster"].map(label_map)

    def get_segmentation_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo estruturado da segmentacao.

        ESTE E O METODO QUE O AGENTE LLM CHAMA VIA TOOL.

        Returns:
            Dict estruturado com segmentos e produtos
        """
        if self.df_products is None:
            return {
                "success": False,
                "error": "Modelo nao treinado. Execute fit() primeiro."
            }

        # Preparar resumo por segmento
        segmentos = []
        total_products = len(self.df_products)
        total_revenue = self.df_products["receita_total"].sum()
        total_volume = self.df_products["volume_vendas"].sum()

        for cluster, profile in self.segment_profiles.items():
            # Top produtos do segmento
            segment_products = self.df_products[self.df_products["cluster"] == cluster]
            top_products = segment_products.nlargest(5, "receita_total")[
                ["codprod", "volume_vendas", "receita_total"]
            ].to_dict(orient="records")

            segmentos.append({
                "nome": profile.get("label", f"Categoria {cluster}"),
                "cluster_id": int(cluster),
                "quantidade_produtos": profile["n_products"],
                "percentual_produtos": round(profile["n_products"] / total_products * 100, 1),
                "volume_total": round(profile["volume_total"], 0),
                "percentual_volume": round(profile["volume_total"] / total_volume * 100, 1),
                "receita_total": round(profile["receita_total"], 2),
                "percentual_receita": round(profile["receita_total"] / total_revenue * 100, 1),
                "receita_media": round(profile["receita_mean"], 2),
                "margem_media": round(profile.get("margem_mean", 0), 1),
                "top_produtos": top_products,
            })

        # Ordenar por receita
        segmentos = sorted(segmentos, key=lambda x: x["receita_total"], reverse=True)

        # Curva ABC
        curva_abc = self._calculate_abc_curve()

        return {
            "success": True,
            "total_produtos": total_products,
            "total_receita": round(float(total_revenue), 2),
            "total_volume": round(float(total_volume), 0),
            "n_segmentos": len(segmentos),
            "segmentos": segmentos,
            "curva_abc": curva_abc,
            "metadata": self.metadata
        }

    def _calculate_abc_curve(self) -> Dict[str, Any]:
        """Calcula curva ABC dos produtos."""
        if self.df_products is None:
            return {}

        # Ordenar por receita
        sorted_products = self.df_products.sort_values("receita_total", ascending=False)
        total_revenue = sorted_products["receita_total"].sum()

        # Calcular percentual acumulado
        sorted_products["pct_acumulado"] = (
            sorted_products["receita_total"].cumsum() / total_revenue * 100
        )

        # Classificar ABC
        n_total = len(sorted_products)

        a_count = len(sorted_products[sorted_products["pct_acumulado"] <= 80])
        b_count = len(sorted_products[
            (sorted_products["pct_acumulado"] > 80) &
            (sorted_products["pct_acumulado"] <= 95)
        ])
        c_count = n_total - a_count - b_count

        return {
            "classe_A": {
                "quantidade": a_count,
                "percentual_produtos": round(a_count / n_total * 100, 1),
                "percentual_receita": 80,
                "descricao": "Produtos que geram 80% da receita"
            },
            "classe_B": {
                "quantidade": b_count,
                "percentual_produtos": round(b_count / n_total * 100, 1),
                "percentual_receita": 15,
                "descricao": "Produtos que geram 15% da receita"
            },
            "classe_C": {
                "quantidade": c_count,
                "percentual_produtos": round(c_count / n_total * 100, 1),
                "percentual_receita": 5,
                "descricao": "Produtos que geram 5% da receita"
            },
        }

    def get_product_segment(self, codprod: int) -> Optional[Dict[str, Any]]:
        """
        Retorna segmento de um produto especifico.

        Args:
            codprod: Codigo do produto

        Returns:
            Dict com dados e segmento do produto
        """
        if self.df_products is None:
            return None

        product = self.df_products[self.df_products["codprod"] == codprod]

        if product.empty:
            return None

        row = product.iloc[0]
        return {
            "codprod": codprod,
            "segmento": row.get("segment_label", f"Cluster {row['cluster']}"),
            "cluster_id": int(row["cluster"]),
            "metricas": {
                "volume_vendas": float(row["volume_vendas"]),
                "receita_total": float(row["receita_total"]),
                "receita_unitaria": float(row.get("receita_unitaria", 0)),
                "margem": float(row.get("margem", 0)) if "margem" in row else None,
            }
        }
