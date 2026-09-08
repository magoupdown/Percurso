"""Schemas pydantic para saída estruturada do Gemini (SPEC §7.5).

Cada geração usa response_mime_type=application/json + response_schema. Os schemas são
propositalmente simples (sem Literal/Dict complexos) para compatibilidade com o conversor do SDK.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BlocoSaida(BaseModel):
    inicio_min: int
    fim_min: int
    titulo: str
    etapa: str = Field(description="acolhimento | introducao | exploracao | pratica | aplicacao | avaliacao | fechamento")
    descricao: str = ""


class AtividadeSaida(BaseModel):
    titulo: str
    descricao: str
    duracao_min: int
    bloco: str = Field(description="etapa do cronograma em que a atividade acontece")
    recursos: List[str] = Field(default_factory=list)


class ReferenciaSaida(BaseModel):
    id_origem: str = Field(description="id exatamente igual a um dos ids fornecidos na lista de fontes disponíveis")
    uso: str = Field(default="", description="como a fonte foi usada no plano")


class JustificativaSaida(BaseModel):
    estrutura: str
    adequacao: str


class PlanoSaida(BaseModel):
    tema: str
    objetivo_geral: str
    objetivos_especificos: List[str]
    conteudos: List[str]
    competencias: List[str]
    habilidades_curriculares: List[str] = Field(default_factory=list, description="somente códigos da lista fornecida; vazio se nenhum")
    metodologia: str
    cronograma: List[BlocoSaida]
    atividades: List[AtividadeSaida]
    intervencoes_professor: List[str]
    possiveis_dificuldades: List[str]
    adaptacoes: str
    avaliacao: str
    continuidade: str
    referencias: List[ReferenciaSaida] = Field(default_factory=list)
    justificativa_pedagogica: JustificativaSaida
    proximo_passo_sugerido: str = ""
    proximo_passo_justificativa: str = ""


class ResumoSaida(BaseModel):
    texto: str = Field(description="resumo pedagógico em até 1500 caracteres, em português do Brasil")


class ClassificacaoItem(BaseModel):
    conteudo: str
    situacao: str = Field(description="consolidado | em_desenvolvimento | dificuldade")
    motivo: str = ""


class ClassificacaoSaida(BaseModel):
    itens: List[ClassificacaoItem]


class RespostaHistorico(BaseModel):
    resposta: str
    aulas_citadas: List[str] = Field(default_factory=list, description="datas (AAAA-MM-DD) das aulas usadas na resposta")
    confianca: str = Field(default="media", description="alta | media | baixa")


class AdaptacaoTextoSaida(BaseModel):
    texto: str


class ComparacaoFontesSaida(BaseModel):
    sintese: str
    convergencias: List[str] = Field(default_factory=list)
    divergencias: List[str] = Field(default_factory=list)
    ids_utilizados: List[str] = Field(default_factory=list)
