"""Montagem dos seis tipos de relatório (SPEC §12.1) e exportação (§12.6)."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..core import attendance as calc
from ..utils import dates
from . import attendance, charts, export_docx, export_pdf, export_text, pedagogical, performance
from .model import Relatorio, Secao

TIPOS = {
    "frequencia": "Relatório de frequência",
    "rendimento": "Relatório de rendimento",
    "pedagogico": "Relatório pedagógico",
    "completo": "Relatório completo",
    "institucional": "Relatório institucional",
    "responsaveis": "Relatório para responsáveis",
}


def _periodo(inicio: Optional[str], fim: Optional[str]) -> str:
    if inicio and fim:
        return f"período {dates.formatar_data_br(inicio)} a {dates.formatar_data_br(fim)}"
    if inicio:
        return f"a partir de {dates.formatar_data_br(inicio)}"
    if fim:
        return f"até {dates.formatar_data_br(fim)}"
    return "todo o histórico"


def montar(sessao, tipo: str, inicio: Optional[str] = None, fim: Optional[str] = None, pasta_graficos: Optional[Path] = None, com_ia: bool = True) -> Relatorio:
    ctx = sessao.contexto
    if ctx is None:
        raise RuntimeError("Nenhum registro carregado.")
    reg, est, aulas = ctx.registro, ctx.estado, ctx.aulas
    prof = sessao.repo.ler_professor()
    rubricas = sessao.repo.ler_rubricas()
    quem = reg.identificacao or (reg.turma.nome if reg.turma else reg.codigo)
    nome_inst = sessao.adaptador(reg.dominio).nome_especialidade(reg.instrumento)
    rel = Relatorio(tipo=tipo, titulo=TIPOS.get(tipo, tipo), subtitulo=f"{quem} · {nome_inst} · {reg.nivel}", codigo=reg.codigo, identificacao=quem, periodo=_periodo(inicio, fim), gerado_em=dates.formatar_data_br(dates.hoje(sessao.fuso)), professor=prof.nome, instituicao=prof.instituicao)
    pasta_graficos = pasta_graficos or (sessao.repo.caminhos.relatorios / "graficos" / reg.codigo)
    pasta_graficos.mkdir(parents=True, exist_ok=True)
    sel = calc.filtrar_periodo(aulas, inicio, fim)

    def freq():
        n, s = attendance.secoes(reg, aulas, inicio, fim)
        g = charts.frequencia_no_periodo(calc.calcular(aulas, inicio, fim, registro=reg), pasta_graficos)
        g2 = charts.aulas_por_mes(sel, pasta_graficos)
        s[0].graficos = [x for x in (g, g2) if x]
        return n, s

    def rend():
        n, s = performance.secoes(aulas, inicio, fim, rubricas)
        g = charts.evolucao_por_criterio(sel, pasta_graficos, rubricas)
        g2 = charts.desempenho_por_criterio(sel, pasta_graficos, rubricas)
        s[0].graficos = [x for x in (g, g2) if x]
        return n, s

    def peda():
        s = pedagogical.secoes_template(reg, est, aulas, ctx.repertorio, inicio, fim)
        if com_ia:
            narrativa = pedagogical.narrativa_gemini(sessao, reg, s)
            if narrativa:
                rel.rotulo_ia = pedagogical.ROTULO_IA
                s.insert(0, Secao("Síntese narrativa", paragrafos=narrativa.split("\n\n")))
        return s

    if tipo == "frequencia":
        rel.resumo_numeros, rel.secoes = freq()
    elif tipo == "rendimento":
        rel.resumo_numeros, rel.secoes = rend()
    elif tipo == "pedagogico":
        rel.secoes = peda()
    elif tipo == "completo":
        n1, s1 = freq()
        n2, s2 = rend()
        rel.resumo_numeros = {**n1, **n2}
        rel.secoes = s1 + s2 + peda()
    elif tipo == "institucional":
        n1, s1 = freq()
        rel.resumo_numeros = {k: v for k, v in n1.items() if k in ("Aulas previstas", "Aulas realizadas", "Frequência", "Tempo total de aula")}
        rel.secoes = s1 + [Secao("Conteúdos e progressão", paragrafos=[x for s in pedagogical.secoes_template(reg, est, aulas, ctx.repertorio, inicio, fim) if s.titulo == "Progressão" for x in s.paragrafos])]
        if reg.curriculo in ("bncc", "bncc_crmg"):
            hab = sorted({h for a in sel for h in a.habilidades_curriculares})
            rel.secoes.append(Secao("Habilidades curriculares trabalhadas", itens=hab or ["Nenhuma habilidade vinculada no período."]))
    elif tipo == "responsaveis":
        n1, s1 = freq()
        rel.resumo_numeros = {"Aulas realizadas": n1["Aulas realizadas"], "Frequência": n1["Frequência"]}
        base = pedagogical.secoes_template(reg, est, aulas, ctx.repertorio, inicio, fim)
        rel.secoes = [s for s in base if s.titulo in ("Conteúdos trabalhados", "Conquistas", "Progressão", "Repertório trabalhado no período", "Recomendações")]
        rel.secoes.append(Secao("Como ajudar em casa", itens=["Garantir um horário curto e regular de prática.", "Valorizar o esforço e a continuidade, não só o resultado.", "Conversar com o professor sobre as recomendações acima."]))
    else:
        raise ValueError(f"Tipo de relatório desconhecido: {tipo}")
    return rel


def exportar(rel: Relatorio, pasta: Path, nome_base: str, formatos: List[str]) -> Dict[str, List[str]]:
    pasta.mkdir(parents=True, exist_ok=True)
    saida: Dict[str, List[str]] = {}
    if "pdf" in formatos:
        saida["pdf"] = [str(export_pdf.exportar(rel, pasta / f"{nome_base}.pdf"))]
    if "docx" in formatos:
        saida["docx"] = [str(export_docx.exportar(rel, pasta / f"{nome_base}.docx"))]
    if "md" in formatos:
        saida["md"] = [str(export_text.exportar_markdown(rel, pasta / f"{nome_base}.md"))]
    if "csv" in formatos and rel.tabelas():
        saida["csv"] = [str(p) for p in export_text.exportar_csv(rel, pasta / f"{nome_base}.csv")]
    return saida
