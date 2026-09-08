"""Contexto mínimo para o modelo (SPEC §7.6): resumo, últimas 3–5 aulas, estado, perfil, trechos.

Nunca o histórico inteiro. Tudo passa pelo Pseudonimizador antes de sair daqui.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..core import grading
from ..core.models import Aula, Registro
from ..ui import texts as T
from .anonymize import Pseudonimizador

ULTIMAS_AULAS = 5


def descrever_perfil(reg: Registro, nome_instrumento: str, ps: Pseudonimizador) -> str:
    quem = "turma" if reg.eh_turma else "aluno"
    linhas = [
        f"- {quem}: {('a turma ' if reg.eh_turma else 'o aluno ')}{reg.codigo}",
        f"- instrumento/área: {nome_instrumento}",
        f"- nível: {T.NIVEIS.get(reg.nivel, reg.nivel)} · idade: {reg.idade if reg.idade is not None else 'não informada'}",
        f"- modalidade: {T.MODALIDADES.get(reg.modalidade, reg.modalidade)} · contexto: {T.CONTEXTOS.get(reg.contexto, reg.contexto)} · currículo: {T.CURRICULOS.get(reg.curriculo, reg.curriculo)}",
    ]
    if reg.eh_turma and reg.turma:
        linhas.append(f"- turma: {reg.turma.quantidade_alunos} aluno(s), faixa etária {reg.turma.faixa_etaria or 'não informada'}")
    if reg.conhecimentos_previos:
        linhas.append("- conhecimentos prévios: " + "; ".join(reg.conhecimentos_previos))
    if reg.objetivos:
        linhas.append("- objetivos do registro: " + "; ".join(reg.objetivos))
    if reg.metodologias:
        linhas.append("- metodologias: " + ", ".join(T.METODOLOGIAS.get(m, m) for m in reg.metodologias))
    if reg.adaptacoes:
        linhas.append(f"- adaptações (texto do professor): {ps.aplicar(reg.adaptacoes)}")
    return "\n".join(ps.aplicar(l) for l in linhas)


def descrever_estado(estado: Dict[str, Any], ps: Pseudonimizador) -> str:
    campos = [
        ("total de aulas", estado.get("total_aulas")),
        ("última aula", estado.get("ultima_aula")),
        ("unidade atual", estado.get("unidade_atual")),
        ("consolidado", "; ".join(estado.get("conteudos_consolidados", []))),
        ("em desenvolvimento", "; ".join(estado.get("em_desenvolvimento", []))),
        ("dificuldades recorrentes", "; ".join(estado.get("dificuldades_recorrentes", []))),
        ("dificuldades recentes", "; ".join(estado.get("dificuldades_recentes", []))),
        ("próximo objetivo", estado.get("proximo_objetivo")),
        ("última observação", estado.get("ultima_observacao")),
        ("rendimento recente", ", ".join(f"{grading.rotulo(k)} {v}" for k, v in (estado.get("rendimento_recente") or {}).items())),
    ]
    return "\n".join(f"- {k}: {ps.aplicar(str(v))}" for k, v in campos if v not in (None, "", []))


def descrever_aulas(aulas: List[Aula], numeros: Dict[str, int], ps: Pseudonimizador, n: int = ULTIMAS_AULAS) -> str:
    sel = [a for a in aulas if not a.cancelada][-n:]
    if not sel:
        return "(nenhuma aula registrada)"
    blocos = []
    for a in sel:
        cls = "; ".join(f"{c.conteudo} ({T.SITUACOES.get(c.situacao, c.situacao)})" for c in a.classificacao_conteudos) or "; ".join(a.conteudo_realizado)
        partes = [f"Aula {numeros.get(a.id, 0)} · {a.data} · {T.FREQUENCIAS.get(a.frequencia, a.frequencia)} · {T.TIPOS_AULA.get(a.tipo_aula, a.tipo_aula)}"]
        if cls:
            partes.append(f"  trabalhado: {cls}")
        if a.rendimento:
            partes.append("  rendimento: " + ", ".join(f"{grading.rotulo(k)} {v}" for k, v in a.rendimento.items()))
        if a.dificuldades:
            partes.append("  dificuldades: " + "; ".join(a.dificuldades))
        if a.conquistas:
            partes.append("  conquistas: " + "; ".join(a.conquistas))
        if a.avaliacao_qualitativa:
            partes.append(f"  avaliação: {a.avaliacao_qualitativa}")
        if a.observacoes:
            partes.append(f"  observações: {a.observacoes}")
        if a.proximo_passo:
            partes.append(f"  próximo passo: {a.proximo_passo}")
        blocos.append(ps.aplicar("\n".join(partes)))
    return "\n".join(blocos)


def descrever_perfil_instrumento(perfil: Dict[str, Any], tema: Optional[str] = None) -> str:
    """Trecho compacto do perfil instrumental: progressão do tema, dificuldades, exercícios do tema."""
    linhas = [f"- instrumento: {perfil.get('nome')} ({perfil.get('familia')})"]
    if perfil.get("tessitura"):
        linhas.append(f"- tessitura: {json.dumps(perfil['tessitura'], ensure_ascii=False)}")
    prog = perfil.get("progressoes") or {}
    temas = [tema] if tema and tema in prog else list(prog)[:3]
    for t in temas:
        linhas.append(f"- progressão de {t}: " + " → ".join(prog[t]))
    if perfil.get("dificuldades_frequentes"):
        linhas.append("- dificuldades frequentes: " + "; ".join(perfil["dificuldades_frequentes"][:5]))
    ex = (perfil.get("tipos_de_exercicios") or {}).get(tema or "", []) if tema else []
    for e in ex[:4]:
        linhas.append(f"- exercício sugerido ({t if temas else ''}): {e.get('titulo')} — {e.get('descricao')} [recursos: {', '.join(e.get('recursos') or []) or 'nenhum'}]")
    return "\n".join(linhas)


def descrever_fontes(fontes: List[Any]) -> str:
    if not fontes:
        return "(nenhuma fonte disponível — a lista de referencias deve ficar vazia)"
    linhas = []
    for f in fontes:
        d = f.model_dump() if hasattr(f, "model_dump") else dict(f)
        tipo = T.ORIGENS_FONTE.get(d.get("tipo", ""), d.get("tipo", ""))
        linhas.append(f"- id={d.get('id_origem')} · {tipo} · {d.get('titulo')} · {d.get('autor', '')} {d.get('ano') or ''}" + (f" · p. {d.get('pagina')}" if d.get("pagina") else "") + (f"\n  trecho: {d.get('trecho')[:600]}" if d.get("trecho") else ""))
    return "\n".join(linhas)
