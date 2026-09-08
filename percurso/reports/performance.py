"""Relatório de rendimento (SPEC §12.3): somente dados registrados; evolução por critério."""
from __future__ import annotations

from typing import List, Optional

from ..core import attendance as calc, grading
from ..core.models import Aula, Rubricas
from ..utils import dates
from .model import Secao, Tabela


def secoes(aulas: List[Aula], inicio: Optional[str], fim: Optional[str], rubricas: Optional[Rubricas] = None) -> tuple:
    sel = calc.filtrar_periodo(aulas, inicio, fim)
    ev = grading.evolucao(sel)
    if not ev:
        return {}, [Secao(titulo="Rendimento", paragrafos=["Nenhum rendimento registrado no período. O Percurso nunca preenche notas não informadas."])]
    medias = grading.medias(sel)
    numeros = {grading.rotulo(c, rubricas): f"média {m:.1f}" for c, m in medias.items()}
    criterios = list(ev.keys())
    datas = sorted({d for v in ev.values() for d, _ in v})
    linhas = []
    for d in datas:
        linha = [dates.formatar_data_br(d)]
        for c in criterios:
            nota = next((n for dd, n in ev[c] if dd == d), None)
            linha.append(str(nota) if nota is not None else "—")
        linhas.append(linha)
    tabela = Tabela(titulo="Notas por aula (1–5)", cabecalho=["Data"] + [grading.rotulo(c, rubricas) for c in criterios], linhas=linhas)
    itens = []
    for c in criterios:
        notas = [n for _, n in ev[c]]
        tend = {"subindo": "em evolução", "caindo": "em queda", "estavel": "estável", "sem_dados": "poucos dados"}[grading.tendencia(notas)]
        itens.append(f"{grading.rotulo(c, rubricas)}: {len(notas)} registro(s), média {medias[c]:.1f}, {tend} ({notas[0]} → {notas[-1]}).")
    return numeros, [Secao(titulo="Rendimento", paragrafos=["Evolução por critério ao longo das aulas, apenas com o que o professor registrou."], itens=itens, tabelas=[tabela])]
