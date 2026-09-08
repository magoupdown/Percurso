"""Consulta à base curricular: listar por etapa/unidade, sugerir habilidades para um tema, converter em Fonte (🏛)."""
from __future__ import annotations

import re
import unicodedata
from typing import List, Optional

from ..core.models import Fonte, Registro
from ..utils import dates
from . import bncc, validate

PALAVRAS_TEMA = {
    "pulsacao": ["ritmo", "elementos constitutivos", "jogos", "brincadeiras", "percussão corporal", "sons"],
    "pulso": ["ritmo", "elementos constitutivos", "brincadeiras"],
    "ritmo": ["ritmo", "elementos constitutivos", "jogos"],
    "leitura": ["notação", "registro musical", "partituras"],
    "notacao": ["notação", "registro musical"],
    "percepcao": ["altura", "timbre", "intensidade", "elementos constitutivos", "qualidades do som", "apreciação"],
    "improvisacao": ["improvisações", "composições", "criação"],
    "composicao": ["composições", "criação", "arranjos"],
    "repertorio": ["gêneros", "apreciação", "estilos musicais", "canções"],
    "instrumento": ["fontes sonoras", "instrumentos musicais", "materiais sonoros"],
    "fontes sonoras": ["fontes sonoras", "objetos cotidianos"],
    "canto": ["vozes", "canções", "brincadeiras cantadas"],
    "tecnologia": ["tecnologia", "áudio", "audiovisual", "equipamentos"],
    "historia": ["contextos", "funções da música", "músicos e grupos", "estilos musicais"],
    "apreciacao": ["apreciar", "apreciação", "gêneros"],
}


def _norm(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


def listar(registro: Optional[Registro] = None, apenas_musica: bool = True, etapa: Optional[str] = None) -> List[bncc.Habilidade]:
    base = validate.base_para(registro)
    etapa = etapa or validate.etapa_do_registro(registro)
    saida = []
    for h in base.values():
        if apenas_musica and not h.musica:
            continue
        if etapa and h.etapa != etapa:
            continue
        if registro is not None and not validate.anos_compativeis(h, registro):
            continue
        saida.append(h)
    return sorted(saida, key=lambda h: h.codigo)


def sugerir_para_tema(tema: str, registro: Optional[Registro] = None, limite: int = 3) -> List[bncc.Habilidade]:
    """Habilidades de Música cuja descrição mais se relaciona ao tema (busca lexical simples, sem IA)."""
    cands = listar(registro, apenas_musica=True)
    if not cands:
        return []
    tn = _norm(tema)
    termos = set(re.findall(r"[a-z]{4,}", tn))
    for chave, extras in PALAVRAS_TEMA.items():
        if chave in tn:
            termos |= {w for e in extras for w in re.findall(r"[a-z]{4,}", _norm(e))}
    pontuados = []
    for h in cands:
        ht = _norm(h.texto + " " + h.unidade_tematica + " " + h.objeto)
        p = sum(1 for t in termos if t in ht)
        if h.unidade_tematica == "Música" or h.unidade_tematica.startswith("Traços"):
            p += 0.5
        if p > 0.5:
            pontuados.append((p, h))
    pontuados.sort(key=lambda x: (-x[0], x[1].codigo))
    return [h for _, h in pontuados[:limite]]


def como_fonte(h: bncc.Habilidade, fuso: Optional[str] = None) -> Fonte:
    base = bncc.bncc_arte() if h.etapa != "EI" else bncc.bncc_infantil()
    if getattr(h, "documento", "BNCC") == "CRMG":
        from . import crmg

        base = crmg.crmg_arte()
    return Fonte(
        titulo=f"{h.codigo} — {h.texto}",
        autor=base.fonte_oficial,
        ano=base.data_obtencao[:4] if base.data_obtencao else None,
        fonte=base.documento,
        url=base.url,
        data_consulta=dates.iso_agora(fuso),
        tipo="curricular",
        id_origem=f"hab:{h.codigo}",
    )


def descrever(h: bncc.Habilidade) -> str:
    anos = ", ".join(h.anos)
    return f"**{h.codigo}** ({h.etapa} {anos} · {h.unidade_tematica}{' · ' + h.objeto if h.objeto else ''}): {h.texto}"
