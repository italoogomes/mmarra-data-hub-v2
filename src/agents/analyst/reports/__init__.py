# -*- coding: utf-8 -*-
"""
Gerador de Relatorios do Agente Analista

Gera relatorios HTML a partir de KPIs calculados.
Usa Jinja2 para templates.
"""

from .generator import ReportGenerator

__all__ = ['ReportGenerator']
