"""Busca livre no histórico (SPEC §6.6, Modo Inteligente): pergunta interpretada pelo Gemini, pseudonimizada."""
from __future__ import annotations

from ..ui import texts as T
from . import context, prompts, schemas, validate_loop
from .anonymize import Pseudonimizador
from .gemini import hash_prompt

MAX_AULAS_NO_PROMPT = 40


def perguntar(sessao, pergunta: str) -> str:
    ctx = sessao.contexto
    if ctx is None:
        return T.NENHUM_REGISTRO_CARREGADO
    if sessao.cliente_gemini is None:
        return T.GEMINI_SEM_RESPOSTA
    pergunta = (pergunta or "").strip()
    if not pergunta:
        return T.HISTORICO_PERGUNTA_LIVRE
    reg = ctx.registro
    ps = Pseudonimizador(reg)
    quem = f"a turma {reg.codigo}" if reg.eh_turma else f"o aluno {reg.codigo}"

    def montar(erro: str) -> str:
        return prompts.preencher(
            "historico",
            quem=quem,
            estado=context.descrever_estado(ctx.estado.model_dump(), ps),
            aulas=context.descrever_aulas(ctx.aulas, ctx.numeros, ps, n=MAX_AULAS_NO_PROMPT),
            pergunta=ps.aplicar(pergunta),
        ) + ("\n\n" + validate_loop.bloco_erro_para_prompt(erro) if erro else "")

    datas = {a.data for a in ctx.aulas}

    def validar(obj: schemas.RespostaHistorico) -> None:
        if not obj.resposta.strip():
            raise validate_loop.FalhaValidacao("resposta vazia")
        inexistentes = [d for d in obj.aulas_citadas if d not in datas]
        if inexistentes:
            raise validate_loop.FalhaValidacao("datas citadas não existem no histórico: " + ", ".join(inexistentes))

    chave = hash_prompt("historico", montar(""))
    if chave in sessao.cache_ia:
        dados = sessao.cache_ia[chave]
    else:
        sistema = prompts.carregar("sistema")

        def gerar(prompt: str):
            if ps.contem_nome(prompt):
                raise validate_loop.FalhaValidacao("prompt contém nome real")
            return sessao.cliente_gemini.gerar_json(prompt, schemas.RespostaHistorico, sistema=sistema)

        r = validate_loop.executar(gerar, montar, schemas.RespostaHistorico, [validar])
        if not r.ok or r.dados is None:
            return r.mensagens[-1] if r.mensagens else T.GEMINI_SEM_RESPOSTA
        dados = r.dados
        sessao.cache_ia[chave] = dados
    texto = ps.restaurar(dados["resposta"])
    if dados.get("aulas_citadas"):
        texto += "\n\n_Aulas consultadas: " + ", ".join(dates_br(d) for d in dados["aulas_citadas"]) + "_"
    texto += f"\n\n_Resposta gerada com apoio de IA (confiança {dados.get('confianca', 'media')})._"
    return texto


def dates_br(d: str) -> str:
    from ..utils import dates

    try:
        return dates.formatar_data_br(d)
    except Exception:
        return d
