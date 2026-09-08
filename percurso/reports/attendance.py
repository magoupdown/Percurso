"""Relatório de frequência (SPEC §12.2). Cálculo em `core.attendance`, nunca IA."""
from __future__ import annotations

from typing import List, Optional

from ..core import attendance as calc
from ..core.models import Aula, Registro
from ..utils import dates
from .model import Secao, Tabela


def secoes(registro: Registro, aulas: List[Aula], inicio: Optional[str], fim: Optional[str]) -> tuple:
    """Devolve (resumo_numeros, [Secao]) da frequência no período."""
    r = calc.calcular(aulas, inicio, fim, registro=registro)
    numeros = {
        "Aulas registradas": str(r.aulas_registradas),
        "Aulas previstas": str(r.aulas_previstas),
        "Aulas realizadas": str(r.aulas_realizadas),
        "Presenças": str(r.presencas),
        "Faltas": str(r.faltas),
        "Faltas justificadas": str(r.faltas_justificadas),
        "Reposições": str(r.reposicoes),
        "Aulas extras": str(r.aulas_extras),
        "Canceladas (professor)": str(r.canceladas_professor),
        "Canceladas (instituição)": str(r.canceladas_instituicao),
        "Frequência": f"{r.frequencia_percentual:.1f} %",
        "Tempo total de aula": f"{r.tempo_total_min} min ({r.tempo_total_min / 60:.1f} h)",
    }
    tabela = Tabela(
        titulo="Aulas no período",
        cabecalho=["Aula", "Data", "Dia", "Previsto", "Real", "Situação", "Duração (min)"],
        linhas=[[l["numero"], dates.formatar_data_br(l["data"]), dates.DIAS_SEMANA_NOME.get(l["dia"], l["dia"]), l["previsto"] or "—", l["real"] or "—", l["situacao"], l["duracao"]] for l in r.linhas],
    )
    sec = Secao(
        titulo="Frequência",
        paragrafos=[
            f"Frequência de {r.frequencia_percentual:.1f} % no período: {r.presencas + r.reposicoes + r.aulas_extras} presença(s) (incluindo reposições e aulas extras) em {r.aulas_previstas} aula(s) prevista(s) não cancelada(s).",
            "Regra de cálculo: (presenças + reposições + aulas extras) ÷ (aulas registradas − canceladas pela instituição − canceladas pelo professor) × 100. Documentada em docs/DATA_MODEL.md.",
        ],
        tabelas=[tabela],
    )
    saida = [sec]
    if r.por_aluno:
        if "_coletiva" in r.por_aluno:
            c = r.por_aluno["_coletiva"]
            saida.append(Secao(titulo="Frequência coletiva da turma", paragrafos=[f"{int(c['presentes'])} presença(s) em {int(c['possiveis'])} possíveis ({c['percentual']:.1f} %)."]))
        else:
            t2 = Tabela(titulo="Frequência por aluno", cabecalho=["Aluno", "Presenças", "Encontros", "Frequência"], linhas=[[str(v["identificacao"]), str(int(v["presentes"])), str(int(v["encontros"])), f"{v['percentual']:.1f} %"] for v in r.por_aluno.values()])
            saida.append(Secao(titulo="Frequência por aluno", tabelas=[t2]))
    return numeros, saida
