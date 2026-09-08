"""OpenAlex (obrigatório; sem chave; polite pool via mailto)."""
from __future__ import annotations

from typing import List

from ...core.models import Fonte
from .base import ResearchProvider, juntar_autores

URL = "https://api.openalex.org/works"


class OpenAlexProvider(ResearchProvider):
    nome = "openalex"
    rotulo = "OpenAlex"

    def __init__(self, mailto: str = "", http=None):
        super().__init__(http)
        self.mailto = mailto

    def buscar(self, consulta: str, limite: int = 5) -> List[Fonte]:
        params = {"search": consulta, "per-page": limite, "select": "id,title,display_name,publication_year,doi,authorships,primary_location,abstract_inverted_index"}
        if self.mailto:
            params["mailto"] = self.mailto
        dados = self.http.get_json(URL, params=params)
        saida = []
        for w in dados.get("results", []) or []:
            autores = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", []) or []]
            loc = (w.get("primary_location") or {}).get("source") or {}
            resumo = _reconstruir_resumo(w.get("abstract_inverted_index"))
            saida.append(
                self._fonte(
                    titulo=w.get("display_name") or w.get("title") or "",
                    autor=juntar_autores(autores),
                    ano=w.get("publication_year"),
                    doi=w.get("doi") or "",
                    url=(w.get("doi") or w.get("id") or ""),
                    fonte=f"OpenAlex · {loc.get('display_name', '')}".strip(" ·"),
                    trecho=resumo,
                    id_origem=f"doi:{(w.get('doi') or '').replace('https://doi.org/', '').lower()}" if w.get("doi") else f"openalex:{(w.get('id') or '').rsplit('/', 1)[-1]}",
                )
            )
        return saida


def _reconstruir_resumo(inv) -> str:
    if not inv:
        return ""
    posicoes = []
    for palavra, idxs in inv.items():
        for i in idxs:
            posicoes.append((i, palavra))
    posicoes.sort()
    return " ".join(p for _, p in posicoes)[:600]
