"""Hashes determinísticos usados na biblioteca, no cache de pesquisas e em ids."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_arquivo(caminho: Path, bloco: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            parte = f.read(bloco)
            if not parte:
                break
            h.update(parte)
    return h.hexdigest()


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_estrutura(obj: Any) -> str:
    """Hash estável de uma estrutura JSON-serializável (usado para cache por hash(prompt))."""
    return sha256_texto(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str))


def id_curto(texto: str, tamanho: int = 4) -> str:
    return sha256_texto(texto)[:tamanho]
