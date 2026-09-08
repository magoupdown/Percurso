"""Exportação PDF com reportlab (SPEC §12.6). Gráficos PNG embutidos."""
from __future__ import annotations

from pathlib import Path
from typing import List

from .model import Relatorio


def _estilos():
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    ss = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_LEFT, spaceAfter=4),
        "sub": ParagraphStyle("s", parent=ss["Normal"], fontName="Helvetica-Oblique", fontSize=10, textColor="#475569", spaceAfter=8),
        "h2": ParagraphStyle("h", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, spaceBefore=10, spaceAfter=4, textColor="#0f766e"),
        "corpo": ParagraphStyle("c", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=4),
        "item": ParagraphStyle("i", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, leftIndent=12, bulletIndent=2),
        "aviso": ParagraphStyle("a", parent=ss["Normal"], fontName="Helvetica-Oblique", fontSize=8.5, textColor="#92400e", spaceAfter=6),
        "cel": ParagraphStyle("cel", parent=ss["Normal"], fontName="Helvetica", fontSize=8, leading=10),
        "celb": ParagraphStyle("celb", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10),
    }


def _esc(t: str) -> str:
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def exportar(rel: Relatorio, destino: Path) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    st = _estilos()
    doc = SimpleDocTemplate(str(destino), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=rel.titulo, author="Percurso")
    fl: List = [Paragraph(_esc(rel.titulo), st["titulo"])]
    sub = " · ".join(x for x in [rel.subtitulo, rel.identificacao, f"código {rel.codigo}" if rel.codigo else "", rel.periodo, f"gerado em {rel.gerado_em}" if rel.gerado_em else ""] if x)
    fl.append(Paragraph(_esc(sub), st["sub"]))
    if rel.professor or rel.instituicao:
        fl.append(Paragraph(_esc(" · ".join(x for x in [rel.professor, rel.instituicao] if x)), st["sub"]))
    if rel.rotulo_ia:
        fl.append(Paragraph(_esc(rel.rotulo_ia), st["aviso"]))
    if rel.resumo_numeros:
        dados = [[Paragraph(_esc(k), st["celb"]), Paragraph(_esc(v), st["cel"])] for k, v in rel.resumo_numeros.items()]
        t = Table(dados, colWidths=[70 * mm, 60 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9"))]))
        fl += [t, Spacer(1, 6)]
    largura_util = A4[0] - 36 * mm
    for s in rel.secoes:
        fl.append(Paragraph(_esc(s.titulo), st["h2"]))
        for p in s.paragrafos:
            fl.append(Paragraph(_esc(p), st["corpo"]))
        for i in s.itens:
            fl.append(Paragraph("• " + _esc(i), st["item"]))
        for tb in s.tabelas:
            fl.append(Paragraph(_esc(tb.titulo), st["corpo"]))
            n = max(len(tb.cabecalho), 1)
            dados = [[Paragraph(_esc(c), st["celb"]) for c in tb.cabecalho]] + [[Paragraph(_esc(str(c)), st["cel"]) for c in l] for l in tb.linhas]
            t = Table(dados, colWidths=[largura_util / n] * n, repeatRows=1)
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            fl += [t, Spacer(1, 6)]
        for g in s.graficos:
            try:
                img = Image(g.caminho_png)
                escala = min(largura_util / img.imageWidth, 1.0)
                img.drawWidth = img.imageWidth * escala
                img.drawHeight = img.imageHeight * escala
                fl += [img, Spacer(1, 6)]
            except Exception:  # noqa: BLE001
                fl.append(Paragraph(_esc(f"[gráfico indisponível: {g.titulo}]"), st["aviso"]))
    fl.append(Spacer(1, 10))
    fl.append(Paragraph("Percurso — Plataforma de inteligência pedagógica", st["sub"]))
    doc.build(fl)
    return destino
