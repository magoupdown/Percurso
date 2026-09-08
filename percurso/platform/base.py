"""Contrato comum entre Colab e ambiente local."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class Plataforma(ABC):
    nome: str = "base"

    @abstractmethod
    def montar_armazenamento(self) -> Path:
        """Garante que o armazenamento está disponível e devolve o base_path da pasta Percurso."""

    @abstractmethod
    def obter_segredo(self, nome: str) -> Optional[str]:
        """Lê um segredo (ex.: GEMINI_API_KEY). Nunca registra o valor."""

    @abstractmethod
    def caminho_log_runtime(self) -> Path:
        ...

    def eh_colab(self) -> bool:
        return False

    def url_proxy(self, porta: int) -> Optional[str]:
        """URL pública pela qual o navegador alcança a porta local (só faz sentido no Colab)."""
        return None

    def limpar_dados_locais(self) -> list:
        """Apaga arquivos temporários da sessão (SPEC §14.5). Devolve o que removeu."""
        return []


_atual: Optional[Plataforma] = None


def detectar() -> Plataforma:
    """Colab se `google.colab` for importável e /content existir; senão, local."""
    try:
        import google.colab  # type: ignore  # noqa: F401

        if os.path.isdir("/content"):
            from .colab import PlataformaColab

            return PlataformaColab()
    except Exception:
        pass
    from .local import PlataformaLocal

    return PlataformaLocal()


def obter_plataforma() -> Plataforma:
    global _atual
    if _atual is None:
        _atual = detectar()
    return _atual


def definir_plataforma(p: Optional[Plataforma]) -> None:
    global _atual
    _atual = p
