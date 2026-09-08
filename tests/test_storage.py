"""Escrita atômica, repositório, primeira abertura, reabertura, migração (casos 1, 2, 10, 18)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import percurso
from percurso.core import state
from percurso.core.models import SCHEMA_VERSION, Registro
from percurso.platform.local import PlataformaLocal
from percurso.storage import atomic
from percurso.storage.migrations import detectar_versao, executar
from percurso.storage.repo import RegistroNaoEncontrado, Repositorio

from conftest import aula, registro_piano


# --------------------------------------------------------------- atômica
def test_escrita_atomica_e_bak(tmp_path):
    p = tmp_path / "x.json"
    atomic.escrever_json(p, {"a": 1})
    atomic.escrever_json(p, {"a": 2})
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 2}
    assert json.loads(p.with_name("x.json.bak").read_text(encoding="utf-8")) == {"a": 1}
    assert not p.with_name("x.json.tmp").exists()


def test_escrita_atomica_validador_falha_preserva_original(tmp_path):
    p = tmp_path / "x.json"
    atomic.escrever_json(p, {"a": 1})

    def validador(obj):
        raise ValueError("inválido")

    with pytest.raises(atomic.ErroEscrita):
        atomic.escrever_json(p, {"a": 2}, validador=validador)
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 1}
    assert not p.with_name("x.json.tmp").exists()


def test_leitura_corrompida_cai_no_bak(tmp_path):
    p = tmp_path / "x.json"
    atomic.escrever_json(p, {"a": 1})
    atomic.escrever_json(p, {"a": 2})
    p.write_text("{corrompido", encoding="utf-8")
    assert atomic.ler_json(p) == {"a": 1}


# ------------------------------------------------ caso 1: primeira abertura
def test_primeira_abertura_cria_estrutura_e_versao(base):
    assert not base.exists()
    sessao = percurso.preparar(plataforma=PlataformaLocal(base), informar=lambda m: None)
    for sub in ["configuracoes", "registros", "biblioteca/arquivos", "indices", "pesquisas/cache", "relatorios", "exportacoes", "backups"]:
        assert (base / sub).is_dir()
    v = sessao.repo.ler_versao()
    assert v is not None and v.schema_version == SCHEMA_VERSION
    assert "Estrutura criada" in " ".join(sessao.mensagens_inicio)


# ------------------------------------------ caso 2/10: reabrir sem alterar
def test_reabrir_recupera_dados_sem_alteracao(base):
    s1 = percurso.preparar(plataforma=PlataformaLocal(base), informar=lambda m: None)
    reg = registro_piano(s1.repo)
    s1.repo.gravar_aula(reg.codigo, aula("2026-08-01", [("nota única", "consolidado")], rendimento={"leitura": 3}))
    state.atualizar_apos_aula(s1.repo, reg.codigo)
    antes = {p.relative_to(base): p.read_bytes() for p in base.rglob("*.json")}

    s2 = percurso.preparar(plataforma=PlataformaLocal(base), informar=lambda m: None)
    assert "recuperados" in " ".join(s2.mensagens_inicio)
    depois = {p.relative_to(base): p.read_bytes() for p in base.rglob("*.json")}
    # apoio.json muda (lembrete do mês); o restante permanece idêntico
    for k, v in antes.items():
        if k.name != "apoio.json":
            assert depois[k] == v, k
    ctx = s2.carregar(reg.codigo.lower().replace("-", ""))
    assert ctx.estado.total_aulas == 1
    assert ctx.estado.conteudos_consolidados == ["nota única"]
    assert ctx.aulas[0].rendimento == {"leitura": 3}


def test_registro_inexistente(repo):
    with pytest.raises(RegistroNaoEncontrado):
        repo.ler_registro("PCR-ZZZZZZ")


def test_criar_registro_cria_arquivos_base(repo):
    reg = registro_piano(repo)
    pasta = repo.caminhos.registro(reg.codigo)
    for nome in ["perfil.json", "estado_atual.json", "resumo_pedagogico.json", "repertorio.json"]:
        assert (pasta / nome).exists()
    assert (pasta / "aulas").is_dir() and (pasta / "planos").is_dir() and (pasta / "materiais").is_dir()
    assert repo.listar_codigos() == [reg.codigo]


def test_escrita_fora_da_base_bloqueada(repo, tmp_path):
    from percurso.core.models import Professor

    with pytest.raises(PermissionError):
        repo._gravar(tmp_path / "fora.json", Professor())


# -------------------------------------------------- caso 18: migração v0
def _dados_v0(base: Path, codigo="PCR-ABC234"):
    reg = base / "registros" / codigo
    (reg / "aulas").mkdir(parents=True)
    (reg / "perfil.json").write_text(json.dumps({"codigo": codigo, "nome": "Maria", "instrumento": "violao", "campo_antigo": "x"}, ensure_ascii=False), encoding="utf-8")
    (reg / "aulas" / "2026-03-01_a1b2.json").write_text(json.dumps({"data": "2026-03-01", "conteudo": "acorde de Mi menor, pulso", "presenca": "sim", "nota_extra": 7}, ensure_ascii=False), encoding="utf-8")
    (reg / "estado_atual.json").write_text(json.dumps({"total_aulas": 1}), encoding="utf-8")


def test_migracao_v0_sem_perda_com_backup(base):
    _dados_v0(base)
    repo = Repositorio(base)
    assert detectar_versao(repo) == 0
    acoes = executar(repo)
    assert any("backup" in a for a in acoes)
    assert repo.ler_versao().schema_version == SCHEMA_VERSION
    reg = repo.ler_registro("PCR-ABC234")
    assert reg.identificacao == "Maria" and reg.instrumento == "violao"
    assert reg.model_dump()["_extra"]["campo_antigo"] == "x"
    aulas = repo.listar_aulas("PCR-ABC234")
    assert len(aulas) == 1
    assert aulas[0].frequencia == "presente"
    assert aulas[0].conteudo_realizado == ["acorde de Mi menor", "pulso"]
    assert aulas[0].model_dump()["_extra"]["nota_extra"] == 7
    backups = repo.listar_backups()
    assert backups and any("pre-migracao" in b for b in backups)
    # o backup contém o arquivo original intacto
    bkp = base / "backups" / [b for b in backups if "pre-migracao" in b][0] / "registros" / "PCR-ABC234" / "perfil.json"
    assert json.loads(bkp.read_text(encoding="utf-8"))["nome"] == "Maria"
    # segunda execução é idempotente
    assert executar(repo) == []


def test_preparar_migra_automaticamente(base):
    _dados_v0(base)
    msgs = []
    sessao = percurso.preparar(plataforma=PlataformaLocal(base), informar=msgs.append)
    assert any("Versão antiga" in m for m in msgs)
    assert sessao.repo.ler_registro("PCR-ABC234").identificacao == "Maria"


# --------------------------------------------------------------- LGPD
def test_excluir_registro_cria_backup(repo):
    reg = registro_piano(repo)
    repo.gravar_aula(reg.codigo, aula("2026-08-01", [("x", "consolidado")]))
    itens = repo.descrever_exclusao_registro(reg.codigo)
    assert "perfil.json" in itens and any(i.startswith("aulas") for i in itens)
    pasta = repo.excluir_registro(reg.codigo)
    assert not repo.registro_existe(reg.codigo)
    assert (pasta / reg.codigo / "perfil.json").exists()


def test_exportar_zip(repo, tmp_path):
    import zipfile

    reg = registro_piano(repo)
    destino = repo.caminhos.exportacoes / "tudo.zip"
    repo.exportar_zip(destino)
    with zipfile.ZipFile(destino) as z:
        nomes = z.namelist()
    assert any(reg.codigo in n and n.endswith("perfil.json") for n in nomes)
    destino2 = repo.caminhos.exportacoes / "um.zip"
    repo.exportar_zip(destino2, apenas_registro=reg.codigo)
    with zipfile.ZipFile(destino2) as z:
        assert all(reg.codigo in n for n in z.namelist())


def test_logs_redigem_chaves(tmp_path):
    from percurso.utils import logging as L

    assert "AIza" not in L.redigir("chave AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ123 aqui")
    assert "[REDIGIDO]" in L.redigir("api_key=abc123")
