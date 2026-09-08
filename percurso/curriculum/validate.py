"""Validação de habilidades curriculares (SPEC §10.2).

código existe? → etapa compatível com o registro? → componente = Arte (ou EI/Linguagens-Arte)? → relação com Música? → usar
Qualquer código que falhe é removido e registrado no log.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..core.models import Registro
from ..utils.logging import obter
from . import bncc, crmg

log = obter("curriculo")

COMPONENTES_ACEITOS = {"Arte", "Educação Infantil", "Linguagens e suas Tecnologias"}


@dataclass
class ResultadoValidacao:
    validos: List[str] = field(default_factory=list)
    removidos: List[Tuple[str, str]] = field(default_factory=list)  # (código, motivo)

    @property
    def mensagem_professor(self) -> str:
        n = len(self.removidos)
        if n == 0:
            return ""
        return f"{n} habilidade{'s' if n > 1 else ''} sugerida{'s' if n > 1 else ''} não foi validada e foi removida" if n == 1 else f"{n} habilidades sugeridas não foram validadas e foram removidas"


def etapa_do_registro(registro: Optional[Registro]) -> Optional[str]:
    """EI / EF / EM inferida da idade (ou faixa etária da turma). None = não inferível (não restringe)."""
    if registro is None:
        return None
    idade = registro.idade
    if idade is None and registro.turma and registro.turma.faixa_etaria:
        import re

        m = re.search(r"\d+", registro.turma.faixa_etaria)
        idade = int(m.group()) if m else None
    if idade is None:
        return None
    if idade <= 5:
        return "EI"
    if idade <= 14:
        return "EF"
    if idade <= 18:
        return "EM"
    return None


def _idade(registro: Optional[Registro]) -> Optional[int]:
    if registro is None:
        return None
    if registro.idade is not None:
        return registro.idade
    if registro.turma and registro.turma.faixa_etaria:
        import re

        m = re.search(r"\d+", registro.turma.faixa_etaria)
        return int(m.group()) if m else None
    return None


def ano_do_registro(registro: Optional[Registro]) -> Optional[str]:
    """Ano escolar aproximado pela idade (6 anos → 1º … 14 anos → 9º; 15–17 → EM 1–3). None = não restringe."""
    idade = _idade(registro)
    if idade is None:
        return None
    if 6 <= idade <= 14:
        return str(idade - 5)
    if 15 <= idade <= 17:
        return str(idade - 14)
    return None


def anos_compativeis(h: bncc.Habilidade, registro: Optional[Registro]) -> bool:
    ano = ano_do_registro(registro)
    if ano is None or h.etapa == "EI" or not h.anos:
        return True
    return ano in h.anos


def base_para(registro: Optional[Registro]) -> Dict[str, bncc.Habilidade]:
    """BNCC sempre; CRMG acrescenta quando o registro pede bncc_crmg."""
    todas = bncc.todas_bncc()
    if registro is not None and registro.curriculo == "bncc_crmg":
        for cod, h in crmg.todas_crmg().items():
            todas.setdefault(cod, h)
    return todas


def validar_codigo(codigo: str, registro: Optional[Registro] = None, exigir_musica: bool = True) -> Tuple[bool, str]:
    cod = (codigo or "").strip().upper()
    base = base_para(registro)
    h = base.get(cod)
    if h is None:
        return False, "código inexistente"
    etapa = etapa_do_registro(registro)
    if etapa and h.etapa != etapa:
        return False, f"etapa {h.etapa} incompatível com o registro ({etapa})"
    if not anos_compativeis(h, registro):
        return False, f"anos {h.anos[0]}º–{h.anos[-1]}º incompatíveis com o registro ({ano_do_registro(registro)}º ano)"
    if h.componente not in COMPONENTES_ACEITOS:
        return False, f"componente {h.componente} não é Arte"
    if exigir_musica and not h.musica:
        return False, "habilidade sem relação com Música"
    return True, ""


def validar_lista(codigos: List[str], registro: Optional[Registro] = None, exigir_musica: bool = True) -> ResultadoValidacao:
    r = ResultadoValidacao()
    vistos = set()
    for c in codigos or []:
        cod = (c or "").strip().upper()
        if not cod or cod in vistos:
            continue
        vistos.add(cod)
        ok, motivo = validar_codigo(cod, registro, exigir_musica)
        if ok:
            r.validos.append(cod)
        else:
            r.removidos.append((cod, motivo))
            log.info("habilidade rejeitada: %s (%s)", cod, motivo)
    return r
