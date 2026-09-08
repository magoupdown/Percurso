"""Migração v0 → v1.

v0 = arquivos sem `schema_version` (formato da especificação v1 do Percurso), com
`nome` no lugar de `identificacao`, `aluno` no lugar de `codigo` e aulas sem `classificacao_conteudos`.
Nenhum campo é perdido: o que o modelo v1 não conhece vai para `_extra`.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ...core.models import Aula, Registro
from ..atomic import escrever_json, ler_json

RENOMEIOS_REGISTRO = {"nome": "identificacao", "aluno": "identificacao", "instrumento_id": "instrumento"}
RENOMEIOS_AULA = {"conteudo": "conteudo_realizado", "conteudos": "conteudo_realizado", "presenca": "frequencia"}


def _mover_desconhecidos(dados: Dict[str, Any], modelo) -> Dict[str, Any]:
    conhecidos = set(modelo.model_fields.keys())
    extra = dict(dados.get("_extra") or {})
    saida: Dict[str, Any] = {}
    for k, v in dados.items():
        if k == "_extra":
            continue
        if k in conhecidos:
            saida[k] = v
        else:
            extra[k] = v
    if extra:
        saida["_extra"] = extra
    return saida


def _migrar_registro(dados: Dict[str, Any], codigo: str) -> Dict[str, Any]:
    d = dict(dados)
    for antigo, novo in RENOMEIOS_REGISTRO.items():
        if antigo in d and novo not in d:
            d[novo] = d.pop(antigo)
    d.setdefault("codigo", codigo)
    d["schema_version"] = 1
    if isinstance(d.get("frequencia"), str):
        pass
    return _mover_desconhecidos(d, Registro)


def _migrar_aula(dados: Dict[str, Any], nome_arquivo: str) -> Dict[str, Any]:
    d = dict(dados)
    for antigo, novo in RENOMEIOS_AULA.items():
        if antigo in d and novo not in d:
            d[novo] = d.pop(antigo)
    if isinstance(d.get("conteudo_realizado"), str):
        d["conteudo_realizado"] = [x.strip() for x in d["conteudo_realizado"].split(",") if x.strip()]
    if "id" not in d:
        base = nome_arquivo[:-5]
        d["id"] = base.split("_")[-1] if "_" in base else base[-4:]
    if "data" not in d:
        d["data"] = nome_arquivo[:10]
    if d.get("frequencia") in (True, "sim", "presente"):
        d["frequencia"] = "presente"
    elif d.get("frequencia") in (False, "nao", "não", "falta"):
        d["frequencia"] = "falta"
    d["schema_version"] = 1
    return _mover_desconhecidos(d, Aula)


def migrar(repo) -> List[str]:
    acoes: List[str] = []
    pasta = repo.caminhos.registros
    if not pasta.exists():
        return acoes
    for reg in sorted(p for p in pasta.iterdir() if p.is_dir()):
        perfil = reg / "perfil.json"
        if perfil.exists():
            dados = ler_json(perfil, {}) or {}
            if int(dados.get("schema_version", 0)) < 1:
                novo = _migrar_registro(dados, reg.name)
                Registro.model_validate(novo)
                escrever_json(perfil, novo)
                acoes.append(f"registro {reg.name} migrado para v1")
        aulas = reg / "aulas"
        if aulas.exists():
            for arq in sorted(aulas.glob("*.json")):
                dados = ler_json(arq, {}) or {}
                if int(dados.get("schema_version", 0)) < 1:
                    novo = _migrar_aula(dados, arq.name)
                    Aula.model_validate(novo)
                    escrever_json(arq, novo)
                    acoes.append(f"aula {reg.name}/{arq.name} migrada para v1")
        for sub in ["planos", "materiais"]:
            (reg / sub).mkdir(exist_ok=True)
        for nome in ["estado_atual.json", "resumo_pedagogico.json", "repertorio.json"]:
            arq = reg / nome
            if arq.exists():
                dados = ler_json(arq, {}) or {}
                if int(dados.get("schema_version", 0)) < 1:
                    dados["schema_version"] = 1
                    escrever_json(arq, dados)
    return acoes
