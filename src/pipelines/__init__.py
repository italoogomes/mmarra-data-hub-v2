# -*- coding: utf-8 -*-
"""
Pipelines de dados do MMarra Data Hub

Pipelines são fluxos automatizados de:
- Extração (Sankhya → Raw)
- Transformação (Raw → Processed)
- Carga (Processed → Curated)
"""

from .extracao import PipelineExtracao

__all__ = ['PipelineExtracao']
