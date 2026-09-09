"""Lembrete mensal de apoio (caso 15) e QR Code."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from percurso.support import donations


def _dt(y, m, d, h=12, fuso="America/Sao_Paulo"):
    return datetime(y, m, d, h, 0, tzinfo=ZoneInfo(fuso))


def test_lembrete_uma_vez_por_mes(repo):
    fuso = "America/Sao_Paulo"
    assert donations.verificar_e_marcar(repo, fuso, _dt(2026, 10, 1)) is True
    assert repo.ler_apoio().ultimo_mes_lembrete_apoio == "2026-10"  # gravado ANTES de exibir
    assert donations.verificar_e_marcar(repo, fuso, _dt(2026, 10, 2)) is False
    assert donations.verificar_e_marcar(repo, fuso, _dt(2026, 10, 20)) is False
    assert donations.verificar_e_marcar(repo, fuso, _dt(2026, 11, 8)) is True  # primeira abertura de novembro
    # não abriu em novembro (já marcado), volta em 15/12
    assert donations.verificar_e_marcar(repo, fuso, _dt(2026, 12, 15)) is True
    assert donations.verificar_e_marcar(repo, fuso, _dt(2026, 12, 31, 23)) is False


def test_lembrete_respeita_fuso(repo):
    # 31/10 23:30 em São Paulo ainda é outubro, embora seja 1º/11 em UTC
    instante = datetime(2026, 11, 1, 2, 30, tzinfo=ZoneInfo("UTC"))
    assert donations.verificar_e_marcar(repo, "America/Sao_Paulo", instante) is True
    assert repo.ler_apoio().ultimo_mes_lembrete_apoio == "2026-10"
    # já em novembro no fuso local → aparece de novo
    assert donations.verificar_e_marcar(repo, "America/Sao_Paulo", datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("UTC"))) is True


def test_qr_png(tmp_path):
    dados = donations.gerar_qr_png("https://link.mercadopago.com.br/teste")
    assert dados[:8] == b"\x89PNG\r\n\x1a\n"
    p = donations.salvar_qr("PCR-ABC234", tmp_path / "qr.png")
    assert p.exists() and p.stat().st_size > 100


def test_link_configurado():
    assert not donations.link_configurado("https://link.mercadopago.com.br/________")
    assert donations.link_configurado("https://link.mercadopago.com.br/percurso")
    assert not donations.link_configurado("")


def test_link_salvo_persiste_e_nao_aceita_segredos(repo):
    import pytest
    from percurso.storage.repo import Repositorio
    valor = 'https://link.mercadopago.com.br/percurso'
    assert donations.salvar_link(repo, valor) == valor
    assert donations.obter_link(Repositorio(repo.base)) == valor
    for invalido in ['APP_USR-token-teste', 'https://link.mercadopago.com.br.evil.test/pagar', 'http://mpago.la/exemplo', 'https://usuario@mpago.la/teste', 'javascript:alert(1)']:
        with pytest.raises(ValueError): donations.salvar_link(repo, invalido)
    assert donations.obter_link(repo) == valor


def test_qr_muda_quando_link_muda(sessao):
    from percurso.ui.screens.apoio import _qr_path
    a = _qr_path(sessao, 'https://mpago.la/primeiro')
    b = _qr_path(sessao, 'https://mpago.la/segundo')
    assert a != b and a.exists() and b.exists()
    assert a.read_bytes() != b.read_bytes()


def test_tela_apoio_atualiza_link_e_qr(sessao):
    import gradio as gr
    from percurso.ui.screens import apoio
    with gr.Blocks() as demo:
        apoio.montar(sessao)
    evento = next(f for f in demo.fns.values() if f.fn and f.fn.__name__ == 'salvar_configuracao')
    url = 'https://link.mercadopago.com.br/percurso'
    saida = evento.fn(url)
    assert saida[1]['visible'] and saida[2]['link'] == url
    assert donations.obter_link(sessao.repo) == url
    with gr.Blocks():
        tela = apoio.montar(sessao)
    assert tela['configurado']
