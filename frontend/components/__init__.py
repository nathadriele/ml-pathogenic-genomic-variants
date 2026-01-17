"""
Components Streamlit para VariantClassifier.

Este módulo contém componentes reutilizáveis para a interface Streamlit.
"""

from .variant_card import display_variant_card
from .acmg_criteria import display_acmg_criteria

__all__ = [
    "display_variant_card",
    "display_acmg_criteria",
]
