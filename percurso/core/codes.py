"""Códigos de registro PCR-XXXXXX (SPEC §4.2)."""
from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Callable, Optional

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O/1/I
PREFIXO = "PCR"
TAMANHO = 6
_RE_CODIGO = re.compile(rf"^{PREFIXO}-[{ALFABETO}]{{{TAMANHO}}}$")


def gerar(existe: Optional[Callable[[str], bool]] = None, tentativas: int = 100) -> str:
    """Gera um código novo, verificando colisão via `existe(codigo)`."""
    for _ in range(tentativas):
        corpo = "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO))
        codigo = f"{PREFIXO}-{corpo}"
        if existe is None or not existe(codigo):
            return codigo
    raise RuntimeError("Não foi possível gerar um código único.")


def normalizar(texto: str) -> str:
    """Aceita 'pcr7k4m2q', 'PCR 7K4M2Q', ' pcr-7k4m2q ' → 'PCR-7K4M2Q'.

    Também corrige confusões comuns de digitação: 0→O? Não: 0/O/1/I não existem no alfabeto,
    então 0→(inválido), tratamos O/0 e I/1 como erro claro na validação.
    """
    t = re.sub(r"[\s\-_]", "", (texto or "").upper())
    if t.startswith(PREFIXO):
        t = t[len(PREFIXO):]
    return f"{PREFIXO}-{t}"


def valido(codigo: str) -> bool:
    return bool(_RE_CODIGO.match(codigo or ""))


def normalizar_e_validar(texto: str) -> str:
    codigo = normalizar(texto)
    if not valido(codigo):
        raise ValueError("Código inválido. O formato é PCR seguido de 6 letras ou números (ex.: PCR-7K4M2Q).")
    return codigo


def existe_em(pasta_registros: Path) -> Callable[[str], bool]:
    def _existe(codigo: str) -> bool:
        return (pasta_registros / codigo).exists()

    return _existe
