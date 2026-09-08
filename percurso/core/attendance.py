"""Frequência (SPEC §12.2). Cálculo em Python, nunca IA.

Regra (documentada em docs/DATA_MODEL.md):
  frequência % = (presenças + reposições + aulas extras) ÷ (aulas previstas não canceladas pela instituição) × 100
  "aulas previstas" = todas as aulas registradas no período, exceto `cancelada_instituicao`.
  `cancelada_professor` conta como prevista e não realizada (não penaliza o aluno: é listada
  separadamente e excluída do denominador quando `penalizar_cancelada_professor=False`, padrão).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence

from .models import Aula, Registro

ROTULOS_FREQUENCIA = {
    "presente": "Presente",
    "falta": "Falta",
    "falta_justificada": "Falta justificada",
    "reposicao": "Reposição",
    "aula_extra": "Aula extra",
    "cancelada_professor": "Cancelada (professor)",
    "cancelada_institucao": "Cancelada (instituição)",
    "cancelada_instituicao": "Cancelada (instituição)",
}


@dataclass
class ResumoFrequencia:
    periodo_inicio: Optional[str]
    periodo_fim: Optional[str]
    aulas_registradas: int = 0
    aulas_previstas: int = 0
    aulas_realizadas: int = 0
    presencas: int = 0
    faltas: int = 0
    faltas_justificadas: int = 0
    reposicoes: int = 0
    aulas_extras: int = 0
    canceladas_professor: int = 0
    canceladas_instituicao: int = 0
    frequencia_percentual: float = 0.0
    tempo_total_min: int = 0
    linhas: List[Dict[str, str]] = field(default_factory=list)
    por_aluno: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def como_dict(self) -> Dict:
        return {
            "periodo_inicio": self.periodo_inicio,
            "periodo_fim": self.periodo_fim,
            "aulas_registradas": self.aulas_registradas,
            "aulas_previstas": self.aulas_previstas,
            "aulas_realizadas": self.aulas_realizadas,
            "presencas": self.presencas,
            "faltas": self.faltas,
            "faltas_justificadas": self.faltas_justificadas,
            "reposicoes": self.reposicoes,
            "aulas_extras": self.aulas_extras,
            "canceladas_professor": self.canceladas_professor,
            "canceladas_instituicao": self.canceladas_instituicao,
            "frequencia_percentual": self.frequencia_percentual,
            "tempo_total_min": self.tempo_total_min,
            "linhas": self.linhas,
            "por_aluno": self.por_aluno,
        }


def filtrar_periodo(aulas: Sequence[Aula], inicio: Optional[str], fim: Optional[str]) -> List[Aula]:
    saida = []
    for a in aulas:
        if inicio and a.data < inicio:
            continue
        if fim and a.data > fim:
            continue
        saida.append(a)
    return sorted(saida, key=lambda a: a.data)


def calcular(
    aulas: Sequence[Aula],
    inicio: Optional[str] = None,
    fim: Optional[str] = None,
    registro: Optional[Registro] = None,
    penalizar_cancelada_professor: bool = False,
) -> ResumoFrequencia:
    sel = filtrar_periodo(aulas, inicio, fim)
    r = ResumoFrequencia(periodo_inicio=inicio, periodo_fim=fim, aulas_registradas=len(sel))
    numero = 0
    for a in sel:
        f = a.frequencia
        if f == "presente":
            r.presencas += 1
        elif f == "falta":
            r.faltas += 1
        elif f == "falta_justificada":
            r.faltas_justificadas += 1
        elif f == "reposicao":
            r.reposicoes += 1
        elif f == "aula_extra":
            r.aulas_extras += 1
        elif f == "cancelada_professor":
            r.canceladas_professor += 1
        elif f == "cancelada_instituicao":
            r.canceladas_instituicao += 1
        if a.realizada:
            r.aulas_realizadas += 1
            r.tempo_total_min += a.duracao_real_min or a.duracao_prevista_min
        if not a.cancelada:
            numero += 1
        r.linhas.append(
            {
                "numero": str(numero if not a.cancelada else "—"),
                "data": a.data,
                "dia": a.dia_semana,
                "previsto": f"{a.horario_previsto.inicio}–{a.horario_previsto.termino}".strip("–"),
                "real": f"{a.horario_real.inicio}–{a.horario_real.termino}".strip("–") if a.realizada else "—",
                "situacao": ROTULOS_FREQUENCIA.get(f, f),
                "duracao": str(a.duracao_real_min if a.realizada else 0),
            }
        )
    previstas = r.aulas_registradas - r.canceladas_instituicao
    if not penalizar_cancelada_professor:
        previstas -= r.canceladas_professor
    r.aulas_previstas = max(previstas, 0)
    numerador = r.presencas + r.reposicoes + r.aulas_extras
    r.frequencia_percentual = round(100.0 * numerador / r.aulas_previstas, 1) if r.aulas_previstas else 0.0

    if registro is not None and registro.eh_turma and registro.turma is not None:
        r.por_aluno = _por_aluno(sel, registro)
    return r


def _por_aluno(aulas: Sequence[Aula], registro: Registro) -> Dict[str, Dict[str, float]]:
    """Frequência individual quando a turma tem lista de alunos (SPEC §12.2)."""
    turma = registro.turma
    assert turma is not None
    alunos = {a.id: a.identificacao for a in turma.alunos}
    if not alunos:
        # frequência coletiva: n presentes de N
        total_n = 0
        total_pres = 0
        for a in aulas:
            if a.cancelada:
                continue
            ft = a.frequencia_turma
            if ft and ft.n_presentes is not None:
                total_pres += ft.n_presentes
                total_n += turma.quantidade_alunos or ft.n_presentes
        return {"_coletiva": {"presentes": total_pres, "possiveis": total_n,
                              "percentual": round(100.0 * total_pres / total_n, 1) if total_n else 0.0}}
    saida: Dict[str, Dict[str, float]] = {}
    encontros = [a for a in aulas if not a.cancelada]
    for aid, nome in alunos.items():
        presentes = 0
        for a in encontros:
            ft = a.frequencia_turma
            if ft and aid in ft.presentes:
                presentes += 1
        saida[aid] = {
            "identificacao": nome,
            "presentes": presentes,
            "encontros": len(encontros),
            "percentual": round(100.0 * presentes / len(encontros), 1) if encontros else 0.0,
        }
    return saida


def aulas_por_mes(aulas: Sequence[Aula]) -> Dict[str, int]:
    saida: Dict[str, int] = {}
    for a in aulas:
        if a.cancelada:
            continue
        chave = a.data[:7]
        saida[chave] = saida.get(chave, 0) + 1
    return dict(sorted(saida.items()))
