"""Auxiliares compartilhados pelas telas."""
from __future__ import annotations

import traceback
from typing import Callable, List, Optional

from ..core import grading
from ..utils import dates
from ..utils.logging import obter
from . import texts as T
from .session import ContextoRegistro, Sessao

log = obter("ui")


def linhas(texto: Optional[str]) -> List[str]:
    return [l.strip() for l in (texto or "").splitlines() if l.strip()]


def juntar(itens: List[str]) -> str:
    return "\n".join(itens or [])


def ok(msg: str) -> str:
    return f"<div class='percurso-ok'>{msg}</div>"


def aviso(msg: str) -> str:
    return f"<div class='percurso-aviso'>{msg}</div>"


def erro(msg: str) -> str:
    return f"<div class='percurso-erro'>{msg}</div>"


def protegido(fn: Callable, mensagem: str = T.ERRO_GENERICO):
    """Envolve um handler: exceção vira frase clara + log técnico (SPEC §15)."""

    def _wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            log.error("erro em %s: %s\n%s", getattr(fn, "__name__", "handler"), e, traceback.format_exc())
            raise _ErroUI(f"{mensagem} ({_curto(e)})") from e

    _wrapper.__name__ = getattr(fn, "__name__", "handler")
    return _wrapper


class _ErroUI(Exception):
    pass


def _curto(e: Exception) -> str:
    s = str(e).strip().split("\n")[0]
    return s[:160] if s else e.__class__.__name__


def painel_retorno(ctx: ContextoRegistro, sessao: Optional[Sessao] = None) -> str:
    """Painel de retorno (SPEC §6.3)."""
    reg, est = ctx.registro, ctx.estado
    if sessao is not None:
        nome_inst = sessao.adaptador(reg.dominio).nome_especialidade(reg.instrumento)
    else:
        nome_inst = reg.instrumento
    if reg.instrumento == "outro" and reg.instrumento_outro:
        nome_inst = reg.instrumento_outro
    quem = reg.identificacao or reg.codigo
    if reg.eh_turma and reg.turma and reg.turma.nome:
        quem = reg.turma.nome
    cab = f"**{quem}** · {nome_inst} · {T.NIVEIS.get(reg.nivel, reg.nivel)} · código `{reg.codigo}`"
    if est.total_aulas == 0:
        return f"{cab}\n\n{T.SEM_AULAS}"
    L = [cab + f" · **Aula {est.total_aulas}** · Última aula: {dates.formatar_data_br(est.ultima_aula)}"]
    if est.unidade_atual:
        L.append(f"**Unidade atual:** {est.unidade_atual}")
    if est.conteudos_trabalhados_recentes:
        L.append("**Conteúdos trabalhados:** " + " · ".join(est.conteudos_trabalhados_recentes[:6]))
    if est.conteudos_consolidados:
        L.append("**Consolidado:** " + " ".join(f"✓ {c}" for c in est.conteudos_consolidados[-5:]))
    if est.em_desenvolvimento:
        L.append("**Em desenvolvimento:** " + " · ".join(est.em_desenvolvimento[-4:]))
    if est.dificuldades_recorrentes:
        L.append("**Dificuldades recorrentes:** " + " · ".join(est.dificuldades_recorrentes[:3]))
    if est.ultima_observacao:
        L.append(f"**Última observação:** {est.ultima_observacao}")
    if est.rendimento_recente:
        partes = []
        for crit, notas in est.rendimento_recente.items():
            partes.append(f"{grading.rotulo(crit)} {'→'.join(str(n) for n in notas)}")
        L.append("**Rendimento recente:** " + " · ".join(partes))
    if sessao is not None:
        try:
            from ..core import planner

            sug = planner.sugerir_proximo_passo(sessao.entrada_planejamento())
            if sug.conteudo:
                L.append(f"**Próximo passo sugerido:** {sug.conteudo} — _{sug.justificativa}_")
        except Exception as e:  # pragma: no cover
            log.warning("sugestão indisponível: %s", e)
    return "\n\n".join(L)


def cabecalho_registro(sessao: Sessao) -> str:
    ctx = sessao.contexto
    if ctx is None:
        return aviso(T.NENHUM_REGISTRO_CARREGADO)
    reg = ctx.registro
    quem = reg.identificacao or reg.codigo
    if reg.eh_turma and reg.turma and reg.turma.nome:
        quem = reg.turma.nome
    return f"<div class='percurso-painel'><b>{quem}</b> · código {reg.codigo} · {ctx.estado.total_aulas} aula(s) registrada(s)</div>"


def badge_modo(sessao: Sessao) -> str:
    if sessao.modo_ia == "gemini" and sessao.gemini_pronto:
        return "<span class='percurso-modo percurso-modo-gemini'>" + T.MODO_INTELIGENTE + "</span>"
    return "<span class='percurso-modo percurso-modo-essencial'>" + T.MODO_ESSENCIAL + "</span>"


def opcoes_instrumentos(sessao: Sessao) -> list:
    return [(e["nome"], e["id"]) for e in sessao.adaptador().listar_especialidades()]


def opcoes_aulas(ctx: Optional[ContextoRegistro]) -> list:
    if ctx is None:
        return []
    saida = []
    for a in reversed(ctx.aulas):
        n = ctx.numeros.get(a.id, 0)
        rot = f"Aula {n:02d} · {dates.formatar_data_br(a.data)} · {T.FREQUENCIAS.get(a.frequencia, a.frequencia)}" if n else f"— · {dates.formatar_data_br(a.data)} · {T.FREQUENCIAS.get(a.frequencia, a.frequencia)}"
        cont = ", ".join(c.conteudo for c in a.classificacao_conteudos) or ", ".join(a.conteudo_realizado)
        if cont:
            rot += f" · {cont[:50]}"
        saida.append((rot, a.id))
    return saida
