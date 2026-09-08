"""Apoio ao projeto (SPEC §13): link público do Mercado Pago, QR Code e lembrete mensal.

Regra do lembrete: uma única vez por mês-calendário, na primeira abertura efetiva do mês,
no fuso configurado. Grava-se o mês ANTES de exibir.
"""
from __future__ import annotations

import io
from urllib.parse import urlsplit

from ..storage.atomic import ler_json, escrever_json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from ..core.models import Apoio
from ..utils import dates

FINALIDADES = [
    "novos recursos",
    "manutenção",
    "expansão para outras áreas",
    "melhoria da biblioteca pedagógica",
    "evolução da plataforma",
]

TEXTO_LEMBRETE_TITULO = "Ajude o Percurso a continuar crescendo."
TEXTO_LEMBRETE_CORPO = (
    "O Percurso é desenvolvido de forma independente e permanece gratuito. "
    "Se a ferramenta tem contribuído para seu trabalho, considere apoiar sua manutenção "
    "e o desenvolvimento de novos recursos."
)
TEXTO_LEMBRETE_RODAPE = "Nenhuma função será bloqueada."


def link_configurado(link: Optional[str]) -> bool:
    if not isinstance(link, str) or not link or "________" in link or any(c.isspace() for c in link):
        return False
    try:
        u = urlsplit(link)
        return (u.scheme == "https" and u.hostname in {"link.mercadopago.com.br", "www.mercadopago.com.br", "mercadopago.com.br", "mpago.la"}
                and not u.username and not u.password and u.port in (None, 443) and bool(u.path.strip("/")))
    except ValueError:
        return False


def obter_link(repo) -> str:
    from .. import config
    dados = ler_json(repo.caminhos.configuracoes / "link_apoio.json", {})
    return dados.get("link", "") or config.link_apoio()


def salvar_link(repo, link: str) -> str:
    valor = (link or "").strip()
    if valor and not link_configurado(valor):
        raise ValueError("Cole um link público HTTPS do Mercado Pago. Não informe chave de API, senha ou chave Pix.")
    escrever_json(repo.caminhos.configuracoes / "link_apoio.json", {"link": valor})
    return obter_link(repo)


def gerar_qr_png(conteudo: str, tamanho_caixa: int = 8) -> bytes:
    """PNG do QR Code (qrcode + Pillow)."""
    import qrcode

    qr = qrcode.QRCode(box_size=tamanho_caixa, border=2)
    qr.add_data(conteudo)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1f2937", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def salvar_qr(conteudo: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(gerar_qr_png(conteudo))
    return destino


def deve_mostrar_lembrete(apoio: Apoio, fuso: str, agora: Optional[datetime] = None) -> Tuple[bool, str]:
    """(mostrar?, mes_atual). Não grava nada."""
    mes = dates.mes_atual(fuso, referencia=agora)
    return (apoio.ultimo_mes_lembrete_apoio != mes), mes


def verificar_e_marcar(repo, fuso: str, agora: Optional[datetime] = None) -> bool:
    """Verifica o lembrete e, se for o caso, GRAVA o mês antes de devolver True (SPEC §13.4)."""
    apoio = repo.ler_apoio()
    mostrar, mes = deve_mostrar_lembrete(apoio, fuso, agora)
    if mostrar:
        apoio.ultimo_mes_lembrete_apoio = mes
        repo.gravar_apoio(apoio)
    return mostrar
