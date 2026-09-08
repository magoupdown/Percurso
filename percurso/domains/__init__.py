"""Registro de adaptadores de domínio. O núcleo chama `obter_adaptador(dominio)`."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .base import DomainAdapter

_cache: Dict[str, DomainAdapter] = {}


def obter_adaptador(dominio: str = "musica", pasta_perfis_editados: Optional[Path] = None) -> DomainAdapter:
    chave = f"{dominio}|{pasta_perfis_editados}"
    if chave in _cache:
        return _cache[chave]
    if dominio == "musica":
        from .music.adapter import MusicAdapter

        adaptador: DomainAdapter = MusicAdapter(pasta_perfis_editados=pasta_perfis_editados)
    else:
        raise ValueError(f"Domínio desconhecido: {dominio}")
    _cache[chave] = adaptador
    return adaptador


def limpar_cache() -> None:
    _cache.clear()
