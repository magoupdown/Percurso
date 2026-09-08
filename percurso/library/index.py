"""Índice BM25 da biblioteca com manifesto e indexação incremental (SPEC §9.5, §9.6).

indices/biblioteca_bm25.json = {manifesto: {hash_por_documento, data_indexacao, metodo, versao_indice, n_trechos},
                                 trechos: [{id, hash, pagina, texto}], tokens: [[...], ...]}
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from ..storage.atomic import escrever_json, ler_json
from ..storage.paths import Caminhos
from ..utils import dates
from . import catalog

VERSAO_INDICE = 1
METODO = "bm25"

_STOP = set(
    "a o e de da do das dos em no na nos nas um uma uns umas por para com sem que se ao aos à às ou como mais mas seu sua seus suas "
    "the of and to in is are for with on at by an as or this that from be it its".split()
)


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def tokenizar(texto: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(t) > 1 and t not in _STOP]


def ler(caminhos: Caminhos) -> Dict[str, Any]:
    dados = ler_json(caminhos.indice_bm25, None)
    if not dados or dados.get("manifesto", {}).get("versao_indice") != VERSAO_INDICE:
        return {"manifesto": {"hash_por_documento": {}, "data_indexacao": "", "metodo": METODO, "versao_indice": VERSAO_INDICE, "n_trechos": 0}, "trechos": [], "tokens": []}
    return dados


def precisa_atualizar_versao(caminhos: Caminhos) -> bool:
    dados = ler_json(caminhos.indice_bm25, None)
    return bool(dados) and dados.get("manifesto", {}).get("versao_indice") != VERSAO_INDICE


def gravar(caminhos: Caminhos, indice: Dict[str, Any]) -> None:
    escrever_json(caminhos.indice_bm25, indice)


def atualizar(caminhos: Caminhos, cat: Optional[catalog.Catalogo] = None, fuso: Optional[str] = None) -> Dict[str, Any]:
    """Indexação incremental: só documentos novos/alterados entram; removidos saem."""
    cat = cat or catalog.ler(caminhos)
    indice = ler(caminhos)
    manifesto = indice["manifesto"]
    conhecidos: Dict[str, str] = dict(manifesto.get("hash_por_documento", {}))
    atuais = {d.hash: d.hash for d in cat.indexaveis()}
    mudou = False

    # remover documentos que saíram
    removidos = [h for h in conhecidos if h not in atuais]
    if removidos:
        pares = [(t, tok) for t, tok in zip(indice["trechos"], indice["tokens"]) if t["hash"] not in removidos]
        indice["trechos"] = [p[0] for p in pares]
        indice["tokens"] = [p[1] for p in pares]
        for h in removidos:
            conhecidos.pop(h, None)
        mudou = True

    # adicionar novos
    for h in atuais:
        if h in conhecidos:
            continue
        for i, tr in enumerate(catalog.ler_trechos(caminhos, h)):
            indice["trechos"].append({"id": f"{h[:12]}-{i:04d}", "hash": h, "pagina": tr.get("pagina"), "texto": tr.get("texto", "")})
            indice["tokens"].append(tokenizar(tr.get("texto", "")))
        conhecidos[h] = h
        mudou = True

    if mudou or not manifesto.get("data_indexacao"):
        manifesto.update({"hash_por_documento": conhecidos, "data_indexacao": dates.iso_agora(fuso), "metodo": METODO, "versao_indice": VERSAO_INDICE, "n_trechos": len(indice["trechos"])})
        indice["manifesto"] = manifesto
        gravar(caminhos, indice)
    return indice


def remover_documento(caminhos: Caminhos, sha: str) -> int:
    indice = ler(caminhos)
    antes = len(indice["trechos"])
    pares = [(t, tok) for t, tok in zip(indice["trechos"], indice["tokens"]) if t["hash"] != sha]
    indice["trechos"] = [p[0] for p in pares]
    indice["tokens"] = [p[1] for p in pares]
    indice["manifesto"].get("hash_por_documento", {}).pop(sha, None)
    indice["manifesto"]["n_trechos"] = len(indice["trechos"])
    gravar(caminhos, indice)
    return antes - len(indice["trechos"])
