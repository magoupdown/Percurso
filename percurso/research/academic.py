"""Pesquisa acadêmica (SPEC §11.2–11.5): provedores em paralelo lógico, cache, deduplicação, falha isolada."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .. import config
from ..core.models import Fonte
from ..utils.logging import obter
from . import cache
from .providers import ResearchProvider, provedores_padrao
from .providers.base import ErroProvedor

log = obter("pesquisa")
MSG_INDISPONIVEL = "{nome} temporariamente indisponível. Continuando com outras fontes."


@dataclass
class ResultadoPesquisa:
    fontes: List[Fonte] = field(default_factory=list)
    consultas: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    do_cache: List[str] = field(default_factory=list)


def _norm_titulo(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def deduplicar(fontes: Sequence[Fonte]) -> List[Fonte]:
    vistos = set()
    saida = []
    for f in fontes:
        chave = f.doi.lower() if f.doi else _norm_titulo(f.titulo)
        if chave and chave not in vistos:
            vistos.add(chave)
            saida.append(f)
    return saida


def provedores_da_sessao(sessao) -> List[ResearchProvider]:
    cfg = config.defaults().get("pesquisa", {})
    mailto = cfg.get("openalex_mailto") or (sessao.repo.ler_professor().email_contato if sessao else "")
    chave_s2 = sessao.plataforma.obter_segredo("SEMANTIC_SCHOLAR_API_KEY") if sessao else None
    return provedores_padrao(mailto=mailto, chave_semantic_scholar=chave_s2)


def pesquisar_consultas(caminhos, consultas: Sequence[str], provedores: Sequence[ResearchProvider], limite: int = 6, fuso: Optional[str] = None, usar_cache: bool = True) -> ResultadoPesquisa:
    r = ResultadoPesquisa(consultas=list(consultas))
    todas: List[Fonte] = []
    nomes = [p.nome for p in provedores if p.disponivel()]
    falhas: Dict[str, str] = {}
    for consulta in consultas:
        entrada = cache.ler(caminhos, consulta, nomes) if usar_cache else None
        if entrada and cache.valido(entrada):
            todas.extend(cache.fontes_de(entrada))
            r.do_cache.append(consulta)
            continue
        colhidas: List[Fonte] = []
        for p in provedores:
            if not p.disponivel() or p.nome in falhas:
                continue
            try:
                colhidas.extend(p.buscar(consulta, limite=max(2, limite // 2)))
            except ErroProvedor as e:
                falhas[p.nome] = str(e)
                log.warning("provedor %s falhou: %s", p.nome, e)
            except Exception as e:  # noqa: BLE001
                falhas[p.nome] = e.__class__.__name__
                log.warning("provedor %s falhou: %s", p.nome, e.__class__.__name__)
        if colhidas:
            cache.gravar(caminhos, consulta, nomes, colhidas, fuso)
        elif entrada:  # rede falhou: usa cache antigo
            colhidas = cache.fontes_de(entrada)
            r.do_cache.append(consulta)
        todas.extend(colhidas)
    for nome, _ in falhas.items():
        rot = next((p.rotulo for p in provedores if p.nome == nome), nome)
        r.avisos.append(MSG_INDISPONIVEL.format(nome=rot))
    r.fontes = deduplicar(todas)[: max(limite, 1) * 2]
    return r


def pesquisar(sessao, consultas: Sequence[str], limite: int = 6) -> Tuple[List[Fonte], List[str]]:
    """Interface usada por research.integracao: (fontes, consultas_realizadas)."""
    res = pesquisar_consultas(sessao.repo.caminhos, consultas, provedores_da_sessao(sessao), limite=limite, fuso=sessao.fuso)
    if res.avisos:
        sessao.avisos_pesquisa = res.avisos  # type: ignore[attr-defined]
    return res.fontes[:limite], res.consultas
