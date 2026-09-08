"""Cache de pesquisas em pesquisas/cache/<hash>.json (SPEC §11.4).

Chave = hash(consulta normalizada + provedores). Validade acadêmica: 90 dias (a entrada antiga permanece e
é usada como fallback se a rede falhar).
"""
from __future__ import annotations

import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .. import config
from ..core.models import Fonte
from ..storage.atomic import escrever_json, ler_json
from ..storage.paths import Caminhos
from ..utils import dates
from ..utils.hashing import hash_estrutura


def normalizar_consulta(q: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", (q or "").lower()) if unicodedata.category(c) != "Mn")
    return " ".join(t.split())


def chave(consulta: str, provedores: List[str]) -> str:
    return hash_estrutura({"q": normalizar_consulta(consulta), "p": sorted(provedores)})[:32]


def ler(caminhos: Caminhos, consulta: str, provedores: List[str]) -> Optional[Dict[str, Any]]:
    return ler_json(caminhos.pesquisa_cache(chave(consulta, provedores)), None)


def valido(entrada: Dict[str, Any], dias: Optional[int] = None) -> bool:
    dias = int(dias or config.defaults().get("pesquisa", {}).get("validade_cache_dias", 90))
    try:
        data = datetime.fromisoformat(entrada.get("data", ""))
    except ValueError:
        return False
    agora = dates.agora()
    if data.tzinfo is None:
        data = data.replace(tzinfo=agora.tzinfo)
    return agora - data <= timedelta(days=dias)


def gravar(caminhos: Caminhos, consulta: str, provedores: List[str], resultados: List[Fonte], fuso: Optional[str] = None) -> None:
    escrever_json(
        caminhos.pesquisa_cache(chave(consulta, provedores)),
        {"consulta": consulta, "consulta_normalizada": normalizar_consulta(consulta), "provedores": sorted(provedores), "data": dates.iso_agora(fuso), "resultados": [f.model_dump(mode="json") for f in resultados]},
    )


def fontes_de(entrada: Dict[str, Any]) -> List[Fonte]:
    return [Fonte.model_validate(f) for f in entrada.get("resultados", [])]
