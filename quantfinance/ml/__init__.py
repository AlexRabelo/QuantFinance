"""Módulo de ML: engenharia de features e utilidades de treino.

Foco inicial em exportar features a partir dos Parquets enriquecidos
para facilitar prototipagem em notebooks ou pipelines externos.
"""

from .features import build_features, export_features

__all__ = [
    "build_features",
    "export_features",
]

