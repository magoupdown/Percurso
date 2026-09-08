"""Gráficos (SPEC §12.5): matplotlib, PNG, sem decoração. Evolução por critério, frequência, aulas por mês, desempenho."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..core import attendance as calc, grading
from ..core.models import Aula, Rubricas
from .model import Grafico


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    return plt


def evolucao_por_criterio(aulas: List[Aula], destino: Path, rubricas: Optional[Rubricas] = None) -> Optional[Grafico]:
    ev = grading.evolucao(aulas)
    if not ev:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=120)
    for crit, pontos in ev.items():
        ax.plot([d[5:] for d, _ in pontos], [n for _, n in pontos], marker="o", linewidth=1.5, label=grading.rotulo(crit, rubricas))
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel("Nota (1–5)")
    ax.set_xlabel("Aula (mês-dia)")
    ax.legend(loc="lower right", fontsize=7, ncol=2)
    ax.set_title("Evolução por critério")
    fig.tight_layout()
    p = destino / "evolucao_criterios.png"
    fig.savefig(p)
    plt.close(fig)
    return Grafico("Evolução por critério", str(p))


def frequencia_no_periodo(resumo: calc.ResumoFrequencia, destino: Path) -> Optional[Grafico]:
    if resumo.aulas_registradas == 0:
        return None
    plt = _plt()
    rot = ["Presenças", "Faltas", "Faltas just.", "Reposições", "Extras", "Canc. prof.", "Canc. inst."]
    val = [resumo.presencas, resumo.faltas, resumo.faltas_justificadas, resumo.reposicoes, resumo.aulas_extras, resumo.canceladas_professor, resumo.canceladas_instituicao]
    fig, ax = plt.subplots(figsize=(7, 3), dpi=120)
    ax.bar(rot, val, color="#0f766e")
    for i, v in enumerate(val):
        ax.text(i, v + 0.05, str(v), ha="center", fontsize=8)
    ax.set_title(f"Frequência no período: {resumo.frequencia_percentual:.1f} %")
    ax.set_ylabel("Aulas")
    fig.tight_layout()
    p = destino / "frequencia.png"
    fig.savefig(p)
    plt.close(fig)
    return Grafico("Frequência no período", str(p))


def aulas_por_mes(aulas: List[Aula], destino: Path) -> Optional[Grafico]:
    por_mes: Dict[str, int] = calc.aulas_por_mes(aulas)
    if not por_mes:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 2.8), dpi=120)
    ax.bar(list(por_mes.keys()), list(por_mes.values()), color="#0f766e")
    ax.set_title("Aulas por mês")
    ax.set_ylabel("Aulas")
    fig.tight_layout()
    p = destino / "aulas_por_mes.png"
    fig.savefig(p)
    plt.close(fig)
    return Grafico("Aulas por mês", str(p))


def desempenho_por_criterio(aulas: List[Aula], destino: Path, rubricas: Optional[Rubricas] = None) -> Optional[Grafico]:
    medias = grading.medias(aulas)
    if not medias:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 2.8), dpi=120)
    rot = [grading.rotulo(c, rubricas) for c in medias]
    ax.barh(rot, list(medias.values()), color="#0f766e")
    ax.set_xlim(0, 5)
    ax.set_xlabel("Média (1–5)")
    ax.set_title("Desempenho por critério")
    fig.tight_layout()
    p = destino / "desempenho_criterios.png"
    fig.savefig(p)
    plt.close(fig)
    return Grafico("Desempenho por critério", str(p))
