"""Estrutura comum dos relatórios: título, metadados, seções (texto/lista), tabelas e gráficos (PNG)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Tabela:
    titulo: str
    cabecalho: List[str]
    linhas: List[List[str]]


@dataclass
class Grafico:
    titulo: str
    caminho_png: str


@dataclass
class Secao:
    titulo: str
    paragrafos: List[str] = field(default_factory=list)
    itens: List[str] = field(default_factory=list)
    tabelas: List[Tabela] = field(default_factory=list)
    graficos: List[Grafico] = field(default_factory=list)


@dataclass
class Relatorio:
    tipo: str  # frequencia | rendimento | pedagogico | completo | institucional | responsaveis
    titulo: str
    subtitulo: str = ""
    codigo: str = ""
    identificacao: str = ""
    periodo: str = ""
    gerado_em: str = ""
    professor: str = ""
    instituicao: str = ""
    rotulo_ia: str = ""  # "gerado com apoio de IA" quando houver narrativa
    secoes: List[Secao] = field(default_factory=list)
    resumo_numeros: Dict[str, str] = field(default_factory=dict)

    def como_markdown(self) -> str:
        L = [f"# {self.titulo}"]
        if self.subtitulo:
            L.append(f"_{self.subtitulo}_")
        cab = [x for x in [self.identificacao, f"código {self.codigo}" if self.codigo else "", self.periodo, f"gerado em {self.gerado_em}" if self.gerado_em else ""] if x]
        if cab:
            L.append(" · ".join(cab))
        if self.professor or self.instituicao:
            L.append(" · ".join(x for x in [self.professor, self.instituicao] if x))
        if self.rotulo_ia:
            L.append(f"> {self.rotulo_ia}")
        if self.resumo_numeros:
            L.append("| Indicador | Valor |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in self.resumo_numeros.items()))
        for s in self.secoes:
            L.append(f"## {s.titulo}")
            L.extend(s.paragrafos)
            if s.itens:
                L.append("\n".join(f"- {i}" for i in s.itens))
            for t in s.tabelas:
                L.append(f"**{t.titulo}**\n\n| " + " | ".join(t.cabecalho) + " |\n|" + "---|" * len(t.cabecalho) + "\n" + "\n".join("| " + " | ".join(str(c) for c in l) + " |" for l in t.linhas))
            for g in s.graficos:
                L.append(f"![{g.titulo}]({g.caminho_png})")
        return "\n\n".join(L)

    def tabelas(self) -> List[Tabela]:
        return [t for s in self.secoes for t in s.tabelas]
