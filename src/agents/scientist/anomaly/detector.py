# -*- coding: utf-8 -*-
"""
Detector de Anomalias com Isolation Forest

Detecta padroes anomalos em dados de vendas, compras ou estoque.

IMPORTANTE:
- Retorna DADOS ESTRUTURADOS (dict), nao texto
- O Agente LLM chama get_anomalies_summary() via tool
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn nao instalado. Instale com: pip install scikit-learn")

from ..config import ANOMALY_CONFIG

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detecta anomalias usando Isolation Forest.

    Metodos principais:
    - fit(): Treina o detector
    - detect(): Detecta anomalias em novos dados
    - get_anomalies_summary(): Retorna dict estruturado (para LLM)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o detector.

        Args:
            config: Configuracoes do Isolation Forest (opcional)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn nao instalado. Instale com: pip install scikit-learn")

        self.config = config or ANOMALY_CONFIG.get("isolation_forest", {})
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns: List[str] = []
        self.df_with_scores: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}

    def fit(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None,
        entity_type: str = "vendas"
    ) -> Dict[str, Any]:
        """
        Treina o detector de anomalias.

        Args:
            df: DataFrame com os dados
            feature_columns: Colunas a usar como features (opcional)
            entity_type: Tipo de entidade ('vendas', 'compras', 'estoque')

        Returns:
            Dict com metadados do treinamento
        """
        df_copy = df.copy()

        # Determinar features
        if feature_columns:
            self.feature_columns = feature_columns
        else:
            self.feature_columns = self._get_default_features(df_copy, entity_type)

        if not self.feature_columns:
            return {
                "success": False,
                "error": "Nenhuma feature valida encontrada nos dados"
            }

        # Filtrar apenas colunas existentes
        self.feature_columns = [c for c in self.feature_columns if c in df_copy.columns]

        if len(self.feature_columns) < 1:
            return {
                "success": False,
                "error": f"Features nao encontradas: {feature_columns}"
            }

        # Preparar dados
        X = df_copy[self.feature_columns].copy()

        # Converter para numerico e preencher NaN
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce')
        X = X.fillna(0)

        # Normalizar
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Criar e treinar modelo
        self.model = IsolationForest(
            contamination=self.config.get("contamination", 0.05),
            n_estimators=self.config.get("n_estimators", 100),
            max_samples=self.config.get("max_samples", "auto"),
            random_state=self.config.get("random_state", 42),
            n_jobs=-1
        )

        # Treinar
        self.model.fit(X_scaled)

        # Calcular scores para todos os dados
        scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)

        # Adicionar ao DataFrame
        self.df_with_scores = df_copy.copy()
        self.df_with_scores["_anomaly_score"] = scores
        self.df_with_scores["_is_anomaly"] = predictions == -1

        # Metadados
        n_anomalies = (predictions == -1).sum()
        self.metadata = {
            "entity_type": entity_type,
            "trained_at": datetime.now().isoformat(),
            "n_samples": len(df_copy),
            "n_features": len(self.feature_columns),
            "features": self.feature_columns,
            "n_anomalies": int(n_anomalies),
            "anomaly_rate": float(n_anomalies / len(df_copy) * 100),
        }

        return {
            "success": True,
            **self.metadata
        }

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detecta anomalias em novos dados.

        Args:
            df: DataFrame com novos dados

        Returns:
            DataFrame com colunas de score e flag de anomalia
        """
        if self.model is None:
            raise ValueError("Modelo nao treinado. Execute fit() primeiro.")

        df_copy = df.copy()

        # Preparar features
        X = df_copy[self.feature_columns].copy()
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce')
        X = X.fillna(0)

        # Normalizar
        X_scaled = self.scaler.transform(X)

        # Prever
        scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)

        df_copy["_anomaly_score"] = scores
        df_copy["_is_anomaly"] = predictions == -1

        return df_copy

    def get_anomalies_summary(
        self,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Retorna resumo estruturado das anomalias.

        ESTE E O METODO QUE O AGENTE LLM CHAMA VIA TOOL.

        Args:
            top_n: Numero de maiores anomalias a retornar

        Returns:
            Dict estruturado com:
            - total_anomalias: quantidade
            - taxa_anomalias: percentual
            - top_anomalias: piores casos
            - por_severidade: agrupado por nivel
        """
        if self.df_with_scores is None:
            return {
                "success": False,
                "error": "Modelo nao treinado. Execute fit() primeiro."
            }

        df = self.df_with_scores

        # Filtrar anomalias
        anomalias = df[df["_is_anomaly"]].copy()

        if anomalias.empty:
            return {
                "success": True,
                "total_anomalias": 0,
                "taxa_anomalias": 0,
                "mensagem": "Nenhuma anomalia detectada",
                "metadata": self.metadata
            }

        # Top N piores anomalias
        top_anomalias = anomalias.nsmallest(top_n, "_anomaly_score")

        # Preparar lista de anomalias
        anomalias_list = []
        for idx, row in top_anomalias.iterrows():
            anomalia = {
                "score": round(float(row["_anomaly_score"]), 4),
                "severidade": self._get_severity(row["_anomaly_score"]),
            }

            # Adicionar colunas relevantes
            for col in self.feature_columns:
                if col in row.index:
                    anomalia[col] = row[col]

            # Adicionar identificadores se existirem
            for id_col in ["NUNOTA", "CODPROD", "CODPARC", "DTNEG"]:
                if id_col in row.index:
                    value = row[id_col]
                    if pd.notna(value):
                        if isinstance(value, (pd.Timestamp, datetime)):
                            anomalia[id_col] = str(value.date())
                        else:
                            anomalia[id_col] = value

            anomalias_list.append(anomalia)

        # Agrupar por severidade
        severidade_counts = self._count_by_severity(anomalias)

        # Estatisticas das anomalias
        stats = self._calculate_anomaly_stats(anomalias)

        return {
            "success": True,
            "total_anomalias": int(len(anomalias)),
            "taxa_anomalias": round(float(len(anomalias) / len(df) * 100), 2),
            "total_registros": len(df),
            "por_severidade": severidade_counts,
            "top_anomalias": anomalias_list,
            "estatisticas": stats,
            "features_analisadas": self.feature_columns,
            "metadata": self.metadata
        }

    def _get_default_features(
        self,
        df: pd.DataFrame,
        entity_type: str
    ) -> List[str]:
        """Retorna features padrao para o tipo de entidade."""
        feature_map = {
            "vendas": ["VLRNOTA", "QTDNEG", "VLRUNIT", "VLRDESC"],
            "compras": ["VLRNOTA", "QTDNEG", "VLRUNIT"],
            "estoque": ["ESTOQUE", "RESERVADO", "DISPONIVEL"],
        }

        suggested = feature_map.get(entity_type, [])

        # Filtrar apenas colunas que existem
        return [c for c in suggested if c in df.columns]

    def _get_severity(self, score: float) -> str:
        """Determina severidade baseado no score."""
        thresholds = ANOMALY_CONFIG.get("alerts", {}).get("severity_thresholds", {})

        if score < thresholds.get("critical", -0.8):
            return "critica"
        elif score < thresholds.get("high", -0.6):
            return "alta"
        elif score < thresholds.get("medium", -0.4):
            return "media"
        else:
            return "baixa"

    def _count_by_severity(self, df: pd.DataFrame) -> Dict[str, int]:
        """Conta anomalias por severidade."""
        counts = {"critica": 0, "alta": 0, "media": 0, "baixa": 0}

        for score in df["_anomaly_score"]:
            severity = self._get_severity(score)
            counts[severity] += 1

        return counts

    def _calculate_anomaly_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula estatisticas das anomalias."""
        stats = {}

        for col in self.feature_columns:
            if col in df.columns:
                col_data = pd.to_numeric(df[col], errors='coerce')
                stats[col] = {
                    "media_anomalias": round(float(col_data.mean()), 2),
                    "max_anomalias": round(float(col_data.max()), 2),
                    "min_anomalias": round(float(col_data.min()), 2),
                }

        return stats
