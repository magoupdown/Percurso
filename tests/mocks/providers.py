"""Cliente HTTP falso para os provedores (SPEC §16.1): respostas gravadas em fixtures/providers/*.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from percurso.research.providers.base import ErroProvedor

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "providers"


def _carregar(nome: str) -> Any:
    return json.loads((FIXTURES / f"{nome}.json").read_text(encoding="utf-8"))


class HTTPFalso:
    """Mapeia trecho da URL → fixture. `fora_do_ar` faz o provedor falhar (ErroProvedor)."""

    def __init__(self, fora_do_ar: Optional[set] = None):
        self.fora_do_ar = fora_do_ar or set()
        self.chamadas: list = []

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        self.chamadas.append((url, dict(params or {})))
        for nome, trecho in [("openalex", "openalex.org"), ("crossref", "crossref.org"), ("googlebooks", "googleapis.com/books"), ("semanticscholar", "semanticscholar.org")]:
            if trecho in url:
                if nome in self.fora_do_ar:
                    raise ErroProvedor(f"{nome} indisponível (simulado)")
                return _carregar(nome)
        raise ErroProvedor(f"URL desconhecida no mock: {url}")
