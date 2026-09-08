"""Estado pedagógico atual e resumo (SPEC §4.3). Atualização determinística.

- O professor classifica cada conteúdo trabalhado como consolidado / em desenvolvimento / dificuldade.
- Dificuldade citada em >= 2 aulas vira recorrente.
- O estado é recalculado a partir de TODAS as aulas (ordem por data), o que torna o registro
  retroativo seguro: reordenar aulas reordena o estado.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from ..utils import dates
from . import grading
from .models import Aula, Encontro, EstadoAtual, Registro, ResumoPedagogico

LIMITE_RECORRENTE = 2
ULTIMOS_ENCONTROS = 5


def _norm(texto: str) -> str:
    return " ".join((texto or "").strip().lower().split())


def _dedupe(itens: Sequence[str]) -> List[str]:
    vistos = set()
    saida = []
    for i in itens:
        k = _norm(i)
        if k and k not in vistos:
            vistos.add(k)
            saida.append(i.strip())
    return saida


def classificacoes_da_aula(aula: Aula) -> List[tuple]:
    """[(conteudo, situacao)] — usa classificacao_conteudos; senão, conteudo_realizado como em_desenvolvimento."""
    if aula.classificacao_conteudos:
        return [(c.conteudo, c.situacao) for c in aula.classificacao_conteudos if c.conteudo.strip()]
    return [(c, "em_desenvolvimento") for c in aula.conteudo_realizado if c.strip()]


def recalcular_estado(aulas: Sequence[Aula], estado_anterior: Optional[EstadoAtual] = None) -> EstadoAtual:
    """Recalcula o estado a partir da lista completa de aulas (ordenada por data)."""
    ordenadas = sorted([a for a in aulas if not a.cancelada], key=lambda a: (a.data, a.criado_em, a.id))
    consolidados: List[str] = []
    em_dev: List[str] = []
    dificuldades_contagem: Dict[str, int] = {}
    dificuldades_rotulo: Dict[str, str] = {}
    unidade = estado_anterior.unidade_atual if estado_anterior else ""
    proximo = ""
    ultima_obs = ""
    trabalhados: List[str] = []

    for a in ordenadas:
        if a.unidade:
            unidade = a.unidade
        for conteudo, situacao in classificacoes_da_aula(a):
            k = _norm(conteudo)
            trabalhados.append(conteudo)
            # remove de todas as listas e reinsere na correta (o estado mais recente vence)
            consolidados = [c for c in consolidados if _norm(c) != k]
            em_dev = [c for c in em_dev if _norm(c) != k]
            if situacao == "consolidado":
                consolidados.append(conteudo)
            elif situacao == "em_desenvolvimento":
                em_dev.append(conteudo)
            elif situacao == "dificuldade":
                em_dev.append(conteudo)
                dificuldades_contagem[k] = dificuldades_contagem.get(k, 0) + 1
                dificuldades_rotulo[k] = conteudo
        for d in a.dificuldades:
            k = _norm(d)
            if k:
                dificuldades_contagem[k] = dificuldades_contagem.get(k, 0) + 1
                dificuldades_rotulo[k] = d
        if a.proximo_passo.strip():
            proximo = a.proximo_passo.strip()
        if a.observacoes.strip():
            ultima_obs = a.observacoes.strip()
        elif a.avaliacao_qualitativa.strip():
            ultima_obs = a.avaliacao_qualitativa.strip()

    recorrentes = [dificuldades_rotulo[k] for k, n in dificuldades_contagem.items() if n >= LIMITE_RECORRENTE]
    recentes = []
    if ordenadas:
        ult = ordenadas[-1]
        recentes = _dedupe(list(ult.dificuldades) + [c for c, s in classificacoes_da_aula(ult) if s == "dificuldade"])

    estado = EstadoAtual(
        total_aulas=len(ordenadas),
        ultima_aula=ordenadas[-1].data if ordenadas else None,
        unidade_atual=unidade,
        conteudos_consolidados=_dedupe(consolidados),
        em_desenvolvimento=_dedupe(em_dev),
        dificuldades_recorrentes=_dedupe(recorrentes),
        dificuldades_recentes=recentes,
        proximo_objetivo=proximo,
        ultima_observacao=ultima_obs,
        rendimento_recente=grading.recentes(ordenadas, 3),
        conteudos_trabalhados_recentes=_dedupe(list(reversed(trabalhados)))[:8],
    )
    return estado


def gerar_resumo_template(registro: Registro, estado: EstadoAtual, aulas: Sequence[Aula], numeros: Optional[Dict[str, int]] = None) -> ResumoPedagogico:
    """Resumo pedagógico por template (Modo Essencial). <= 1500 caracteres + últimos 5 encontros."""
    ordenadas = sorted([a for a in aulas if not a.cancelada], key=lambda a: (a.data, a.criado_em, a.id))
    numeros = numeros or {a.id: i + 1 for i, a in enumerate(ordenadas)}
    quem = registro.identificacao or registro.codigo
    inst = registro.nome_instrumento_exibicao
    partes = []
    if not ordenadas:
        partes.append(f"{quem} ({inst}, {registro.nivel}) ainda não possui aulas registradas.")
    else:
        partes.append(
            f"{quem} ({inst}, nível {registro.nivel}) tem {estado.total_aulas} aula(s) registrada(s); "
            f"última em {dates.formatar_data_br(estado.ultima_aula)}."
        )
        if estado.unidade_atual:
            partes.append(f"Unidade atual: {estado.unidade_atual}.")
        if estado.conteudos_consolidados:
            partes.append("Consolidado: " + "; ".join(estado.conteudos_consolidados[-6:]) + ".")
        if estado.em_desenvolvimento:
            partes.append("Em desenvolvimento: " + "; ".join(estado.em_desenvolvimento[-6:]) + ".")
        if estado.dificuldades_recorrentes:
            partes.append("Dificuldades recorrentes: " + "; ".join(estado.dificuldades_recorrentes[:4]) + ".")
        if estado.proximo_objetivo:
            partes.append(f"Próximo objetivo: {estado.proximo_objetivo}.")
        if estado.ultima_observacao:
            partes.append(f"Última observação: {estado.ultima_observacao}")
    texto = " ".join(partes)[:1500]

    encontros: List[Encontro] = []
    for a in ordenadas[-ULTIMOS_ENCONTROS:]:
        cls = classificacoes_da_aula(a)
        conteudo = ", ".join(c for c, _ in cls) or ", ".join(a.conteudo_planejado)
        situ = _situacao_resumida(cls)
        linha = a.observacoes or a.avaliacao_qualitativa or a.proximo_passo or ""
        encontros.append(
            Encontro(
                data=a.data,
                numero=numeros.get(a.id, 0),
                conteudo=conteudo[:200],
                situacao=situ,
                linha=linha.strip().split("\n")[0][:160],
            )
        )
    return ResumoPedagogico(texto=texto, ultimos_encontros=encontros, gerado_por="template")


def _situacao_resumida(cls: Sequence[tuple]) -> str:
    if not cls:
        return ""
    n = {"consolidado": 0, "em_desenvolvimento": 0, "dificuldade": 0}
    for _, s in cls:
        n[s] = n.get(s, 0) + 1
    partes = []
    if n["consolidado"]:
        partes.append(f"{n['consolidado']} consolidado(s)")
    if n["em_desenvolvimento"]:
        partes.append(f"{n['em_desenvolvimento']} em desenvolvimento")
    if n["dificuldade"]:
        partes.append(f"{n['dificuldade']} com dificuldade")
    return ", ".join(partes)


def classificacao_pre_preenchida(estado: EstadoAtual, conteudos: Sequence[str]) -> List[Dict[str, str]]:
    """Pré-preenche a classificação de conteúdos com o estado anterior (SPEC §4.3)."""
    cons = {_norm(c) for c in estado.conteudos_consolidados}
    dif = {_norm(c) for c in estado.dificuldades_recorrentes} | {_norm(c) for c in estado.dificuldades_recentes}
    saida = []
    for c in conteudos:
        k = _norm(c)
        if k in cons:
            s = "consolidado"
        elif k in dif:
            s = "dificuldade"
        else:
            s = "em_desenvolvimento"
        saida.append({"conteudo": c, "situacao": s})
    return saida


def atualizar_apos_aula(repo, codigo: str) -> EstadoAtual:
    """Recalcula e grava estado + resumo após registrar/editar/excluir uma aula."""
    registro = repo.ler_registro(codigo)
    aulas = repo.listar_aulas(codigo)
    anterior = repo.ler_estado(codigo)
    estado = recalcular_estado(aulas, anterior)
    repo.gravar_estado(codigo, estado)
    resumo_atual = repo.ler_resumo(codigo)
    numeros = {a.id: n for n, a in repo.numerar_aulas(codigo)}
    novo = gerar_resumo_template(registro, estado, aulas, numeros)
    if resumo_atual.gerado_por in ("gemini", "professor") and resumo_atual.texto:
        # preserva texto editado/gerado; atualiza só a lista de encontros
        resumo_atual.ultimos_encontros = novo.ultimos_encontros
        repo.gravar_resumo(codigo, resumo_atual)
    else:
        repo.gravar_resumo(codigo, novo)
    return estado
