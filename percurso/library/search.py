"""Busca na biblioteca (SPEC §9.5): textual exata, BM25 com expansão de sinônimos, semântica opcional.

Resultado sempre traz documento, página, trecho e origem 📚.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.models import Fonte
from ..storage.paths import Caminhos
from ..utils import dates
from . import catalog, index


@dataclass
class Resultado:
    hash: str
    titulo: str
    autor: str
    ano: str
    pagina: Optional[int]
    trecho: str
    pontuacao: float
    metodo: str  # exata | bm25 | semantica
    id_trecho: str

    def como_fonte(self, fuso: Optional[str] = None) -> Fonte:
        return Fonte(
            titulo=self.titulo,
            autor=self.autor,
            ano=self.ano or None,
            fonte="Minha Biblioteca",
            pagina=str(self.pagina) if self.pagina else None,
            data_consulta=dates.iso_agora(fuso),
            tipo="biblioteca",
            trecho=self.trecho,
            id_origem=self.id_trecho,
        )


def expandir(consulta: str, sinonimos: Dict[str, List[str]]) -> List[str]:
    """'desenvolvimento da pulsação' → termos + sinônimos PT/EN vindos do adaptador."""
    base = index.tokenizar(consulta)
    extras: List[str] = []
    cn = index.normalizar(consulta)
    for chave, lista in sinonimos.items():
        kn = index.normalizar(chave)
        if kn in cn or any(kn == t or (len(t) > 4 and t.startswith(kn[:5])) for t in base):
            for s in lista:
                extras.extend(index.tokenizar(s))
    vistos = set()
    saida = []
    for t in base + extras:
        if t not in vistos:
            vistos.add(t)
            saida.append(t)
    return saida


def _meta(cat: catalog.Catalogo, sha: str):
    d = cat.por_hash(sha)
    if d is None:
        return ("(documento removido)", "", "")
    return (d.titulo or d.nome_original, d.autor, d.ano)


def buscar_exata(caminhos: Caminhos, consulta: str, limite: int = 20, cat: Optional[catalog.Catalogo] = None) -> List[Resultado]:
    cat = cat or catalog.ler(caminhos)
    idx = index.ler(caminhos)
    alvo = index.normalizar(consulta.strip())
    if not alvo:
        return []
    saida: List[Resultado] = []
    for t in idx["trechos"]:
        tn = index.normalizar(t["texto"])
        pos = tn.find(alvo)
        if pos >= 0:
            titulo, autor, ano = _meta(cat, t["hash"])
            ini = max(0, pos - 150)
            saida.append(Resultado(t["hash"], titulo, autor, ano, t.get("pagina"), t["texto"][ini: pos + len(alvo) + 200].strip(), 1.0, "exata", t["id"]))
            if len(saida) >= limite:
                break
    return saida


def buscar_bm25(caminhos: Caminhos, consulta: str, sinonimos: Dict[str, List[str]], limite: int = 10, cat: Optional[catalog.Catalogo] = None) -> List[Resultado]:
    cat = cat or catalog.ler(caminhos)
    idx = index.ler(caminhos)
    if not idx["tokens"]:
        return []
    termos = expandir(consulta, sinonimos)
    if not termos:
        return []
    from rank_bm25 import BM25Okapi

    bm = BM25Okapi(idx["tokens"])
    pont = bm.get_scores(termos)
    conjunto = set(termos)
    # com poucos documentos o IDF do BM25 fica negativo; por isso o critério de inclusão é
    # "ao menos um termo presente" e a pontuação apenas ordena (sobreposição desempata em corpora pequenos)
    sobreposicao = [len(conjunto & set(toks)) for toks in idx["tokens"]]
    poucos = len(idx["tokens"]) < 3
    ordem = sorted((i for i in range(len(pont)) if sobreposicao[i] > 0), key=lambda i: (-sobreposicao[i] if poucos else 0, -pont[i]))
    saida: List[Resultado] = []
    for i in ordem[: limite * 2]:
        t = idx["trechos"][i]
        titulo, autor, ano = _meta(cat, t["hash"])
        saida.append(Resultado(t["hash"], titulo, autor, ano, t.get("pagina"), _janela(t["texto"], termos), float(round(pont[i], 3)), "bm25", t["id"]))
        if len(saida) >= limite:
            break
    return saida


def _janela(texto: str, termos: List[str], tamanho: int = 420) -> str:
    tn = index.normalizar(texto)
    pos = min((tn.find(t) for t in termos if tn.find(t) >= 0), default=0)
    ini = max(0, pos - tamanho // 3)
    return texto[ini: ini + tamanho].strip()


def buscar(caminhos: Caminhos, consulta: str, sinonimos: Dict[str, List[str]], limite: int = 10, semantica=None) -> List[Resultado]:
    """Combina exata (primeiro) + BM25 (+ semântica se fornecida), deduplicando por trecho."""
    cat = catalog.ler(caminhos)
    vistos = set()
    saida: List[Resultado] = []
    for r in buscar_exata(caminhos, consulta, limite, cat) + buscar_bm25(caminhos, consulta, sinonimos, limite, cat):
        if r.id_trecho not in vistos:
            vistos.add(r.id_trecho)
            saida.append(r)
    if semantica is not None:
        try:
            for r in semantica(consulta, limite):
                if r.id_trecho not in vistos:
                    vistos.add(r.id_trecho)
                    saida.append(r)
        except Exception:  # noqa: BLE001 — a pesquisa nunca para (D5)
            pass
    return saida[: limite * 2]


def formatar(resultados: List[Resultado]) -> str:
    if not resultados:
        return "_Nenhum trecho encontrado na sua biblioteca._"
    L = []
    for r in resultados:
        pag = f" · p. {r.pagina}" if r.pagina else ""
        L.append(f"**📚 {r.titulo}**{(' · ' + r.autor) if r.autor else ''}{(' · ' + r.ano) if r.ano else ''}{pag} _( {r.metodo} )_\n\n> {re.sub(r'\\s+', ' ', r.trecho)}")
    return "\n\n".join(L)
