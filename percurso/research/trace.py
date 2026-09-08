"""Rastreabilidade (SPEC §11.5): toda fonte apresentada carrega origem verificável.

Uma referência só entra num plano se estiver em `fontes_utilizadas` com origem verificável:
cache de pesquisa (academica), catálogo/índice (biblioteca) ou base curricular (curricular).
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from ..core.models import Fonte
from ..ui import texts as T


def marcar(fonte: Fonte) -> str:
    return T.ORIGENS_FONTE.get(fonte.tipo, "")


def formatar(fonte: Fonte) -> str:
    partes = [fonte.titulo]
    if fonte.autor:
        partes.append(fonte.autor)
    if fonte.ano:
        partes.append(str(fonte.ano))
    if fonte.fonte:
        partes.append(fonte.fonte)
    if fonte.pagina:
        partes.append(f"p. {fonte.pagina}")
    if fonte.doi:
        partes.append(f"DOI {fonte.doi}")
    elif fonte.url:
        partes.append(fonte.url)
    if fonte.data_consulta:
        partes.append(f"consultado em {fonte.data_consulta[:10]}")
    return f"{marcar(fonte)} " + " · ".join(partes)


def formatar_lista(fontes: Iterable[Fonte]) -> str:
    fontes = list(fontes)
    if not fontes:
        return "_Nenhuma fonte._"
    return "\n".join(f"- {formatar(f)}" for f in fontes)


def verificar_origem(fonte: Fonte, permitidas: Iterable[str]) -> Tuple[bool, str]:
    """Aceita apenas fontes cujo id_origem esteja no conjunto verificável da sessão/plano."""
    ids = set(permitidas)
    if not fonte.id_origem:
        return False, "fonte sem identificador de origem"
    if fonte.id_origem not in ids:
        return False, "fonte não consta do conjunto verificado"
    return True, ""


def filtrar_verificadas(fontes: Iterable[Fonte], permitidas: Iterable[str]) -> Tuple[List[Fonte], List[Fonte]]:
    ok, rejeitadas = [], []
    ids = set(permitidas)
    for f in fontes:
        (ok if verificar_origem(f, ids)[0] else rejeitadas).append(f)
    return ok, rejeitadas
