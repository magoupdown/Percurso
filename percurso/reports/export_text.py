"""Exportação Markdown e CSV (SPEC §12.6)."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from .model import Relatorio


def exportar_markdown(rel: Relatorio, destino: Path) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(rel.como_markdown(), encoding="utf-8")
    return destino


def exportar_csv(rel: Relatorio, destino: Path) -> List[Path]:
    """Um CSV por tabela (relatórios tabulares). Devolve os caminhos criados."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    saidas = []
    tabelas = rel.tabelas()
    for i, t in enumerate(tabelas):
        p = destino if len(tabelas) == 1 else destino.with_name(f"{destino.stem}_{i + 1}{destino.suffix}")
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(t.cabecalho)
            for l in t.linhas:
                w.writerow(l)
        saidas.append(p)
    if not tabelas and rel.resumo_numeros:
        with open(destino, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["indicador", "valor"])
            for k, v in rel.resumo_numeros.items():
                w.writerow([k, v])
        saidas.append(destino)
    return saidas
