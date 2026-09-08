"""Busca semântica (SPEC D5, §9.5).

- Gemini: índice `indices/biblioteca_emb_gemini.json`, incremental, só no Modo Inteligente.
- Local (opt-in explícito): `sentence-transformers` (multilingual-e5-small) instalado só se o professor pedir na sessão;
  índice `indices/biblioteca_emb_local.json`; fallback automático para BM25 se não carregar.
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..storage.atomic import escrever_json, ler_json
from ..storage.paths import Caminhos
from ..utils import dates
from ..utils.logging import obter
from . import catalog, index
from .search import Resultado

log = obter("embeddings")
LOTE = 32
MODELO_LOCAL = "intfloat/multilingual-e5-small"
_modelo_local = None


def _caminho(caminhos: Caminhos, metodo: str) -> Path:
    return caminhos.indice_emb_gemini if metodo == "gemini" else caminhos.indice_emb_local


def ler(caminhos: Caminhos, metodo: str) -> Dict[str, Any]:
    dados = ler_json(_caminho(caminhos, metodo), None)
    if not dados:
        return {"manifesto": {"hash_por_documento": {}, "data_indexacao": "", "metodo": metodo, "modelo": "", "versao_indice": 1, "n_trechos": 0}, "itens": []}
    return dados


def atualizar(caminhos: Caminhos, metodo: str, embutir: Callable[[List[str]], List[List[float]]], nome_modelo: str, fuso: Optional[str] = None, progresso: Callable[[str], None] = lambda m: None) -> Dict[str, Any]:
    """Indexação incremental por documento. `embutir(textos)` devolve vetores."""
    cat = catalog.ler(caminhos)
    idx = ler(caminhos, metodo)
    man = idx["manifesto"]
    conhecidos = dict(man.get("hash_por_documento", {}))
    if man.get("modelo") and man["modelo"] != nome_modelo:
        # modelo mudou → índice precisa ser refeito
        idx["itens"] = []
        conhecidos = {}
    atuais = {d.hash for d in cat.indexaveis()}
    removidos = [h for h in conhecidos if h not in atuais]
    if removidos:
        idx["itens"] = [it for it in idx["itens"] if it["hash"] not in removidos]
        for h in removidos:
            conhecidos.pop(h, None)
    novos = [h for h in atuais if h not in conhecidos]
    for h in novos:
        trechos = catalog.ler_trechos(caminhos, h)
        progresso(f"Indexando {cat.por_hash(h).titulo if cat.por_hash(h) else h[:8]} ({len(trechos)} trechos)…")
        for i in range(0, len(trechos), LOTE):
            lote = trechos[i: i + LOTE]
            vetores = embutir([t["texto"] for t in lote])
            for t, v in zip(lote, vetores):
                idx["itens"].append({"id": t["id"], "hash": h, "pagina": t.get("pagina"), "vetor": [round(x, 6) for x in v]})
        conhecidos[h] = h
    if novos or removidos or not man.get("data_indexacao"):
        man.update({"hash_por_documento": conhecidos, "data_indexacao": dates.iso_agora(fuso), "metodo": metodo, "modelo": nome_modelo, "versao_indice": 1, "n_trechos": len(idx["itens"])})
        idx["manifesto"] = man
        escrever_json(_caminho(caminhos, metodo), idx)
    return idx


def remover_documento(caminhos: Caminhos, sha: str) -> int:
    total = 0
    for metodo in ("gemini", "local"):
        p = _caminho(caminhos, metodo)
        if not p.exists():
            continue
        idx = ler(caminhos, metodo)
        antes = len(idx["itens"])
        idx["itens"] = [it for it in idx["itens"] if it["hash"] != sha]
        idx["manifesto"].get("hash_por_documento", {}).pop(sha, None)
        idx["manifesto"]["n_trechos"] = len(idx["itens"])
        escrever_json(p, idx)
        total += antes - len(idx["itens"])
    return total


def _cos(a: List[float], b: List[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (na * nb)


def buscar(caminhos: Caminhos, metodo: str, embutir: Callable[[List[str]], List[List[float]]], consulta: str, limite: int = 8) -> List[Resultado]:
    idx = ler(caminhos, metodo)
    if not idx["itens"]:
        return []
    q = embutir([consulta])[0]
    pont = [(_cos(q, it["vetor"]), it) for it in idx["itens"]]
    pont.sort(key=lambda p: -p[0])
    cat = catalog.ler(caminhos)
    texto_por_id = {t["id"]: t["texto"] for t in index.ler(caminhos)["trechos"]}
    saida = []
    for s, it in pont[:limite]:
        if s <= 0:
            break
        d = cat.por_hash(it["hash"])
        saida.append(Resultado(it["hash"], (d.titulo or d.nome_original) if d else "(removido)", d.autor if d else "", d.ano if d else "", it.get("pagina"), texto_por_id.get(it["id"], "")[:420], float(round(s, 4)), "semantica", it["id"]))
    return saida


# --------------------------------------------------------------- Gemini
def embutir_gemini(cliente) -> Callable[[List[str]], List[List[float]]]:
    return lambda textos: cliente.embeddings(textos)


# ------------------------------------------------------------ local (opt-in)
def local_disponivel() -> bool:
    try:
        import sentence_transformers  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def instalar_local(progresso: Callable[[str], None] = lambda m: None) -> bool:
    """Instala sentence-transformers apenas a pedido explícito do professor (D5)."""
    if local_disponivel():
        return True
    progresso("Instalando busca semântica local (pode levar alguns minutos)…")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"], check=True, timeout=900)
    except Exception as e:  # noqa: BLE001
        log.warning("instalação local falhou: %s", e)
        return False
    return local_disponivel()


def embutir_local() -> Optional[Callable[[List[str]], List[List[float]]]]:
    global _modelo_local
    try:
        if _modelo_local is None:
            from sentence_transformers import SentenceTransformer  # type: ignore

            _modelo_local = SentenceTransformer(MODELO_LOCAL)
        modelo = _modelo_local
        return lambda textos: [list(map(float, v)) for v in modelo.encode(["passage: " + t for t in textos], normalize_embeddings=True)]
    except Exception as e:  # noqa: BLE001
        log.warning("modelo local indisponível: %s", e)
        return None
