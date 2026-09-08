"""Estrutura de pastas dentro de <base_path> (SPEC §4.1). O código só opera dentro dela."""
from __future__ import annotations

from pathlib import Path
import re

SUBPASTAS = [
    "configuracoes",
    "configuracoes/perfis",
    "registros",
    "biblioteca",
    "biblioteca/arquivos",
    "biblioteca/texto",
    "indices",
    "pesquisas",
    "pesquisas/cache",
    "curriculo",
    "relatorios",
    "exportacoes",
    "backups",
]


class Caminhos:
    def __init__(self, base_path: Path):
        self.base = Path(base_path)

    # --- raiz ---------------------------------------------------------------
    def criar_estrutura(self) -> list:
        criadas = []
        for sub in SUBPASTAS:
            p = self.base / sub
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                criadas.append(sub)
        return criadas

    def estrutura_existe(self) -> bool:
        return all((self.base / s).is_dir() for s in SUBPASTAS)

    # --- configurações -------------------------------------------------------
    @property
    def configuracoes(self) -> Path:
        return self.base / "configuracoes"

    @property
    def professor(self) -> Path:
        return self.configuracoes / "professor.json"

    @property
    def apoio(self) -> Path:
        return self.configuracoes / "apoio.json"

    @property
    def versao(self) -> Path:
        return self.configuracoes / "versao.json"

    @property
    def diagnostico_log(self) -> Path:
        return self.configuracoes / "diagnostico.log"

    @property
    def perfis_editados(self) -> Path:
        return self.configuracoes / "perfis"

    def perfil_editado(self, instrumento: str) -> Path:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", instrumento or ""):
            raise ValueError("Identificador de instrumento inválido.")
        destino = self.perfis_editados / f"{instrumento}.json"
        if not self.dentro_da_base(destino):
            raise ValueError("O perfil deve permanecer na pasta do Percurso.")
        return destino

    @property
    def rubricas(self) -> Path:
        return self.configuracoes / "rubricas.json"

    # --- registros -----------------------------------------------------------
    @property
    def registros(self) -> Path:
        return self.base / "registros"

    def registro(self, codigo: str) -> Path:
        return self.registros / codigo

    def perfil(self, codigo: str) -> Path:
        return self.registro(codigo) / "perfil.json"

    def estado_atual(self, codigo: str) -> Path:
        return self.registro(codigo) / "estado_atual.json"

    def resumo_pedagogico(self, codigo: str) -> Path:
        return self.registro(codigo) / "resumo_pedagogico.json"

    def repertorio(self, codigo: str) -> Path:
        return self.registro(codigo) / "repertorio.json"

    def aulas(self, codigo: str) -> Path:
        return self.registro(codigo) / "aulas"

    def aula(self, codigo: str, data_iso: str, id4: str) -> Path:
        return self.aulas(codigo) / f"{data_iso}_{id4}.json"

    def planos(self, codigo: str) -> Path:
        return self.registro(codigo) / "planos"

    def plano(self, codigo: str, data_iso: str, id4: str) -> Path:
        return self.planos(codigo) / f"{data_iso}_{id4}.json"

    def materiais(self, codigo: str) -> Path:
        return self.registro(codigo) / "materiais"

    # --- biblioteca ----------------------------------------------------------
    @property
    def biblioteca(self) -> Path:
        return self.base / "biblioteca"

    @property
    def catalogo(self) -> Path:
        return self.biblioteca / "catalogo.json"

    @property
    def biblioteca_arquivos(self) -> Path:
        return self.biblioteca / "arquivos"

    @property
    def biblioteca_texto(self) -> Path:
        return self.biblioteca / "texto"

    def arquivo_biblioteca(self, sha: str, ext: str) -> Path:
        return self.biblioteca_arquivos / f"{sha}.{ext.lstrip('.')}"

    def texto_biblioteca(self, sha: str) -> Path:
        return self.biblioteca_texto / f"{sha}.json"

    # --- índices e pesquisa --------------------------------------------------
    @property
    def indices(self) -> Path:
        return self.base / "indices"

    @property
    def indice_bm25(self) -> Path:
        return self.indices / "biblioteca_bm25.json"

    @property
    def indice_emb_gemini(self) -> Path:
        return self.indices / "biblioteca_emb_gemini.json"

    @property
    def indice_emb_local(self) -> Path:
        return self.indices / "biblioteca_emb_local.json"

    @property
    def pesquisas_cache(self) -> Path:
        return self.base / "pesquisas" / "cache"

    def pesquisa_cache(self, hash_query: str) -> Path:
        return self.pesquisas_cache / f"{hash_query}.json"

    # --- saídas --------------------------------------------------------------
    @property
    def curriculo(self) -> Path:
        return self.base / "curriculo"

    @property
    def relatorios(self) -> Path:
        return self.base / "relatorios"

    @property
    def exportacoes(self) -> Path:
        return self.base / "exportacoes"

    @property
    def backups(self) -> Path:
        return self.base / "backups"

    # --- segurança -----------------------------------------------------------
    def dentro_da_base(self, caminho: Path) -> bool:
        """Garante que nenhuma operação sai de <base_path> (SPEC §14.2)."""
        try:
            Path(caminho).resolve().relative_to(self.base.resolve())
            return True
        except ValueError:
            return False
