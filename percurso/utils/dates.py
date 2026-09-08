"""Datas e horários. Fuso padrão America/Sao_Paulo via zoneinfo (SPEC §13.4)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

FUSO_PADRAO = "America/Sao_Paulo"

DIAS_SEMANA = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
DIAS_SEMANA_NOME = {
    "segunda": "Segunda-feira",
    "terca": "Terça-feira",
    "quarta": "Quarta-feira",
    "quinta": "Quinta-feira",
    "sexta": "Sexta-feira",
    "sabado": "Sábado",
    "domingo": "Domingo",
}


def fuso(nome: Optional[str] = None) -> ZoneInfo:
    try:
        return ZoneInfo(nome or FUSO_PADRAO)
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        return ZoneInfo("UTC")


def agora(nome_fuso: Optional[str] = None) -> datetime:
    return datetime.now(fuso(nome_fuso))


def hoje(nome_fuso: Optional[str] = None) -> date:
    return agora(nome_fuso).date()


def mes_atual(nome_fuso: Optional[str] = None, referencia: Optional[datetime] = None) -> str:
    """Devolve 'YYYY-MM' no fuso configurado."""
    dt = referencia if referencia is not None else agora(nome_fuso)
    if dt.tzinfo is not None:
        dt = dt.astimezone(fuso(nome_fuso))
    return dt.strftime("%Y-%m")


def iso_agora(nome_fuso: Optional[str] = None) -> str:
    return agora(nome_fuso).isoformat(timespec="seconds")


def dia_semana(d: date) -> str:
    return DIAS_SEMANA[d.weekday()]


def formatar_data_br(d) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d.strftime("%d/%m/%Y")


def parse_data(texto: str) -> date:
    """Aceita 'YYYY-MM-DD' ou 'DD/MM/YYYY'."""
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("Data vazia.")
    if "/" in texto:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    return date.fromisoformat(texto)


def parse_hora(texto: str) -> time:
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("Horário vazio.")
    if ":" not in texto:
        texto = f"{texto}:00"
    h, m = texto.split(":")[:2]
    return time(int(h), int(m))


def minutos_entre(inicio: str, termino: str) -> int:
    """Duração em minutos entre 'HH:MM' e 'HH:MM'. Passagem de meia-noite tratada."""
    a = parse_hora(inicio)
    b = parse_hora(termino)
    delta = (b.hour * 60 + b.minute) - (a.hour * 60 + a.minute)
    if delta < 0:
        delta += 24 * 60
    return delta


def somar_minutos(inicio: str, minutos: int) -> str:
    a = parse_hora(inicio)
    dt = datetime.combine(date(2000, 1, 1), a) + timedelta(minutes=minutos)
    return dt.strftime("%H:%M")


def carimbo_arquivo(nome_fuso: Optional[str] = None) -> str:
    """Formato '2026-09-06T10-15' para nomes de pasta de backup."""
    return agora(nome_fuso).strftime("%Y-%m-%dT%H-%M")
