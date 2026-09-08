"""Catálogo da biblioteca (SPEC §9.3): biblioteca/catalogo.json."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..core.models import SCHEMA_VERSION
from ..storage.atomic import escrever_json, ler_json
from ..storage.paths import Caminhos

CATEGORIAS = [
    "pedagogia musical", "teoria", "percepção", "harmonia", "história", "técnica instrumental",
    "repertório", "educação infantil", "avaliação", "currículo", "inclusão", "metodologia", "outros",
]
TIPOS_DOCUMENTO = ["livro", "artigo", "apostila", "partitura", "capítulo", "tese/dissertação", "material próprio", "outro"]


class Documento(BaseModel):
    model_config = ConfigDict(extra="allow")
    hash: str
    nome_original: str
    extensao: str
    titulo: str = ""
    autor: str = ""
    ano: str = ""
    categoria: str = "outros"
    area: str = "musica"
    instrumento: str = ""
    nivel: str = ""
    tipo_documento: str = "outro"
    observacoes: str = ""
    data_inclusao: str = ""
    paginas: int = 0
    n_trechos: int = 0
    sem_texto: bool = False
    tamanho_bytes: int = 0


class Catalogo(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: int = SCHEMA_VERSION
    documentos: List[Documento] = Field(default_factory=list)

    def por_hash(self, sha: str) -> Optional[Documento]:
        return next((d for d in self.documentos if d.hash == sha), None)

    def indexaveis(self) -> List[Documento]:
        return [d for d in self.documentos if not d.sem_texto and d.n_trechos > 0]


def ler(caminhos: Caminhos) -> Catalogo:
    dados = ler_json(caminhos.catalogo, None)
    return Catalogo.model_validate(dados) if dados else Catalogo()


def gravar(caminhos: Caminhos, catalogo: Catalogo) -> None:
    escrever_json(caminhos.catalogo, catalogo.model_dump(mode="json"), validador=lambda o: Catalogo.model_validate(o))


def ler_trechos(caminhos: Caminhos, sha: str) -> List[Dict]:
    dados = ler_json(caminhos.texto_biblioteca(sha), None)
    return list(dados.get("trechos", [])) if dados else []


def gravar_trechos(caminhos: Caminhos, sha: str, trechos: List[Dict]) -> None:
    escrever_json(caminhos.texto_biblioteca(sha), {"schema_version": SCHEMA_VERSION, "hash": sha, "trechos": trechos})


def descrever(doc: Documento) -> str:
    partes = [doc.titulo or doc.nome_original]
    if doc.autor:
        partes.append(doc.autor)
    if doc.ano:
        partes.append(doc.ano)
    return " · ".join(partes)
