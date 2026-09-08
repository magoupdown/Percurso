"""Resumo pedagógico narrativo no Modo Inteligente (SPEC §4.3, §7.2). O professor pode editar."""
from __future__ import annotations

from typing import Optional

from ..core.models import ResumoPedagogico
from ..ui import texts as T
from ..utils.logging import obter
from . import context, prompts, schemas, validate_loop
from .anonymize import Pseudonimizador
from .gemini import hash_prompt

log = obter("resumo")


def reescrever(sessao, codigo: Optional[str] = None) -> ResumoPedagogico:
    """Reescreve o resumo com Gemini (pseudonimizado) e grava com gerado_por='gemini'.

    Em falha, devolve o resumo atual sem alterá-lo.
    """
    ctx = sessao.contexto if codigo is None else sessao.carregar(codigo)
    if ctx is None or sessao.cliente_gemini is None:
        raise RuntimeError(T.GEMINI_SEM_RESPOSTA)
    reg = ctx.registro
    ps = Pseudonimizador(reg)
    quem = f"a turma {reg.codigo}" if reg.eh_turma else f"o aluno {reg.codigo}"
    nome_inst = sessao.adaptador(reg.dominio).nome_especialidade(reg.instrumento)

    def montar(erro: str) -> str:
        return prompts.preencher(
            "resumo",
            quem=quem,
            perfil=context.descrever_perfil(reg, nome_inst, ps),
            estado=context.descrever_estado(ctx.estado.model_dump(), ps),
            ultimas_aulas=context.descrever_aulas(ctx.aulas, ctx.numeros, ps),
            resumo_atual=ps.aplicar(ctx.resumo.texto),
        ) + ("\n\n" + validate_loop.bloco_erro_para_prompt(erro) if erro else "")

    def validar(obj: schemas.ResumoSaida) -> None:
        if not obj.texto.strip():
            raise validate_loop.FalhaValidacao("texto vazio")
        if len(obj.texto) > 1500:
            raise validate_loop.FalhaValidacao(f"texto com {len(obj.texto)} caracteres; máximo 1500")

    chave = hash_prompt("resumo", montar(""))
    if chave in sessao.cache_ia:
        dados = sessao.cache_ia[chave]
    else:
        sistema = prompts.carregar("sistema")

        def gerar(prompt: str):
            if ps.contem_nome(prompt):
                raise validate_loop.FalhaValidacao("prompt contém nome real")
            return sessao.cliente_gemini.gerar_json(prompt, schemas.ResumoSaida, sistema=sistema)

        r = validate_loop.executar(gerar, montar, schemas.ResumoSaida, [validar])
        if not r.ok or r.dados is None:
            raise RuntimeError(r.mensagens[-1] if r.mensagens else T.GEMINI_SEM_RESPOSTA)
        dados = r.dados
        sessao.cache_ia[chave] = dados
    novo = ResumoPedagogico(texto=ps.restaurar(dados["texto"]), ultimos_encontros=ctx.resumo.ultimos_encontros, gerado_por="gemini")
    sessao.repo.gravar_resumo(reg.codigo, novo)
    sessao.recarregar()
    return novo


def salvar_edicao(sessao, texto: str) -> ResumoPedagogico:
    ctx = sessao.contexto
    if ctx is None:
        raise RuntimeError(T.NENHUM_REGISTRO_CARREGADO)
    novo = ResumoPedagogico(texto=(texto or "")[:1500], ultimos_encontros=ctx.resumo.ultimos_encontros, gerado_por="professor")
    sessao.repo.gravar_resumo(ctx.codigo, novo)
    sessao.recarregar()
    return novo
