"""Provedores de pesquisa acadêmica (SPEC §11.2)."""
from __future__ import annotations

from typing import List, Optional

from .base import ResearchProvider  # noqa: F401
from .crossref import CrossrefProvider
from .googlebooks import GoogleBooksProvider
from .openalex import OpenAlexProvider
from .semanticscholar import SemanticScholarProvider
from .websearch import WebSearchProvider  # noqa: F401


def provedores_padrao(mailto: str = "", chave_semantic_scholar: Optional[str] = None, http=None) -> List[ResearchProvider]:
    """Obrigatórios: OpenAlex, Crossref, Google Books. Opcional: Semantic Scholar (com ou sem chave)."""
    return [
        OpenAlexProvider(mailto=mailto, http=http),
        CrossrefProvider(mailto=mailto, http=http),
        GoogleBooksProvider(http=http),
        SemanticScholarProvider(chave=chave_semantic_scholar, http=http),
    ]
