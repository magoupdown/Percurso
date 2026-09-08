"""Estado de sessão (SPEC §3.4): vive só em memória e morre com o runtime.

Contém: repositório, plataforma, modo IA, chave temporária, consentimento de trechos,
mapa de pseudonimização, registro carregado e último plano gerado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core import planner, state as state_mod
from ..core.models import Aula, EstadoAtual, Plano, Registro, Repertorio, ResumoPedagogico
from ..domains import obter_adaptador
from ..platform.base import Plataforma
from ..storage.repo import RegistroNaoEncontrado, Repositorio
from ..utils import dates
from ..utils.logging import obter

log = obter("sessao")


@dataclass
class ContextoRegistro:
    registro: Registro
    estado: EstadoAtual
    resumo: ResumoPedagogico
    aulas: List[Aula]
    repertorio: Repertorio
    numeros: Dict[str, int]

    @property
    def codigo(self) -> str:
        return self.registro.codigo


@dataclass
class Sessao:
    repo: Repositorio
    plataforma: Plataforma
    modo_ia: str = "essencial"  # essencial | gemini
    chave_temporaria: Optional[str] = None
    gemini_pronto: bool = False
    consentimento_trechos: bool = False
    mapa_pseudonimos: Dict[str, str] = field(default_factory=dict)
    contexto: Optional[ContextoRegistro] = None
    ultimo_plano: Optional[Plano] = None
    formulario_aula: Dict[str, Any] = field(default_factory=dict)
    mostrar_lembrete_apoio: bool = False
    mensagens_inicio: List[str] = field(default_factory=list)
    cache_ia: Dict[str, Any] = field(default_factory=dict)
    cliente_gemini: Any = None

    # ------------------------------------------------------------ registro
    def carregar(self, codigo: str) -> ContextoRegistro:
        registro = self.repo.ler_registro(codigo)
        return self._montar_contexto(registro)

    def recarregar(self) -> Optional[ContextoRegistro]:
        if self.contexto is None:
            return None
        try:
            return self._montar_contexto(self.repo.ler_registro(self.contexto.codigo))
        except RegistroNaoEncontrado:
            self.contexto = None
            return None

    def _montar_contexto(self, registro: Registro) -> ContextoRegistro:
        codigo = registro.codigo
        numerados = self.repo.numerar_aulas(codigo)
        ctx = ContextoRegistro(
            registro=registro,
            estado=self.repo.ler_estado(codigo),
            resumo=self.repo.ler_resumo(codigo),
            aulas=[a for _, a in numerados],
            repertorio=self.repo.ler_repertorio(codigo),
            numeros={a.id: n for n, a in numerados},
        )
        self.contexto = ctx
        return ctx

    def descarregar(self) -> None:
        self.contexto = None
        self.ultimo_plano = None
        self.formulario_aula = {}

    # ------------------------------------------------------------- domínio
    def adaptador(self, dominio: str = "musica"):
        return obter_adaptador(dominio, self.repo.caminhos.perfis_editados)

    # ---------------------------------------------------------------- fuso
    @property
    def fuso(self) -> str:
        try:
            return self.repo.ler_professor().fuso_horario or dates.FUSO_PADRAO
        except Exception:
            return dates.FUSO_PADRAO

    # ------------------------------------------------------------- planos
    def entrada_planejamento(self, **kw) -> planner.EntradaPlanejamento:
        ctx = self.contexto
        if ctx is None:
            raise RuntimeError("Nenhum registro carregado.")
        return planner.EntradaPlanejamento(
            registro=ctx.registro,
            estado=ctx.estado,
            resumo=ctx.resumo,
            aulas=ctx.aulas,
            repertorio=ctx.repertorio,
            pasta_perfis_editados=self.repo.caminhos.perfis_editados,
            rubricas_professor=self.repo.ler_rubricas(),
            **kw,
        )

    def registrar_aula(self, aula: Aula) -> int:
        """Grava a aula, recalcula o estado e devolve o número derivado da aula."""
        ctx = self.contexto
        if ctx is None:
            raise RuntimeError("Nenhum registro carregado.")
        aula = self.repo.gravar_aula(ctx.codigo, aula)
        state_mod.atualizar_apos_aula(self.repo, ctx.codigo)
        if aula.plano_origem:
            self._marcar_plano_realizado(ctx.codigo, aula.plano_origem)
        self.recarregar()
        return self.repo.numero_da_aula(ctx.codigo, aula.id)

    def _marcar_plano_realizado(self, codigo: str, plano_origem: str) -> None:
        try:
            nome = Path(plano_origem).name
            for p in self.repo.listar_planos(codigo):
                if p.nome_arquivo() == nome and p.status != "realizado":
                    p.status = "realizado"
                    self.repo.gravar_plano(p)
        except Exception as e:  # pragma: no cover
            log.warning("não foi possível marcar plano como realizado: %s", e)

    # ------------------------------------------------------------ pseudônimos
    def pseudonimizar(self, texto: str) -> str:
        """Substitui identificação do registro (e dos alunos da turma) por códigos/índices (D7)."""
        ctx = self.contexto
        if ctx is None or not texto:
            return texto
        saida = texto
        reg = ctx.registro
        pares = []
        if reg.identificacao.strip():
            pares.append((reg.identificacao.strip(), f"o aluno {reg.codigo}" if not reg.eh_turma else f"a turma {reg.codigo}"))
        if reg.turma:
            for al in reg.turma.alunos:
                if al.identificacao.strip():
                    pares.append((al.identificacao.strip(), f"aluno {al.id}"))
        pares.sort(key=lambda p: -len(p[0]))
        for nome, codigo in pares:
            self.mapa_pseudonimos[codigo] = nome
            saida = _substituir_palavra(saida, nome, codigo)
        return saida

    def restaurar_nomes(self, texto: str) -> str:
        saida = texto or ""
        for codigo, nome in sorted(self.mapa_pseudonimos.items(), key=lambda p: -len(p[0])):
            saida = saida.replace(codigo, nome)
            # variantes "PCR-XXXXXX" isolado
            if codigo.startswith("o aluno ") or codigo.startswith("a turma "):
                saida = saida.replace(codigo.split(" ", 2)[2], nome)
        return saida


def _substituir_palavra(texto: str, alvo: str, novo: str) -> str:
    import re

    return re.sub(rf"(?<!\w){re.escape(alvo)}(?!\w)", novo, texto, flags=re.IGNORECASE)
