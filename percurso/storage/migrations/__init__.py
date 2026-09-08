"""Versionamento e migração de schema (SPEC §4.5).

`configuracoes/versao.json` guarda a versão global; cada arquivo guarda a sua.
Ao detectar versão antiga: backup da pasta afetada e migração. Campos desconhecidos → `_extra`.
"""
from __future__ import annotations

from typing import Callable, Dict, List

from ...core.models import SCHEMA_VERSION, Versao
from ..repo import Repositorio
from . import v0_to_v1

MIGRACOES: Dict[int, Callable[[Repositorio], List[str]]] = {
    0: v0_to_v1.migrar,
}

MENSAGEM_MIGRACAO = "Versão antiga detectada. Fazendo backup e atualizando seus dados…"


def detectar_versao(repo: Repositorio) -> int:
    v = repo.ler_versao()
    if v is not None:
        return int(v.schema_version)
    # sem versao.json: se há registros, são dados antigos (v0); senão, instalação nova
    if repo.listar_codigos() or any(repo.caminhos.registros.glob("*/")):
        return 0
    return SCHEMA_VERSION


def executar(repo: Repositorio, informar: Callable[[str], None] = lambda m: None) -> List[str]:
    """Migra até SCHEMA_VERSION. Devolve lista de ações realizadas (para log/relatório)."""
    acoes: List[str] = []
    atual = detectar_versao(repo)
    if atual < SCHEMA_VERSION:
        informar(MENSAGEM_MIGRACAO)
        if repo.caminhos.registros.exists() and any(repo.caminhos.registros.iterdir()):
            destino = repo.backup_pasta(repo.caminhos.registros, f"pre-migracao-v{SCHEMA_VERSION}")
            acoes.append(f"backup criado em {destino.name}")
        if repo.caminhos.configuracoes.exists():
            destino = repo.backup_pasta(repo.caminhos.configuracoes, f"pre-migracao-v{SCHEMA_VERSION}")
            acoes.append(f"backup de configurações em {destino.name}")
        while atual < SCHEMA_VERSION:
            fn = MIGRACOES.get(atual)
            if fn is None:
                raise RuntimeError(f"Não existe migração da versão {atual} para {atual + 1}.")
            acoes.extend(fn(repo))
            atual += 1
    if repo.ler_versao() is None or repo.ler_versao().schema_version != SCHEMA_VERSION:
        repo.gravar_versao(Versao(schema_version=SCHEMA_VERSION))
        acoes.append(f"versão gravada: {SCHEMA_VERSION}")
    return acoes
