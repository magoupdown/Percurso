"""CRMG — Currículo Referência de Minas Gerais (recorte Arte/Música), SPEC §10.1."""
from __future__ import annotations

from typing import Dict

from .bncc import BaseCurricular, Habilidade, carregar


def crmg_arte() -> BaseCurricular:
    return carregar("crmg_arte")


def todas_crmg() -> Dict[str, Habilidade]:
    return {h.codigo: h for h in crmg_arte().habilidades}
