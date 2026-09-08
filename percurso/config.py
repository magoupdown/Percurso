"""Leitura de config/defaults.json e config/gemini.json (raiz do repositório)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CONFIG = RAIZ / "config"


def _ler(nome: str) -> Dict[str, Any]:
    caminho = PASTA_CONFIG / nome
    if not caminho.exists():
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def defaults() -> Dict[str, Any]:
    return _ler("defaults.json")


@lru_cache(maxsize=1)
def gemini() -> Dict[str, Any]:
    return _ler("gemini.json")


def template_cronograma(chave: str) -> list:
    t = defaults().get("templates_cronograma", {})
    return t.get(chave) or t.get("individual") or []


def link_apoio() -> str:
    return defaults().get("apoio", {}).get("link_mercado_pago", "")


def recarregar() -> None:
    defaults.cache_clear()
    gemini.cache_clear()
