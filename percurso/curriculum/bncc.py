"""Carregamento das bases curriculares estruturadas (curriculum/data/*.json)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

PASTA_DADOS = Path(__file__).resolve().parent / "data"


class Habilidade(BaseModel):
    model_config = ConfigDict(extra="allow")
    codigo: str
    etapa: str  # EI | EF | EM
    anos: List[str] = Field(default_factory=list)
    componente: str = ""
    unidade_tematica: str = ""
    objeto: str = ""
    texto: str = ""
    musica: bool = False
    documento: str = "BNCC"


class BaseCurricular(BaseModel):
    model_config = ConfigDict(extra="allow")
    documento: str
    versao: str = ""
    fonte_oficial: str = ""
    url: str = ""
    data_obtencao: str = ""
    observacao: str = ""
    habilidades: List[Habilidade] = Field(default_factory=list)

    def por_codigo(self, codigo: str) -> Optional[Habilidade]:
        c = (codigo or "").strip().upper()
        return next((h for h in self.habilidades if h.codigo == c), None)


@lru_cache(maxsize=None)
def carregar(nome: str) -> BaseCurricular:
    caminho = PASTA_DADOS / f"{nome}.json"
    with open(caminho, "r", encoding="utf-8") as f:
        return BaseCurricular.model_validate(json.load(f))


def bncc_arte() -> BaseCurricular:
    return carregar("bncc_arte")


def bncc_infantil() -> BaseCurricular:
    return carregar("bncc_infantil")


def todas_bncc() -> Dict[str, Habilidade]:
    saida: Dict[str, Habilidade] = {}
    for base in (bncc_arte(), bncc_infantil()):
        for h in base.habilidades:
            saida[h.codigo] = h
    return saida


def versoes() -> List[Dict[str, str]]:
    """Metadados de cada base (para o cache curricular controlado por versão, SPEC §11.4)."""
    from . import crmg

    saida = []
    for base in (bncc_arte(), bncc_infantil(), crmg.crmg_arte()):
        saida.append({"documento": base.documento, "versao": base.versao, "url": base.url, "data_obtencao": base.data_obtencao, "n": len(base.habilidades)})
    return saida
