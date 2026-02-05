# -*- coding: utf-8 -*-
"""
Segmentacao de Clientes (RFM Analysis)

Segmenta clientes usando analise RFM:
- Recency: Dias desde a ultima compra
- Frequency: Numero de compras
- Monetary: Valor total gasto

IMPORTANTE:
- Retorna DADOS ESTRUTURADOS (dict), nao texto
- O Agente LLM chama get_segmentation_summary() via tool
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


class CustomerSegmentation:
    """
    Segmenta clientes usando analise RFM e K-Means.

    Segmentos padrao:
    - VIP: Alta frequencia, alto valor, recente
    - Regular: Frequencia e valor medios
    - Esporadico: Baixa frequencia
    - Inativo: Muito tempo sem comprar
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o segmentador.

        Args:
            config: Configuracoes do K-Means (opcional)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn nao instalado")

        self.config = config or CLUSTERING_CONFIG.get("customers", {})
        self.kmeans_config = CLUSTERING_CONFIG.get("kmeans", {})

        self.model: Optional[KMeans] = None
        self.scaler: Optional[StandardScaler] = None
        self.df_rfm: Optional[pd.DataFrame] = None
        self.segment_profiles: Dict[int, Dict] = {}
        self.metadata: Dict[str, Any] = {}

    def fit(
        self,
        df: pd.DataFrame,
        customer_col: str = "CODPARC",
        date_col: str = "DTNEG",
        value_col: str = "VLRNOTA",
        n_clusters: Optional[int] = None,
        reference_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula RFM e segmenta clientes.

        Args:
            df: DataFrame com dados de vendas
            customer_col: Coluna de identificacao do cliente
            date_col: Coluna de data
            value_col: Coluna de valor
            n_clusters: Numero de clusters (None = automatico)
            reference_date: Data de referencia para calculo de recencia

        Returns:
            Dict com metadados da segmentacao
        """
        # Calcular RFM
        df_rfm = self._calculate_rfm(
            df, customer_col, date_col, value_col, reference_date
        )

        if df_rfm.empty:
            return {
                "success": False,
                "error": "Nao foi possivel calcular RFM"
            }

        self.df_rfm = df_rfm

        # Determinar numero de clusters
        if n_clusters is None:
            n_clusters = self.config.get("default_n_clusters", 4)

        # Normalizar features
        features = ["recency", "frequency", "monetary"]
        X = df_rfm[features].values

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Treinar K-Means
        self.model = KMeans(
            n_clusters=n_clusters,
            n_init=self.kmeans_config.get("n_init", 10),
            max_iter=self.kmeans_config.get("max_iter", 300),
            random_state=self.kmeans_config.get("random_state", 42)
        )

        self.df_rfm["cluster"] = self.model.fit_predict(X_scaled)

        # Calcular perfis dos segmentos
        self._calculate_segment_profiles()

        # Atribuir labels aos segmentos
        self._assign_segment_labels()

        # Metadados
        self.metadata = {
            "n_customers": len(df_rfm),
            "n_clusters": n_clusters,
            "trained_at": datetime.now().isoformat(),
            "features": features,
        }

        return {
            "success": True,
            **self.metadata
        }

    def _calculate_rfm(
        self,
        df: pd.DataFrame,
        customer_col: str,
        date_col: str,
        value_col: str,
        reference_date: Optional[str]
    ) -> pd.DataFrame:
        """Calcula metricas RFM."""
        df_copy = df.copy()

        # Verificar se colunas existem
        if customer_col not in df_copy.columns:
            logger.warning(f"Coluna {customer_col} nao encontrada. Colunas disponiveis: {list(df_copy.columns)}")
            return pd.DataFrame()

        if date_col not in df_copy.columns:
            logger.warning(f"Coluna {date_col} nao encontrada. Colunas disponiveis: {list(df_copy.columns)}")
            return pd.DataFrame()

        if value_col not in df_copy.columns:
            logger.warning(f"Coluna {value_col} nao encontrada. Colunas disponiveis: {list(df_copy.columns)}")
            return pd.DataFrame()

        # Verificar se coluna de data tem dados validos ANTES de converter
        n_nulos_antes = df_copy[date_col].isna().sum()
        n_total = len(df_copy)

        if n_nulos_antes == n_total:
            logger.error(
                f"ERRO: Coluna {date_col} esta 100% nula ({n_nulos_antes}/{n_total}). "
                f"Verifique a extracao de dados. "
                f"Dica: Tente usar DTFATUR como alternativa se DTNEG estiver vazia."
            )
            return pd.DataFrame()

        # Converter data
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])

        if df_copy.empty:
            logger.error(
                f"DataFrame vazio apos conversao de data. "
                f"Valores nulos antes: {n_nulos_antes}/{n_total}. "
                f"Formato da coluna pode estar incorreto."
            )
            return pd.DataFrame()

        # Data de referencia
        if reference_date:
            ref_date = pd.to_datetime(reference_date)
        else:
            ref_date = df_copy[date_col].max()

        # Calcular RFM por cliente
        # Recency: dias desde a ultima compra
        recency = df_copy.groupby(customer_col)[date_col].max().reset_index()
        recency["recency"] = (ref_date - recency[date_col]).dt.days
        recency = recency[[customer_col, "recency"]]

        # Frequency: numero de transacoes unicas
        if "NUNOTA" in df_copy.columns:
            frequency = df_copy.groupby(customer_col)["NUNOTA"].nunique().reset_index()
            frequency.columns = [customer_col, "frequency"]
        else:
            frequency = df_copy.groupby(customer_col).size().reset_index()
            frequency.columns = [customer_col, "frequency"]

        # Monetary: valor total
        monetary = df_copy.groupby(customer_col)[value_col].sum().reset_index()
        monetary.columns = [customer_col, "monetary"]

        # Merge
        rfm = recency.merge(frequency, on=customer_col)
        rfm = rfm.merge(monetary, on=customer_col)

        # Remover clientes sem compras
        rfm = rfm[rfm["monetary"] > 0]

        return rfm

    def _calculate_segment_profiles(self) -> None:
        """Calcula perfil de cada segmento."""
        if self.df_rfm is None:
            return

        for cluster in self.df_rfm["cluster"].unique():
            segment = self.df_rfm[self.df_rfm["cluster"] == cluster]

            self.segment_profiles[cluster] = {
                "n_customers": len(segment),
                "recency_mean": float(segment["recency"].mean()),
                "frequency_mean": float(segment["frequency"].mean()),
                "monetary_mean": float(segment["monetary"].mean()),
                "monetary_total": float(segment["monetary"].sum()),
            }

    def _assign_segment_labels(self) -> None:
        """Atribui labels descritivos aos segmentos baseado no perfil."""
        if not self.segment_profiles:
            return

        # Ordenar por valor monetario medio (descendente)
        sorted_clusters = sorted(
            self.segment_profiles.items(),
            key=lambda x: x[1]["monetary_mean"],
            reverse=True
        )

        labels = self.config.get("labels", {
            0: "VIP",
            1: "Regular",
            2: "Esporadico",
            3: "Inativo"
        })

        # Atribuir labels na ordem do valor
        for i, (cluster, profile) in enumerate(sorted_clusters):
            label = labels.get(i, f"Segmento {i+1}")
            self.segment_profiles[cluster]["label"] = label

        # Adicionar label ao DataFrame
        label_map = {c: p["label"] for c, p in self.segment_profiles.items()}
        self.df_rfm["segment_label"] = self.df_rfm["cluster"].map(label_map)

    def get_segmentation_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo estruturado da segmentacao.

        ESTE E O METODO QUE O AGENTE LLM CHAMA VIA TOOL.

        Returns:
            Dict estruturado com segmentos e perfis
        """
        if self.df_rfm is None:
            return {
                "success": False,
                "error": "Modelo nao treinado. Execute fit() primeiro."
            }

        # Preparar resumo por segmento
        segmentos = []
        total_customers = len(self.df_rfm)
        total_revenue = self.df_rfm["monetary"].sum()

        for cluster, profile in self.segment_profiles.items():
            segmentos.append({
                "nome": profile.get("label", f"Segmento {cluster}"),
                "cluster_id": int(cluster),
                "quantidade_clientes": profile["n_customers"],
                "percentual_clientes": round(profile["n_customers"] / total_customers * 100, 1),
                "recencia_media_dias": round(profile["recency_mean"], 0),
                "frequencia_media": round(profile["frequency_mean"], 1),
                "valor_medio": round(profile["monetary_mean"], 2),
                "valor_total": round(profile["monetary_total"], 2),
                "percentual_receita": round(profile["monetary_total"] / total_revenue * 100, 1),
            })

        # Ordenar por valor
        segmentos = sorted(segmentos, key=lambda x: x["valor_total"], reverse=True)

        # Insights automaticos
        insights = self._generate_insights(segmentos)

        return {
            "success": True,
            "total_clientes": total_customers,
            "total_receita": round(float(total_revenue), 2),
            "n_segmentos": len(segmentos),
            "segmentos": segmentos,
            "insights": insights,
            "metadata": self.metadata
        }

    def _generate_insights(self, segmentos: List[Dict]) -> List[str]:
        """Gera insights automaticos sobre a segmentacao."""
        insights = []

        if not segmentos:
            return insights

        # Top segment
        top = segmentos[0]
        insights.append(
            f"O segmento '{top['nome']}' representa {top['percentual_clientes']:.1f}% "
            f"dos clientes mas gera {top['percentual_receita']:.1f}% da receita"
        )

        # Concentracao
        if len(segmentos) >= 2:
            top2_revenue = segmentos[0]["percentual_receita"] + segmentos[1]["percentual_receita"]
            top2_customers = segmentos[0]["percentual_clientes"] + segmentos[1]["percentual_clientes"]
            insights.append(
                f"Os 2 melhores segmentos ({top2_customers:.1f}% dos clientes) "
                f"geram {top2_revenue:.1f}% da receita"
            )

        # Clientes inativos (maior recencia)
        maior_recencia = max(segmentos, key=lambda x: x["recencia_media_dias"])
        if maior_recencia["recencia_media_dias"] > 90:
            insights.append(
                f"O segmento '{maior_recencia['nome']}' tem {maior_recencia['quantidade_clientes']} "
                f"clientes sem comprar ha {maior_recencia['recencia_media_dias']:.0f} dias em media"
            )

        return insights

    def get_customer_segment(self, codparc: int) -> Optional[Dict[str, Any]]:
        """
        Retorna segmento de um cliente especifico.

        Args:
            codparc: Codigo do parceiro/cliente

        Returns:
            Dict com dados RFM e segmento do cliente
        """
        if self.df_rfm is None:
            return None

        customer = self.df_rfm[self.df_rfm.iloc[:, 0] == codparc]

        if customer.empty:
            return None

        row = customer.iloc[0]
        return {
            "codparc": codparc,
            "segmento": row.get("segment_label", f"Cluster {row['cluster']}"),
            "cluster_id": int(row["cluster"]),
            "rfm": {
                "recency": int(row["recency"]),
                "frequency": int(row["frequency"]),
                "monetary": float(row["monetary"]),
            }
        }
