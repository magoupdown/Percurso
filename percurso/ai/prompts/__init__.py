"""Carrega os prompts (.txt) desta pasta. Uso: prompts.carregar("plano").format(**campos)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def carregar(nome: str) -> str:
    return (PASTA / f"{nome}.txt").read_text(encoding="utf-8")


def preencher(nome: str, **campos) -> str:
    texto = carregar(nome)
    for k, v in campos.items():
        texto = texto.replace("{" + k + "}", str(v))
    return texto
