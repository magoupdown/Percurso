"""Materiais sob demanda (SPEC §8.5): folha do professor, folha do aluno, exercícios, rubrica, ficha,
lista de repertório → PDF/DOCX; exemplos musicais → MIDI/MusicXML; QR do registro.
Salvos em registros/<código>/materiais/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..core import grading, planner
from ..core.models import Plano, Registro, Repertorio, Rubricas
from ..support import donations
from ..utils import dates
from . import export_docx, export_pdf
from .model import Relatorio, Secao, Tabela

TIPOS = {
    "folha_professor": "Folha do professor",
    "folha_aluno": "Folha do aluno",
    "exercicios": "Exercícios",
    "rubrica": "Rubrica de avaliação",
    "ficha": "Ficha do registro",
    "repertorio": "Lista de repertório",
}


def _base(reg: Registro, titulo: str, fuso: Optional[str]) -> Relatorio:
    return Relatorio(tipo="material", titulo=titulo, subtitulo="Material gerado pelo Percurso", codigo=reg.codigo, identificacao=reg.identificacao or (reg.turma.nome if reg.turma else ""), gerado_em=dates.formatar_data_br(dates.hoje(fuso)))


def folha_professor(reg: Registro, plano: Plano, fuso: Optional[str], rubricas: Optional[Rubricas] = None) -> Relatorio:
    r = _base(reg, f"Folha do professor — {plano.tema}", fuso)
    r.subtitulo = f"{plano.rotulo} · {dates.formatar_data_br(plano.data)} · {plano.duracao_min} min"
    r.secoes = [
        Secao("Objetivos", paragrafos=[plano.objetivo_geral], itens=plano.objetivos_especificos),
        Secao("Cronograma", tabelas=[Tabela("Blocos", ["Início", "Fim", "Bloco"], [[f"{b.inicio_min} min", f"{b.fim_min} min", b.titulo] for b in plano.cronograma])]),
        Secao("Atividades", itens=[f"{a.titulo} ({a.duracao_min} min): {a.descricao}" for a in plano.atividades]),
        Secao("Intervenções do professor", itens=plano.intervencoes_professor),
        Secao("Possíveis dificuldades", itens=plano.possiveis_dificuldades),
        Secao("Avaliação", paragrafos=[plano.avaliacao], itens=[grading.rotulo(c, rubricas) for c in plano.criterios]),
        Secao("Continuidade", paragrafos=[plano.continuidade]),
        Secao("Justificativa pedagógica", paragrafos=[plano.justificativa_pedagogica.estrutura, plano.justificativa_pedagogica.adequacao]),
    ]
    if plano.referencias:
        from ..research import trace

        r.secoes.append(Secao("Referências", itens=[trace.formatar(f) for f in plano.referencias]))
    return r


def folha_aluno(reg: Registro, plano: Plano, fuso: Optional[str]) -> Relatorio:
    r = _base(reg, f"Aula de hoje — {plano.tema}", fuso)
    r.subtitulo = dates.formatar_data_br(plano.data)
    atividades = [a for a in plano.atividades if a.bloco not in ("avaliacao", "alternativa")]
    r.secoes = [
        Secao("O que vamos fazer hoje", itens=[f"{a.titulo}: {a.descricao}" for a in atividades]),
        Secao("Para praticar em casa", itens=[plano.continuidade]),
        Secao("Minhas anotações", paragrafos=["\n\n" + "_" * 60 + "\n\n" + "_" * 60 + "\n\n" + "_" * 60]),
    ]
    return r


def exercicios(reg: Registro, plano: Plano, fuso: Optional[str]) -> Relatorio:
    r = _base(reg, f"Exercícios — {plano.tema}", fuso)
    r.secoes = [Secao(a.titulo, paragrafos=[a.descricao, f"Duração sugerida: {a.duracao_min} min" + (f" · Recursos: {', '.join(a.recursos)}" if a.recursos else "")]) for a in plano.atividades if a.bloco in ("exploracao", "pratica", "aplicacao", "alternativa")]
    if not r.secoes:
        r.secoes = [Secao("Exercícios", paragrafos=["Este plano não contém exercícios específicos."])]
    return r


def rubrica(reg: Registro, criterios: List[str], fuso: Optional[str], rubricas: Optional[Rubricas] = None, escala: int = 5) -> Relatorio:
    r = _base(reg, "Rubrica de avaliação", fuso)
    linhas = [[grading.rotulo(c, rubricas)] + [""] * escala + [""] for c in criterios]
    r.secoes = [Secao("Critérios (marque 1 a 5 somente no que observar)", tabelas=[Tabela("Rubrica", ["Critério"] + [str(i) for i in range(1, escala + 1)] + ["Observação"], linhas)])]
    return r


def ficha(reg: Registro, estado, fuso: Optional[str], nome_instrumento: str) -> Relatorio:
    r = _base(reg, "Ficha do registro", fuso)
    r.resumo_numeros = {"Instrumento/área": nome_instrumento, "Nível": reg.nivel, "Modalidade": reg.modalidade, "Contexto": reg.contexto, "Currículo": reg.curriculo, "Agenda": f"{reg.agenda.dia_habitual} {reg.agenda.inicio}–{reg.agenda.termino} ({reg.agenda.duracao_min} min)", "Aulas registradas": str(estado.total_aulas)}
    r.secoes = [
        Secao("Conhecimentos prévios", itens=reg.conhecimentos_previos or ["—"]),
        Secao("Objetivos", itens=reg.objetivos or ["—"]),
        Secao("Estado atual", itens=[f"Consolidado: {', '.join(estado.conteudos_consolidados) or '—'}", f"Em desenvolvimento: {', '.join(estado.em_desenvolvimento) or '—'}", f"Dificuldades recorrentes: {', '.join(estado.dificuldades_recorrentes) or '—'}", f"Próximo objetivo: {estado.proximo_objetivo or '—'}"]),
        Secao("Adaptações e observações", paragrafos=[reg.adaptacoes or "—", reg.observacoes or "—"]),
    ]
    return r


def lista_repertorio(reg: Registro, rep: Repertorio, fuso: Optional[str]) -> Relatorio:
    r = _base(reg, "Lista de repertório", fuso)
    linhas = [[i.obra, i.compositor, i.arranjo, i.nivel, i.estado.replace("_", " "), dates.formatar_data_br(i.inicio) if i.inicio else "", dates.formatar_data_br(i.fim) if i.fim else ""] for i in rep.itens]
    r.secoes = [Secao("Repertório", tabelas=[Tabela("Obras", ["Obra", "Compositor", "Arranjo", "Nível", "Estado", "Início", "Fim"], linhas or [["—"] * 7])])]
    return r


def salvar(rel: Relatorio, pasta: Path, nome_base: str, formatos: List[str]) -> Dict[str, str]:
    pasta.mkdir(parents=True, exist_ok=True)
    saida = {}
    if "pdf" in formatos:
        saida["pdf"] = str(export_pdf.exportar(rel, pasta / f"{nome_base}.pdf"))
    if "docx" in formatos:
        saida["docx"] = str(export_docx.exportar(rel, pasta / f"{nome_base}.docx"))
    return saida


def exemplo_musical(adaptador, pasta: Path, tipo: str, parametros: Dict) -> Dict:
    """MIDI + MusicXML via music21 (D8)."""
    params = dict(parametros)
    params["destino"] = str(pasta)
    params.setdefault("nome_base", f"{tipo}_{dates.carimbo_arquivo()}")
    return adaptador.gerar_material_deterministico(tipo, params)


def qr_registro(reg: Registro, pasta: Path) -> Path:
    return donations.salvar_qr(reg.codigo, pasta / "qr_codigo.png")
