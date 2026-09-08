"""Pesquisa externa (roadmap, SPEC §11.2): interface definida, desativada na V1.

Um provedor concreto (configurável) pode ser plugado no futuro sem alterar o restante do sistema.
"""
from __future__ import annotations

from typing import List

from ...core.models import Fonte
from .base import ResearchProvider


class WebSearchProvider(ResearchProvider):
    nome = "web"
    rotulo = "Fonte externa"

    def disponivel(self) -> bool:
        return False

    def buscar(self, consulta: str, limite: int = 5) -> List[Fonte]:
        return []
