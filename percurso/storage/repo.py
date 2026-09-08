"""Repositório: leitura e escrita de todas as entidades em <base_path> (SPEC §4).

JSON é a fonte de verdade (D4). Leitura por glob. Escrita sempre atômica e imediata (§3.4).
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel

from ..core import codes
from ..core.models import (
    Apoio,
    Aula,
    EstadoAtual,
    Plano,
    Professor,
    Registro,
    Repertorio,
    ResumoPedagogico,
    Rubricas,
    Versao,
)
from ..utils import dates
from ..utils.hashing import id_curto
from .atomic import copiar_pasta_backup, escrever_json, ler_json
from .paths import Caminhos


class RegistroNaoEncontrado(Exception):
    pass


def _validador(modelo: type[BaseModel]) -> Callable:
    def _v(obj):
        modelo.model_validate(obj)

    return _v


class Repositorio:
    def __init__(self, base_path: Path):
        self.caminhos = Caminhos(Path(base_path))
        self.caminhos.criar_estrutura()

    # ------------------------------------------------------------------ util
    @property
    def base(self) -> Path:
        return self.caminhos.base

    def _gravar(self, caminho: Path, modelo: BaseModel) -> None:
        if not self.caminhos.dentro_da_base(caminho):
            raise PermissionError("Tentativa de escrita fora da pasta Percurso.")
        escrever_json(caminho, modelo.model_dump(mode="json"), validador=_validador(type(modelo)))

    def _fuso(self) -> str:
        try:
            return self.ler_professor().fuso_horario or dates.FUSO_PADRAO
        except Exception:
            return dates.FUSO_PADRAO

    def agora_iso(self) -> str:
        return dates.iso_agora(self._fuso())

    # ------------------------------------------------------------ professor
    def ler_professor(self) -> Professor:
        dados = ler_json(self.caminhos.professor, None)
        return Professor.model_validate(dados) if dados else Professor()

    def gravar_professor(self, professor: Professor) -> Professor:
        if not professor.criado_em:
            professor.criado_em = dates.iso_agora(professor.fuso_horario)
        professor.atualizado_em = dates.iso_agora(professor.fuso_horario)
        self._gravar(self.caminhos.professor, professor)
        return professor

    def professor_existe(self) -> bool:
        return self.caminhos.professor.exists()

    # -------------------------------------------------------------- versão
    def ler_versao(self) -> Optional[Versao]:
        dados = ler_json(self.caminhos.versao, None)
        return Versao.model_validate(dados) if dados else None

    def gravar_versao(self, versao: Versao) -> None:
        versao.atualizado_em = self.agora_iso()
        self._gravar(self.caminhos.versao, versao)

    # --------------------------------------------------------------- apoio
    def ler_apoio(self) -> Apoio:
        dados = ler_json(self.caminhos.apoio, None)
        return Apoio.model_validate(dados) if dados else Apoio()

    def gravar_apoio(self, apoio: Apoio) -> None:
        self._gravar(self.caminhos.apoio, apoio)

    # ------------------------------------------------------------ rubricas
    def ler_rubricas(self) -> Rubricas:
        dados = ler_json(self.caminhos.rubricas, None)
        return Rubricas.model_validate(dados) if dados else Rubricas()

    def gravar_rubricas(self, rubricas: Rubricas) -> None:
        self._gravar(self.caminhos.rubricas, rubricas)

    # ------------------------------------------------------------ registros
    def listar_codigos(self) -> List[str]:
        if not self.caminhos.registros.exists():
            return []
        return sorted(
            p.name for p in self.caminhos.registros.iterdir() if p.is_dir() and (p / "perfil.json").exists()
        )

    def registro_existe(self, codigo: str) -> bool:
        return self.caminhos.perfil(codigo).exists()

    def novo_codigo(self) -> str:
        return codes.gerar(existe=lambda c: self.caminhos.registro(c).exists())

    def criar_registro(self, registro: Registro) -> Registro:
        if not registro.codigo:
            registro.codigo = self.novo_codigo()
        registro.codigo = codes.normalizar_e_validar(registro.codigo)
        if self.registro_existe(registro.codigo):
            raise ValueError(f"O código {registro.codigo} já existe.")
        agora = self.agora_iso()
        registro.criado_em = registro.criado_em or agora
        registro.atualizado_em = agora
        pasta = self.caminhos.registro(registro.codigo)
        for sub in ["aulas", "planos", "materiais"]:
            (pasta / sub).mkdir(parents=True, exist_ok=True)
        self._gravar(self.caminhos.perfil(registro.codigo), registro)
        self.gravar_estado(registro.codigo, EstadoAtual(atualizado_em=agora))
        self.gravar_resumo(registro.codigo, ResumoPedagogico(atualizado_em=agora))
        self.gravar_repertorio(registro.codigo, Repertorio())
        return registro

    def ler_registro(self, codigo: str) -> Registro:
        codigo = codes.normalizar_e_validar(codigo)
        dados = ler_json(self.caminhos.perfil(codigo), None)
        if not dados:
            raise RegistroNaoEncontrado(codigo)
        return Registro.model_validate(dados)

    def gravar_registro(self, registro: Registro) -> Registro:
        registro.atualizado_em = self.agora_iso()
        self._gravar(self.caminhos.perfil(registro.codigo), registro)
        return registro

    # ---------------------------------------------------------------- aulas
    def listar_aulas(self, codigo: str, incluir_canceladas: bool = True) -> List[Aula]:
        pasta = self.caminhos.aulas(codigo)
        aulas: List[Aula] = []
        if pasta.exists():
            for arq in sorted(pasta.glob("*.json")):
                dados = ler_json(arq, None)
                if dados:
                    aulas.append(Aula.model_validate(dados))
        aulas.sort(key=lambda a: (a.data, a.criado_em, a.id))
        if not incluir_canceladas:
            aulas = [a for a in aulas if not a.cancelada]
        return aulas

    def numerar_aulas(self, codigo: str) -> List[tuple]:
        """[(numero, aula)] — numeração derivada por data, excluindo canceladas (SPEC §4.3)."""
        numeradas = []
        n = 0
        for a in self.listar_aulas(codigo):
            if a.cancelada:
                numeradas.append((0, a))
            else:
                n += 1
                numeradas.append((n, a))
        return numeradas

    def numero_da_aula(self, codigo: str, id_aula: str) -> int:
        for n, a in self.numerar_aulas(codigo):
            if a.id == id_aula:
                return n
        return 0

    def ler_aula(self, codigo: str, id_aula: str) -> Aula:
        for a in self.listar_aulas(codigo):
            if a.id == id_aula:
                return a
        raise FileNotFoundError(f"Aula {id_aula} não encontrada em {codigo}.")

    def novo_id_aula(self, codigo: str, data: str) -> str:
        existentes = {a.id for a in self.listar_aulas(codigo)}
        base = f"{codigo}|{data}|{self.agora_iso()}"
        i = 0
        while True:
            cand = id_curto(f"{base}|{i}")
            if cand not in existentes:
                return cand
            i += 1

    def gravar_aula(self, codigo: str, aula: Aula) -> Aula:
        if not aula.id:
            aula.id = self.novo_id_aula(codigo, aula.data)
        agora = self.agora_iso()
        aula.criado_em = aula.criado_em or agora
        aula.atualizado_em = agora
        if not aula.dia_semana:
            aula.dia_semana = dates.dia_semana(dates.parse_data(aula.data))
        # se a data mudou, remove o arquivo antigo com o mesmo id
        pasta = self.caminhos.aulas(codigo)
        pasta.mkdir(parents=True, exist_ok=True)
        for antigo in pasta.glob(f"*_{aula.id}.json"):
            if antigo.name != aula.nome_arquivo():
                antigo.unlink()
        self._gravar(pasta / aula.nome_arquivo(), aula)
        return aula

    def excluir_aula(self, codigo: str, id_aula: str) -> bool:
        pasta = self.caminhos.aulas(codigo)
        removido = False
        for arq in pasta.glob(f"*_{id_aula}.json"):
            arq.unlink()
            removido = True
        for extra in pasta.glob(f"*_{id_aula}.json.bak"):
            extra.unlink()
        return removido

    # --------------------------------------------------------------- estado
    def ler_estado(self, codigo: str) -> EstadoAtual:
        dados = ler_json(self.caminhos.estado_atual(codigo), None)
        return EstadoAtual.model_validate(dados) if dados else EstadoAtual()

    def gravar_estado(self, codigo: str, estado: EstadoAtual) -> None:
        estado.atualizado_em = self.agora_iso()
        self._gravar(self.caminhos.estado_atual(codigo), estado)

    def ler_resumo(self, codigo: str) -> ResumoPedagogico:
        dados = ler_json(self.caminhos.resumo_pedagogico(codigo), None)
        return ResumoPedagogico.model_validate(dados) if dados else ResumoPedagogico()

    def gravar_resumo(self, codigo: str, resumo: ResumoPedagogico) -> None:
        resumo.atualizado_em = self.agora_iso()
        self._gravar(self.caminhos.resumo_pedagogico(codigo), resumo)

    # ----------------------------------------------------------- repertório
    def ler_repertorio(self, codigo: str) -> Repertorio:
        dados = ler_json(self.caminhos.repertorio(codigo), None)
        return Repertorio.model_validate(dados) if dados else Repertorio()

    def gravar_repertorio(self, codigo: str, rep: Repertorio) -> None:
        self._gravar(self.caminhos.repertorio(codigo), rep)

    # --------------------------------------------------------------- planos
    def listar_planos(self, codigo: str) -> List[Plano]:
        pasta = self.caminhos.planos(codigo)
        planos: List[Plano] = []
        if pasta.exists():
            for arq in sorted(pasta.glob("*.json")):
                dados = ler_json(arq, None)
                if dados:
                    planos.append(Plano.model_validate(dados))
        planos.sort(key=lambda p: (p.data, p.criado_em))
        return planos

    def ler_plano(self, codigo: str, id_plano: str) -> Plano:
        for p in self.listar_planos(codigo):
            if p.id == id_plano:
                return p
        raise FileNotFoundError(f"Plano {id_plano} não encontrado.")

    def gravar_plano(self, plano: Plano) -> Plano:
        if not plano.id:
            plano.id = id_curto(f"{plano.codigo_registro}|{plano.data}|{self.agora_iso()}|plano")
        plano.criado_em = plano.criado_em or self.agora_iso()
        pasta = self.caminhos.planos(plano.codigo_registro)
        pasta.mkdir(parents=True, exist_ok=True)
        self._gravar(pasta / plano.nome_arquivo(), plano)
        return plano

    def caminho_relativo_plano(self, plano: Plano) -> str:
        return f"planos/{plano.nome_arquivo()}"

    # ------------------------------------------------------ perfis editados
    def ler_perfil_editado(self, instrumento: str) -> Optional[dict]:
        return ler_json(self.caminhos.perfil_editado(instrumento), None)

    def gravar_perfil_editado(self, instrumento: str, perfil: dict) -> None:
        escrever_json(self.caminhos.perfil_editado(instrumento), perfil)

    def remover_perfil_editado(self, instrumento: str) -> bool:
        p = self.caminhos.perfil_editado(instrumento)
        if p.exists():
            p.unlink()
            return True
        return False

    # ------------------------------------------------------ LGPD / backups
    def backup_pasta(self, origem: Path, motivo: str) -> Path:
        return copiar_pasta_backup(origem, self.caminhos.backups, dates.carimbo_arquivo(self._fuso()), motivo)

    def excluir_registro(self, codigo: str) -> Path:
        """Exclui o registro criando backup em backups/ (SPEC §14.5). Devolve a pasta do backup."""
        codigo = codes.normalizar_e_validar(codigo)
        pasta = self.caminhos.registro(codigo)
        if not pasta.exists():
            raise RegistroNaoEncontrado(codigo)
        destino = self.backup_pasta(pasta, f"exclusao-{codigo}")
        shutil.rmtree(pasta)
        return destino

    def descrever_exclusao_registro(self, codigo: str) -> List[str]:
        pasta = self.caminhos.registro(codigo)
        if not pasta.exists():
            return []
        itens = []
        for p in sorted(pasta.rglob("*")):
            if p.is_file() and not p.name.endswith((".bak", ".tmp")):
                itens.append(str(p.relative_to(pasta)))
        return itens

    def exportar_zip(self, destino: Path, apenas_registro: Optional[str] = None) -> Path:
        """Zip de Percurso/ inteiro ou de um registro."""
        raiz = self.caminhos.registro(apenas_registro) if apenas_registro else self.base
        destino.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for p in raiz.rglob("*"):
                if p.is_file() and not p.name.endswith((".tmp",)):
                    if apenas_registro is None and self.caminhos.backups in p.parents:
                        continue
                    if apenas_registro is None and p.resolve() == destino.resolve():
                        continue
                    z.write(p, p.relative_to(raiz.parent if apenas_registro else self.base.parent))
        return destino

    def listar_backups(self) -> List[str]:
        if not self.caminhos.backups.exists():
            return []
        return sorted(p.name for p in self.caminhos.backups.iterdir() if p.is_dir())

    def remover_backup(self, nome: str) -> bool:
        p = self.caminhos.backups / nome
        if p.exists() and self.caminhos.dentro_da_base(p) and p.parent == self.caminhos.backups:
            shutil.rmtree(p)
            return True
        return False

    def estatisticas(self) -> Dict[str, int]:
        cods = self.listar_codigos()
        return {
            "registros": len(cods),
            "aulas": sum(len(self.listar_aulas(c)) for c in cods),
        }
