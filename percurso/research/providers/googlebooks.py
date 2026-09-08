"""Google Books (obrigatório; sem chave; livros/ISBN/assuntos)."""
from __future__ import annotations

from typing import List

from ...core.models import Fonte
from .base import ResearchProvider, juntar_autores

URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksProvider(ResearchProvider):
    nome = "googlebooks"
    rotulo = "Google Books"

    def buscar(self, consulta: str, limite: int = 5) -> List[Fonte]:
        dados = self.http.get_json(URL, params={"q": consulta, "maxResults": limite, "printType": "books"})
        saida = []
        for it in dados.get("items", []) or []:
            v = it.get("volumeInfo") or {}
            isbn = ""
            for ident in v.get("industryIdentifiers", []) or []:
                if ident.get("type") in ("ISBN_13", "ISBN_10"):
                    isbn = ident.get("identifier", "")
                    break
            saida.append(
                self._fonte(
                    titulo=v.get("title", "") + (f": {v.get('subtitle')}" if v.get("subtitle") else ""),
                    autor=juntar_autores(v.get("authors", []) or []),
                    ano=(v.get("publishedDate") or "")[:4] or None,
                    url=v.get("infoLink") or v.get("canonicalVolumeLink") or "",
                    fonte=f"Google Books · {v.get('publisher', '')}".strip(" ·") + (f" · ISBN {isbn}" if isbn else ""),
                    trecho=(v.get("description") or "")[:600],
                    id_origem=f"isbn:{isbn}" if isbn else f"googlebooks:{it.get('id', '')}",
                )
            )
        return saida
