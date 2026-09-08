"""Crossref (obrigatório; sem chave; DOI/metadados/periódicos)."""
from __future__ import annotations

from typing import List

from ...core.models import Fonte
from .base import ResearchProvider, juntar_autores

URL = "https://api.crossref.org/works"


class CrossrefProvider(ResearchProvider):
    nome = "crossref"
    rotulo = "Crossref"

    def __init__(self, mailto: str = "", http=None):
        super().__init__(http)
        self.mailto = mailto

    def buscar(self, consulta: str, limite: int = 5) -> List[Fonte]:
        params = {"query": consulta, "rows": limite, "select": "DOI,title,author,issued,container-title,URL,abstract"}
        if self.mailto:
            params["mailto"] = self.mailto
        dados = self.http.get_json(URL, params=params)
        saida = []
        for it in (dados.get("message") or {}).get("items", []) or []:
            titulo = (it.get("title") or [""])[0]
            autores = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", []) or []]
            ano = None
            partes = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
            if partes and partes[0]:
                ano = partes[0]
            periodico = (it.get("container-title") or [""])[0]
            saida.append(
                self._fonte(
                    titulo=titulo,
                    autor=juntar_autores(autores),
                    ano=ano,
                    doi=it.get("DOI") or "",
                    url=it.get("URL") or "",
                    fonte=f"Crossref · {periodico}".strip(" ·"),
                    trecho=_limpar_abstract(it.get("abstract") or ""),
                )
            )
        return saida


def _limpar_abstract(t: str) -> str:
    import re

    return re.sub(r"<[^>]+>", " ", t).strip()[:600]
