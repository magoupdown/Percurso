"""Proposta de classificação de conteúdos pela IA (SPEC §4.3): o modelo propõe, o professor confirma."""
from __future__ import annotations

from typing import Dict, List

from ..core import state as state_mod
from ..ui import texts as T
from . import context, prompts, schemas, validate_loop
from .anonymize import Pseudonimizador

SITUACOES = {"consolidado", "em_desenvolvimento", "dificuldade"}


def propor(sessao, conteudos: List[str], avaliacao: str = "", dificuldades: List[str] = (), conquistas: List[str] = (), observacoes: str = "", rendimento: Dict[str, int] = None) -> List[Dict[str, str]]:
    """Devolve [{conteudo, situacao, motivo}] na mesma ordem de `conteudos`.

    Sem Gemini (ou em falha), cai no pré-preenchimento determinístico pelo estado anterior.
    """
    ctx = sessao.contexto
    conteudos = [c for c in conteudos if c.strip()]
    padrao = [dict(x, motivo="pré-preenchido pelo estado anterior") for x in state_mod.classificacao_pre_preenchida(ctx.estado if ctx else state_mod.EstadoAtual(), conteudos)]
    if ctx is None or sessao.cliente_gemini is None or not conteudos:
        return padrao
    reg = ctx.registro
    ps = Pseudonimizador(reg)
    quem = f"a turma {reg.codigo}" if reg.eh_turma else f"o aluno {reg.codigo}"

    def montar(erro: str) -> str:
        return prompts.preencher(
            "classificacao",
            quem=quem,
            estado=context.descrever_estado(ctx.estado.model_dump(), ps),
            conteudos="; ".join(ps.aplicar(c) for c in conteudos),
            avaliacao=ps.aplicar(avaliacao) or "(não informada)",
            dificuldades="; ".join(ps.aplicar(d) for d in dificuldades) or "(nenhuma)",
            conquistas="; ".join(ps.aplicar(c) for c in conquistas) or "(nenhuma)",
            observacoes=ps.aplicar(observacoes) or "(nenhuma)",
            rendimento=", ".join(f"{k} {v}" for k, v in (rendimento or {}).items()) or "(não informado)",
        ) + ("\n\n" + validate_loop.bloco_erro_para_prompt(erro) if erro else "")

    esperados = {c.lower(): c for c in conteudos}

    def validar(obj: schemas.ClassificacaoSaida) -> None:
        vistos = {}
        for it in obj.itens:
            if it.situacao not in SITUACOES:
                raise validate_loop.FalhaValidacao(f"situação inválida '{it.situacao}' para '{it.conteudo}'")
            k = it.conteudo.strip().lower()
            if k not in esperados:
                raise validate_loop.FalhaValidacao(f"conteúdo '{it.conteudo}' não está na lista; use exatamente os textos fornecidos")
            vistos[k] = it
        faltam = [c for c in esperados if c not in vistos]
        if faltam:
            raise validate_loop.FalhaValidacao("faltou classificar: " + "; ".join(esperados[f] for f in faltam))

    sistema = prompts.carregar("sistema")

    def gerar(prompt: str):
        if ps.contem_nome(prompt):
            raise validate_loop.FalhaValidacao("prompt contém nome real")
        return sessao.cliente_gemini.gerar_json(prompt, schemas.ClassificacaoSaida, sistema=sistema)

    r = validate_loop.executar(gerar, montar, schemas.ClassificacaoSaida, [validar])
    if not r.ok or r.dados is None:
        return padrao
    por_k = {it["conteudo"].strip().lower(): it for it in r.dados["itens"]}
    return [{"conteudo": c, "situacao": por_k[c.lower()]["situacao"], "motivo": ps.restaurar(por_k[c.lower()].get("motivo", "")) + " (proposta da IA — confirme)"} for c in conteudos]


def rotulo_fonte(item: Dict[str, str]) -> str:
    return item.get("motivo", "") or T.SITUACOES.get(item.get("situacao", ""), "")
