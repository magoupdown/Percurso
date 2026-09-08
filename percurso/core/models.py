"""Entidades do Percurso (SPEC §4.3). Todas carregam `schema_version`.

Campos desconhecidos são preservados (extra="allow") para que migrações nunca percam dados.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = 1

TipoRegistro = Literal["individual", "dupla", "turma"]
Modalidade = Literal[
    "individual", "dupla", "turma", "coral", "banda", "percepcao_musical",
    "musicalizacao", "oficina", "pratica_conjunto", "outro",
]
Nivel = Literal["iniciante", "basico", "intermediario", "avancado"]
Contexto = Literal["escola", "conservatorio", "aula_particular", "projeto_social", "curso_livre", "outro"]
Curriculo = Literal["bncc", "bncc_crmg", "proprio", "curso_livre", "conservatorio", "nenhum"]
Frequencia = Literal[
    "presente", "falta", "falta_justificada", "reposicao", "aula_extra",
    "cancelada_professor", "cancelada_instituicao",
]
TipoAula = Literal["continuidade", "revisao", "nova_unidade", "extraordinaria", "retroativa"]
Situacao = Literal["consolidado", "em_desenvolvimento", "dificuldade"]
ModoIA = Literal["essencial", "gemini"]
StatusPlano = Literal["gerado", "realizado", "descartado"]
EstadoRepertorio = Literal["em_estudo", "concluido", "apresentacao", "revisao"]
TipoFonte = Literal["biblioteca", "curricular", "academica", "externa"]

FREQUENCIAS_CANCELADAS = {"cancelada_professor", "cancelada_instituicao"}
FREQUENCIAS_REALIZADAS = {"presente", "reposicao", "aula_extra"}


class ModeloBase(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=False, populate_by_name=True)
    schema_version: int = SCHEMA_VERSION


# ----------------------------------------------------------------------------
# Professor
# ----------------------------------------------------------------------------
class Professor(ModeloBase):
    nome: str = ""
    instituicao: str = ""
    cidade: str = ""
    estado: str = ""
    area_principal: str = ""
    niveis_ensino: List[str] = Field(default_factory=list)
    duracao_padrao_min: int = 50
    curriculo_padrao: Curriculo = "nenhum"
    preferencias_pedagogicas: str = ""
    metodologias_preferidas: List[str] = Field(default_factory=list)
    fuso_horario: str = "America/Sao_Paulo"
    email_contato: str = ""
    onboarding_concluido: bool = False
    criado_em: str = ""
    atualizado_em: str = ""


# ----------------------------------------------------------------------------
# Registro (aluno, dupla, turma)
# ----------------------------------------------------------------------------
class AlunoTurma(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    identificacao: str


class Turma(BaseModel):
    model_config = ConfigDict(extra="allow")
    nome: str = ""
    quantidade_alunos: int = 0
    nivel_geral: Nivel = "iniciante"
    faixa_etaria: str = ""
    alunos: List[AlunoTurma] = Field(default_factory=list)


class Agenda(BaseModel):
    model_config = ConfigDict(extra="allow")
    dia_habitual: str = ""
    inicio: str = ""
    termino: str = ""
    duracao_min: int = 50


class Registro(ModeloBase):
    codigo: str
    tipo: TipoRegistro = "individual"
    modalidade: Modalidade = "individual"
    modalidade_outro: Optional[str] = None
    dominio: str = "musica"
    identificacao: str = ""
    idade: Optional[int] = None
    instrumento: str = "outro"
    instrumento_outro: Optional[str] = None
    nivel: Nivel = "iniciante"
    contexto: Contexto = "aula_particular"
    curriculo: Curriculo = "nenhum"
    agenda: Agenda = Field(default_factory=Agenda)
    conhecimentos_previos: List[str] = Field(default_factory=list)
    objetivos: List[str] = Field(default_factory=list)
    adaptacoes: str = ""
    recursos_habituais: List[str] = Field(default_factory=list)
    metodologias: List[str] = Field(default_factory=list)
    observacoes: str = ""
    turma: Optional[Turma] = None
    rubrica: List[str] = Field(default_factory=list)  # critérios ativos; vazio = padrão do perfil
    rubrica_ativa: bool = True
    criado_em: str = ""
    atualizado_em: str = ""

    @property
    def nome_instrumento_exibicao(self) -> str:
        if self.instrumento == "outro" and self.instrumento_outro:
            return self.instrumento_outro
        return self.instrumento

    @property
    def eh_turma(self) -> bool:
        return self.tipo == "turma"


# ----------------------------------------------------------------------------
# Aula
# ----------------------------------------------------------------------------
class Horario(BaseModel):
    model_config = ConfigDict(extra="allow")
    inicio: str = ""
    termino: str = ""


class BlocoCronograma(BaseModel):
    model_config = ConfigDict(extra="allow")
    inicio_min: int
    fim_min: int
    titulo: str
    descricao: str = ""
    etapa: str = ""  # acolhimento | introducao | exploracao | pratica | aplicacao | avaliacao | fechamento


class ConteudoTrabalhado(BaseModel):
    model_config = ConfigDict(extra="allow")
    conteudo: str
    situacao: Situacao = "em_desenvolvimento"


class FrequenciaTurma(BaseModel):
    model_config = ConfigDict(extra="allow")
    presentes: List[str] = Field(default_factory=list)
    ausentes: List[str] = Field(default_factory=list)
    n_presentes: Optional[int] = None


class Fonte(BaseModel):
    """Fonte rastreável (SPEC §11.5)."""

    model_config = ConfigDict(extra="allow")
    titulo: str
    autor: str = ""
    ano: Optional[str] = None
    fonte: str = ""  # nome do provedor/periódico/documento
    url: str = ""
    doi: str = ""
    pagina: Optional[str] = None
    data_consulta: str = ""
    tipo: TipoFonte = "biblioteca"
    trecho: str = ""
    id_origem: str = ""  # hash de cache, sha do documento, código da habilidade

    @field_validator("ano", mode="before")
    @classmethod
    def _ano_str(cls, v: Any) -> Any:
        return str(v) if v is not None and not isinstance(v, str) else v


class Aula(ModeloBase):
    id: str
    data: str  # YYYY-MM-DD
    dia_semana: str = ""
    horario_previsto: Horario = Field(default_factory=Horario)
    horario_real: Horario = Field(default_factory=Horario)
    duracao_prevista_min: int = 50
    duracao_real_min: int = 0
    frequencia: Frequencia = "presente"
    frequencia_turma: Optional[FrequenciaTurma] = None
    tipo_aula: TipoAula = "continuidade"
    conteudo_planejado: List[str] = Field(default_factory=list)
    conteudo_realizado: List[str] = Field(default_factory=list)
    classificacao_conteudos: List[ConteudoTrabalhado] = Field(default_factory=list)
    objetivos: List[str] = Field(default_factory=list)
    atividades: List[str] = Field(default_factory=list)
    materiais: List[str] = Field(default_factory=list)
    cronograma: List[BlocoCronograma] = Field(default_factory=list)
    rendimento: Dict[str, int] = Field(default_factory=dict)
    avaliacao_qualitativa: str = ""
    dificuldades: List[str] = Field(default_factory=list)
    conquistas: List[str] = Field(default_factory=list)
    observacoes: str = ""
    tarefas: List[str] = Field(default_factory=list)
    proximo_passo: str = ""
    repertorio_trabalhado: List[str] = Field(default_factory=list)
    habilidades_curriculares: List[str] = Field(default_factory=list)
    fontes_utilizadas: List[Fonte] = Field(default_factory=list)
    modo_ia: ModoIA = "essencial"
    plano_origem: Optional[str] = None
    unidade: str = ""
    criado_em: str = ""
    atualizado_em: str = ""

    @field_validator("rendimento", mode="before")
    @classmethod
    def _rendimento_limpo(cls, v: Any) -> Any:
        if not v:
            return {}
        saida = {}
        for k, val in dict(v).items():
            if val is None or val == "":
                continue  # nunca inventar rendimento não informado
            saida[str(k)] = int(val)
        return saida

    @property
    def cancelada(self) -> bool:
        return self.frequencia in FREQUENCIAS_CANCELADAS

    @property
    def realizada(self) -> bool:
        return self.frequencia in FREQUENCIAS_REALIZADAS

    def nome_arquivo(self) -> str:
        return f"{self.data}_{self.id}.json"


# ----------------------------------------------------------------------------
# Estado e resumo
# ----------------------------------------------------------------------------
class EstadoAtual(ModeloBase):
    total_aulas: int = 0
    ultima_aula: Optional[str] = None
    unidade_atual: str = ""
    conteudos_consolidados: List[str] = Field(default_factory=list)
    em_desenvolvimento: List[str] = Field(default_factory=list)
    dificuldades_recorrentes: List[str] = Field(default_factory=list)
    dificuldades_recentes: List[str] = Field(default_factory=list)
    proximo_objetivo: str = ""
    ultima_observacao: str = ""
    rendimento_recente: Dict[str, List[int]] = Field(default_factory=dict)
    conteudos_trabalhados_recentes: List[str] = Field(default_factory=list)
    atualizado_em: str = ""


class Encontro(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: str
    numero: int = 0
    conteudo: str = ""
    situacao: str = ""
    linha: str = ""


class ResumoPedagogico(ModeloBase):
    texto: str = ""
    ultimos_encontros: List[Encontro] = Field(default_factory=list)
    gerado_por: Literal["template", "gemini", "professor"] = "template"
    atualizado_em: str = ""

    @field_validator("texto")
    @classmethod
    def _limite(cls, v: str) -> str:
        return v[:1500]


# ----------------------------------------------------------------------------
# Repertório
# ----------------------------------------------------------------------------
class ItemRepertorio(BaseModel):
    model_config = ConfigDict(extra="allow")
    obra: str
    compositor: str = ""
    arranjo: str = ""
    nivel: str = ""
    estado: EstadoRepertorio = "em_estudo"
    inicio: Optional[str] = None
    fim: Optional[str] = None


class Repertorio(ModeloBase):
    itens: List[ItemRepertorio] = Field(default_factory=list)


# ----------------------------------------------------------------------------
# Plano de aula (SPEC §8.4)
# ----------------------------------------------------------------------------
class Atividade(BaseModel):
    model_config = ConfigDict(extra="allow")
    titulo: str
    descricao: str = ""
    duracao_min: int = 0
    bloco: str = ""
    recursos: List[str] = Field(default_factory=list)
    conteudo: str = ""


class Justificativa(BaseModel):
    model_config = ConfigDict(extra="allow")
    estrutura: str = ""  # Por que esta aula foi estruturada assim?
    adequacao: str = ""  # Por que este exercício é adequado ao instrumento e ao estágio?


class ProximoPasso(BaseModel):
    model_config = ConfigDict(extra="allow")
    conteudo: str = ""
    tema: str = ""
    justificativa: str = ""


class Plano(ModeloBase):
    id: str
    codigo_registro: str
    data: str
    status: StatusPlano = "gerado"
    origem: Literal["modelo_pedagogico", "gemini"] = "modelo_pedagogico"
    tipo_aula: TipoAula = "continuidade"
    tema: str = ""
    contexto: str = ""
    faixa_etaria: str = ""
    nivel: str = ""
    instrumento: str = ""
    duracao_min: int = 50
    objetivo_geral: str = ""
    objetivos_especificos: List[str] = Field(default_factory=list)
    conhecimentos_previos: List[str] = Field(default_factory=list)
    conteudos: List[str] = Field(default_factory=list)
    competencias: List[str] = Field(default_factory=list)
    habilidades_curriculares: List[str] = Field(default_factory=list)
    recursos: List[str] = Field(default_factory=list)
    metodologia: str = ""
    cronograma: List[BlocoCronograma] = Field(default_factory=list)
    atividades: List[Atividade] = Field(default_factory=list)
    intervencoes_professor: List[str] = Field(default_factory=list)
    possiveis_dificuldades: List[str] = Field(default_factory=list)
    adaptacoes: str = ""
    avaliacao: str = ""
    criterios: List[str] = Field(default_factory=list)
    continuidade: str = ""
    referencias: List[Fonte] = Field(default_factory=list)
    justificativa_pedagogica: Justificativa = Field(default_factory=Justificativa)
    proximo_passo_sugerido: ProximoPasso = Field(default_factory=ProximoPasso)
    consultas_realizadas: List[str] = Field(default_factory=list)
    unidade: str = ""
    avisos: List[str] = Field(default_factory=list)
    rotulo: str = "gerado por modelo pedagógico (sem IA)"
    criado_em: str = ""

    def nome_arquivo(self) -> str:
        return f"{self.data}_{self.id}.json"


# ----------------------------------------------------------------------------
# Configurações auxiliares
# ----------------------------------------------------------------------------
class Apoio(ModeloBase):
    ultimo_mes_lembrete_apoio: Optional[str] = None


class Versao(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: int = SCHEMA_VERSION
    atualizado_em: str = ""


class Rubricas(ModeloBase):
    """Critérios próprios do professor (SPEC §5.3): {id: rótulo}."""

    criterios_proprios: Dict[str, str] = Field(default_factory=dict)
    escala_max: int = 5
