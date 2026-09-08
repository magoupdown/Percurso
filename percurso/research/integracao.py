"""'Onde pesquisar?' integrado ao planejamento (SPEC §11.1, §11.5).

Devolve {referencias: [Fonte], consultas: [str], habilidades: [str]} — só fontes com origem verificável.
Cada camada falha de forma isolada; a pesquisa nunca para o planejamento.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..core.models import Fonte
from ..library import search
from ..utils.logging import obter

log = obter("pesquisa")
MAX_BIBLIOTECA = 6
MAX_ACADEMICA = 6


def pesquisar_para_plano(sessao, tema: str, onde: List[str]) -> Dict[str, Any]:
    ctx = sessao.contexto
    reg = ctx.registro if ctx else None
    adaptador = sessao.adaptador(reg.dominio if reg else "musica")
    tema = (tema or "").strip()
    if not tema and ctx is not None:
        from ..core import planner

        try:
            tema = planner.sugerir_proximo_passo(sessao.entrada_planejamento()).conteudo
        except Exception:  # noqa: BLE001
            tema = ""
    saida: Dict[str, Any] = {"referencias": [], "consultas": [], "habilidades": []}
    if not tema:
        return saida
    instrumento = reg.instrumento if reg else "outro"
    nivel = reg.nivel if reg else "iniciante"
    consultas = adaptador.expandir_consulta(tema, instrumento, nivel)
    saida["consultas"] = consultas

    if "biblioteca" in onde:
        try:
            sin = adaptador.sinonimos_pedagogicos()
            res = search.buscar(sessao.repo.caminhos, tema, sin, limite=MAX_BIBLIOTECA)
            saida["referencias"].extend(r.como_fonte(sessao.fuso) for r in res[:MAX_BIBLIOTECA])
        except Exception as e:  # noqa: BLE001
            log.warning("biblioteca indisponível na pesquisa: %s", e)

    if "curricular" in onde and reg is not None:
        try:
            from ..curriculum import consulta as cur

            hab = cur.sugerir_para_tema(tema, reg)
            saida["habilidades"] = [h.codigo for h in hab]
            saida["referencias"].extend(cur.como_fonte(h, sessao.fuso) for h in hab)
        except ImportError:
            pass
        except Exception as e:  # noqa: BLE001
            log.warning("base curricular indisponível: %s", e)

    if "academica" in onde:
        try:
            from . import academic

            fontes, consultas_feitas = academic.pesquisar(sessao, consultas, limite=MAX_ACADEMICA)
            saida["referencias"].extend(fontes)
            saida["consultas"] = consultas_feitas or consultas
        except ImportError:
            pass
        except Exception as e:  # noqa: BLE001
            log.warning("pesquisa acadêmica indisponível: %s", e)

    saida["referencias"] = _dedupe(saida["referencias"])
    return saida


def _dedupe(fontes: List[Fonte]) -> List[Fonte]:
    vistos = set()
    saida = []
    for f in fontes:
        chave = f.id_origem or (f.doi.lower() if f.doi else f.titulo.strip().lower())
        if chave and chave not in vistos:
            vistos.add(chave)
            saida.append(f)
    return saida
