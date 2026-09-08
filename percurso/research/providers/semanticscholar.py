"""Semantic Scholar (opcional): com chave em Colab Secrets SEMANTIC_SCHOLAR_API_KEY; sem chave, respeita o limite público."""
from __future__ import annotations

import time
from typing import List, Optional

from ...core.models import Fonte
from .base import ResearchProvider, juntar_autores

URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_ultimo_acesso = 0.0
INTERVALO_PUBLICO_S = 1.1  # limite público aproximado: 1 requisição/segundo


class SemanticScholarProvider(ResearchProvider):
    nome = "semanticscholar"
    rotulo = "Semantic Scholar"

    def __init__(self, chave: Optional[str] = None, http=None):
        super().__init__(http)
        self.chave = chave

    def buscar(self, consulta: str, limite: int = 5) -> List[Fonte]:
        global _ultimo_acesso
        if not self.chave:
            espera = INTERVALO_PUBLICO_S - (time.monotonic() - _ultimo_acesso)
            if espera > 0:
                time.sleep(espera)
        headers = {"x-api-key": self.chave} if self.chave else None
        dados = self.http.get_json(URL, params={"query": consulta, "limit": limite, "fields": "title,authors,year,externalIds,url,abstract,venue"}, headers=headers)
        _ultimo_acesso = time.monotonic()
        saida = []
        for p in dados.get("data", []) or []:
            doi = ((p.get("externalIds") or {}).get("DOI")) or ""
            saida.append(
                self._fonte(
                    titulo=p.get("title", ""),
                    autor=juntar_autores([a.get("name", "") for a in p.get("authors", []) or []]),
                    ano=p.get("year"),
                    doi=doi,
                    url=p.get("url") or "",
                    fonte=f"Semantic Scholar · {p.get('venue', '')}".strip(" ·"),
                    trecho=(p.get("abstract") or "")[:600],
                    id_origem=f"doi:{doi.lower()}" if doi else f"s2:{p.get('paperId', '')}",
                )
            )
        return saida
