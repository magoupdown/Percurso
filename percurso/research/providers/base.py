"""Contrato dos provedores (SPEC §11.2): buscar(consulta) -> [Fonte]; disponivel() -> bool.

Rede via httpx com timeout (15 s) e retry com backoff (tenacity, máximo 3). Falha de um provedor nunca
derruba a pesquisa: quem chama trata `ErroProvedor`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ... import config
from ...core.models import Fonte
from ...utils import dates
from ...utils.logging import obter

log = obter("pesquisa")


class ErroProvedor(Exception):
    pass


class ClienteHTTP:
    """Cliente httpx mínimo e substituível nos testes (tests/mocks/providers.py)."""

    def __init__(self, timeout_s: Optional[float] = None, user_agent: str = "Percurso/1.0 (plataforma pedagógica; gratuita)"):
        self.timeout_s = float(timeout_s or config.defaults().get("pesquisa", {}).get("timeout_s", 15))
        self.user_agent = user_agent

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        import httpx
        from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

        max_tent = int(config.defaults().get("pesquisa", {}).get("max_tentativas", 3))

        @retry(stop=stop_after_attempt(max_tent), wait=wait_exponential(multiplier=0.5, min=0.5, max=4), retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)), reraise=True)
        def _get():
            h = {"User-Agent": self.user_agent, "Accept": "application/json"}
            if headers:
                h.update(headers)
            r = httpx.get(url, params=params, headers=h, timeout=self.timeout_s, follow_redirects=True)
            if r.status_code == 429 or r.status_code >= 500:
                raise httpx.TransportError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r.json()

        try:
            return _get()
        except Exception as e:  # noqa: BLE001
            raise ErroProvedor(f"{e.__class__.__name__}: {str(e)[:120]}") from e


class ResearchProvider(ABC):
    nome: str = "base"
    rotulo: str = "Provedor"

    def __init__(self, http: Optional[ClienteHTTP] = None):
        self.http = http or ClienteHTTP()

    @abstractmethod
    def buscar(self, consulta: str, limite: int = 5) -> List[Fonte]:
        ...

    def disponivel(self) -> bool:
        return True

    # ------------------------------------------------------------ util
    def _fonte(self, titulo: str, autor: str = "", ano: Any = None, url: str = "", doi: str = "", fonte: str = "", trecho: str = "", id_origem: str = "") -> Fonte:
        doi = (doi or "").replace("https://doi.org/", "").strip()
        ident = id_origem or (f"doi:{doi.lower()}" if doi else f"{self.nome}:{_slug(titulo)}")
        return Fonte(
            titulo=(titulo or "").strip() or "(sem título)",
            autor=(autor or "").strip(),
            ano=str(ano) if ano else None,
            fonte=fonte or self.rotulo,
            url=url or (f"https://doi.org/{doi}" if doi else ""),
            doi=doi,
            data_consulta=dates.iso_agora(),
            tipo="academica",
            trecho=(trecho or "")[:600],
            id_origem=ident,
        )


def _slug(t: str) -> str:
    import re
    import unicodedata

    t = "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:80]


def juntar_autores(lista: List[str], maximo: int = 3) -> str:
    lista = [a for a in lista if a]
    if not lista:
        return ""
    if len(lista) > maximo:
        return ", ".join(lista[:maximo]) + " et al."
    return ", ".join(lista)
