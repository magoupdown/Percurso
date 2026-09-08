"""Expansão de consultas PT/EN (SPEC §11.3) via vocabulário do adaptador de domínio."""
from __future__ import annotations

from typing import List

from ..domains import obter_adaptador


def expandir(tema: str, instrumento: str, nivel: str, dominio: str = "musica", maximo: int = 6) -> List[str]:
    adaptador = obter_adaptador(dominio)
    consultas = adaptador.expandir_consulta(tema, instrumento, nivel)
    return consultas[:maximo]
