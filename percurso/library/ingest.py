"""Pipeline de ingestão (SPEC §9.2).

arquivo → validar formato → SHA-256 → duplicado? → copiar para biblioteca/arquivos/<sha>.<ext>
→ extrair texto → trechos → biblioteca/texto/<sha>.json → metadados → indexar (incremental) → catálogo
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..storage.paths import Caminhos
from ..utils import dates
from ..utils.hashing import sha256_arquivo
from ..utils.logging import obter
from . import catalog, extract, index

log = obter("biblioteca")

MSG_DUPLICADO = "Este documento já está na sua biblioteca."
MSG_SEM_TEXTO = "Este PDF parece ser digitalizado como imagem. O conteúdo não pôde ser lido."
MSG_CORROMPIDO = "Não foi possível processar este arquivo. Os demais documentos continuam disponíveis."
MSG_FORMATO = "Formato não aceito. Use PDF, DOCX, TXT ou MD."


@dataclass
class ResultadoIngestao:
    ok: bool
    mensagem: str
    documento: Optional[catalog.Documento] = None
    duplicado: bool = False
    sem_texto: bool = False


def adicionar(caminhos: Caminhos, origem: Path, nome_original: Optional[str] = None, fuso: Optional[str] = None, indexar: bool = True) -> ResultadoIngestao:
    origem = Path(origem)
    nome = nome_original or origem.name
    if not extract.formato_valido(nome):
        return ResultadoIngestao(False, MSG_FORMATO)
    ext = Path(nome).suffix.lower().lstrip(".")
    try:
        sha = sha256_arquivo(origem)
    except OSError as e:
        log.warning("hash falhou: %s", e)
        return ResultadoIngestao(False, MSG_CORROMPIDO)

    cat = catalog.ler(caminhos)
    existente = cat.por_hash(sha)
    if existente is not None:
        return ResultadoIngestao(False, MSG_DUPLICADO, existente, duplicado=True)

    destino = caminhos.arquivo_biblioteca(sha, ext)
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(origem, destino)
    except OSError as e:
        log.warning("cópia falhou: %s", e)
        return ResultadoIngestao(False, MSG_CORROMPIDO)

    doc = catalog.Documento(
        hash=sha, nome_original=nome, extensao=ext, data_inclusao=dates.iso_agora(fuso), tamanho_bytes=destino.stat().st_size
    )
    invalido = False
    try:
        extracao = extract.extrair(destino)
    except extract.SemTexto:
        doc.sem_texto = True
        doc.titulo = Path(nome).stem.replace("_", " ")
        cat.documentos.append(doc)
        catalog.gravar(caminhos, cat)
        return ResultadoIngestao(True, MSG_SEM_TEXTO, doc, sem_texto=True)
    except extract.ArquivoInvalido as e:
        # str(e): não passar o objeto da exceção ao log (o traceback manteria o leitor de PDF aberto)
        log.warning("arquivo inválido %s: %s", nome, str(e))
        invalido = True
    if invalido:
        # fora do bloco except: o traceback (que mantém o leitor de PDF aberto no Windows) já foi liberado
        _remover_com_retentativa(destino)
        return ResultadoIngestao(False, MSG_CORROMPIDO)

    trechos = extract.dividir_em_trechos(extracao)
    for i, t in enumerate(trechos):
        t["id"] = f"{sha[:12]}-{i:04d}"
    catalog.gravar_trechos(caminhos, sha, trechos)
    meta = extract.detectar_metadados(extracao, nome)
    doc.titulo = meta.get("titulo", "") or Path(nome).stem
    doc.autor = meta.get("autor", "")
    doc.ano = meta.get("ano", "")
    doc.categoria = meta.get("categoria", "outros")
    doc.instrumento = meta.get("instrumento", "")
    doc.paginas = extracao.n_paginas
    doc.n_trechos = len(trechos)
    cat.documentos.append(doc)
    catalog.gravar(caminhos, cat)
    if indexar:
        index.atualizar(caminhos, cat, fuso)
    return ResultadoIngestao(True, f"Documento adicionado: {doc.titulo} ({doc.n_trechos} trechos).", doc)


def _remover_com_retentativa(caminho: Path, tentativas: int = 3) -> bool:
    import gc
    import time

    for i in range(tentativas):
        try:
            if caminho.exists():
                caminho.unlink()
            return True
        except OSError:
            gc.collect()
            time.sleep(0.2 * (i + 1))
    log.warning("não foi possível remover %s", caminho.name)
    return False


def remover(caminhos: Caminhos, sha: str) -> list:
    """Remove arquivo, texto e entradas do índice. Devolve lista do que foi apagado."""
    cat = catalog.ler(caminhos)
    doc = cat.por_hash(sha)
    apagados = []
    if doc is None:
        return apagados
    arq = caminhos.arquivo_biblioteca(sha, doc.extensao)
    for p in [arq, caminhos.texto_biblioteca(sha)]:
        if p.exists():
            p.unlink()
            apagados.append(str(p.relative_to(caminhos.base)))
        bak = p.with_name(p.name + ".bak")
        if bak.exists():
            bak.unlink()
    n = index.remover_documento(caminhos, sha)
    if n:
        apagados.append(f"{n} trecho(s) do índice")
    try:
        from . import embeddings

        n2 = embeddings.remover_documento(caminhos, sha)
        if n2:
            apagados.append(f"{n2} vetor(es) do índice semântico")
    except Exception:  # noqa: BLE001
        pass
    cat.documentos = [d for d in cat.documentos if d.hash != sha]
    catalog.gravar(caminhos, cat)
    return apagados


def descrever_remocao(caminhos: Caminhos, sha: str) -> list:
    cat = catalog.ler(caminhos)
    doc = cat.por_hash(sha)
    if doc is None:
        return []
    itens = [f"biblioteca/arquivos/{sha}.{doc.extensao}"]
    if not doc.sem_texto:
        itens.append(f"biblioteca/texto/{sha}.json")
        itens.append(f"{doc.n_trechos} trecho(s) do índice de busca")
    return itens


def atualizar_metadados(caminhos: Caminhos, sha: str, **campos) -> Optional[catalog.Documento]:
    cat = catalog.ler(caminhos)
    doc = cat.por_hash(sha)
    if doc is None:
        return None
    for k, v in campos.items():
        if hasattr(doc, k) and v is not None:
            setattr(doc, k, v)
    catalog.gravar(caminhos, cat)
    return doc
