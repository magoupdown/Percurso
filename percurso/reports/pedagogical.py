"""Relatório pedagógico (SPEC §12.4): template estruturado (Essencial) ou narrativa pseudonimizada (Inteligente)."""
from __future__ import annotations

from typing import List, Optional

from ..core import attendance as calc, state as state_mod
from ..core.models import Aula, EstadoAtual, Registro, Repertorio
from ..utils import dates
from .model import Secao

ROTULO_IA = "Narrativa gerada com apoio de IA (Gemini), a partir dos registros do professor; números calculados pelo Percurso."


def secoes_template(registro: Registro, estado: EstadoAtual, aulas: List[Aula], repertorio: Repertorio, inicio: Optional[str], fim: Optional[str]) -> List[Secao]:
    sel = [a for a in calc.filtrar_periodo(aulas, inicio, fim) if not a.cancelada]
    est_periodo = state_mod.recalcular_estado(sel) if (inicio or fim) else estado
    trabalhados = []
    conquistas, dificuldades, reps, tarefas = [], [], [], []
    for a in sel:
        for c, s in state_mod.classificacoes_da_aula(a):
            if c not in trabalhados:
                trabalhados.append(c)
        conquistas += [x for x in a.conquistas if x not in conquistas]
        dificuldades += [x for x in a.dificuldades if x not in dificuldades]
        reps += [x for x in a.repertorio_trabalhado if x not in reps]
        tarefas += [x for x in a.tarefas if x not in tarefas]
    quem = registro.identificacao or registro.codigo
    secs = [
        Secao(titulo="Conteúdos trabalhados", itens=trabalhados or ["Nenhum conteúdo registrado no período."]),
        Secao(titulo="Conquistas", itens=(["Consolidado: " + c for c in est_periodo.conteudos_consolidados] + conquistas) or ["Nenhuma conquista registrada."]),
        Secao(titulo="Dificuldades", itens=(["Recorrente: " + d for d in est_periodo.dificuldades_recorrentes] + [d for d in dificuldades if d not in est_periodo.dificuldades_recorrentes]) or ["Nenhuma dificuldade registrada."]),
        Secao(titulo="Progressão", paragrafos=[_progressao(quem, est_periodo, sel)]),
        Secao(titulo="Repertório trabalhado no período", itens=(reps + [f"{i.obra} ({i.estado.replace('_', ' ')})" for i in repertorio.itens if i.obra not in reps]) or ["Nenhum repertório registrado."]),
        Secao(titulo="Participação", paragrafos=[_participacao(sel)]),
        Secao(titulo="Objetivos atuais", itens=([est_periodo.proximo_objetivo] if est_periodo.proximo_objetivo else []) + registro.objetivos or ["Nenhum objetivo registrado."]),
        Secao(titulo="Recomendações", itens=_recomendacoes(est_periodo, tarefas)),
    ]
    return secs


def _progressao(quem: str, est: EstadoAtual, sel: List[Aula]) -> str:
    if not sel:
        return "Sem aulas realizadas no período."
    partes = [f"{quem} realizou {len(sel)} aula(s) entre {dates.formatar_data_br(sel[0].data)} e {dates.formatar_data_br(sel[-1].data)}."]
    if est.conteudos_consolidados:
        partes.append(f"Consolidou: {', '.join(est.conteudos_consolidados[-6:])}.")
    if est.em_desenvolvimento:
        partes.append(f"Segue em desenvolvimento: {', '.join(est.em_desenvolvimento[-4:])}.")
    if est.unidade_atual:
        partes.append(f"Unidade atual: {est.unidade_atual}.")
    if est.ultima_observacao:
        partes.append(f"Última observação do professor: {est.ultima_observacao}")
    return " ".join(partes)


def _participacao(sel: List[Aula]) -> str:
    if not sel:
        return "Sem dados."
    presentes = sum(1 for a in sel if a.realizada)
    return f"Presente em {presentes} de {len(sel)} encontro(s) não cancelado(s) no período."


def _recomendacoes(est: EstadoAtual, tarefas: List[str]) -> List[str]:
    saida = []
    if est.dificuldades_recorrentes:
        saida.append(f"Priorizar a dificuldade recorrente '{est.dificuldades_recorrentes[0]}' antes de ampliar conteúdo.")
    if est.em_desenvolvimento:
        saida.append(f"Manter prática regular de '{est.em_desenvolvimento[-1]}' até consolidar.")
    if est.proximo_objetivo:
        saida.append(f"Próximo objetivo: {est.proximo_objetivo}.")
    if tarefas:
        saida.append("Tarefas propostas no período: " + "; ".join(tarefas[-3:]) + ".")
    return saida or ["Continuar a progressão planejada."]


def narrativa_gemini(sessao, registro: Registro, secs: List[Secao]) -> Optional[str]:
    """Narrativa pseudonimizada (nomes restaurados na saída). None se indisponível."""
    if not (sessao.modo_ia == "gemini" and sessao.gemini_pronto and sessao.cliente_gemini is not None):
        return None
    from ..ai.anonymize import Pseudonimizador
    from ..ai import prompts

    ps = Pseudonimizador(registro)
    quem = f"a turma {registro.codigo}" if registro.eh_turma else f"o aluno {registro.codigo}"
    corpo = "\n".join(f"## {s.titulo}\n" + "\n".join(s.paragrafos + [f"- {i}" for i in s.itens]) for s in secs)
    prompt = (
        f"Tarefa: redigir, em Português do Brasil, um relatório pedagógico narrativo (3 a 5 parágrafos, máximo 2500 caracteres) sobre {quem}, "
        "usando exclusivamente os dados abaixo. Não invente notas, frequência ou fatos. Refira-se ao aluno apenas pelo código.\n\n" + ps.aplicar(corpo)
    )
    try:
        texto = sessao.cliente_gemini.gerar_texto(prompt, sistema=prompts.carregar("sistema"))
    except Exception:  # noqa: BLE001
        return None
    if not texto or ps.contem_nome(prompt):
        return None
    return ps.restaurar(texto)[:2600]
