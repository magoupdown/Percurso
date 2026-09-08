"""Contrato do adaptador de domínio (SPEC §5.1).

O núcleo só conhece esta interface. Toda referência a instrumento, tessitura, técnica,
music21 etc. vive no adaptador concreto (ex.: `percurso.domains.music`).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DomainAdapter(ABC):
    id: str = "base"
    nome: str = "Base"

    @abstractmethod
    def listar_especialidades(self) -> List[Dict[str, str]]:
        """[{'id': 'piano', 'nome': 'Piano'}, ...] — instrumentos / áreas."""

    @abstractmethod
    def perfil_especialidade(self, id_especialidade: str) -> Dict[str, Any]:
        """Perfil estruturado (SPEC §5.2). Deve considerar cópia editada pelo professor, se houver."""

    @abstractmethod
    def rubrica_padrao(self, especialidade: str, modalidade: str, idade: Optional[int]) -> List[str]:
        """Ids de critérios de avaliação (ex.: ['leitura', 'ritmo', ...])."""

    @abstractmethod
    def progressao_sugerida(self, estado_atual: Dict[str, Any], perfil: Dict[str, Any], curriculo: str) -> Dict[str, str]:
        """{'conteudo': ..., 'tema': ..., 'justificativa': ...} — próximo passo sugerido."""

    @abstractmethod
    def vocabulario(self, especialidade: str) -> Dict[str, List[str]]:
        """{'pt': [...], 'en': [...]} para expansão de consultas."""

    @abstractmethod
    def gerar_material_deterministico(self, tipo: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Ex.: MIDI/MusicXML de escala. Devolve {'arquivos': [...], 'descricao': ...}."""

    @abstractmethod
    def validar_conteudo(self, texto: str) -> List[str]:
        """Checagens determinísticas; devolve lista de avisos (vazia = ok)."""

    @abstractmethod
    def expandir_consulta(self, tema: str, especialidade: str, nivel: str) -> List[str]:
        """Consultas PT/EN derivadas do vocabulário."""

    # ---- opcionais com implementação padrão -------------------------------
    def sinonimos_pedagogicos(self) -> Dict[str, List[str]]:
        """Mapa termo → sinônimos PT/EN usado pela busca BM25 (SPEC §9.5)."""
        return {}

    def rotulo_criterio(self, id_criterio: str) -> str:
        return id_criterio.replace("_", " ").capitalize()

    def exercicios_para(
        self,
        perfil: Dict[str, Any],
        conteudo: str,
        recursos: List[str],
        idade: Optional[int],
        maximo: int = 4,
    ) -> List[Dict[str, Any]]:
        return []

    def tema_do_conteudo(self, perfil: Dict[str, Any], conteudo: str) -> Optional[str]:
        return None

    def dificuldades_esperadas(self, perfil: Dict[str, Any], conteudo: str) -> List[str]:
        return list(perfil.get("dificuldades_frequentes", []))[:3]
