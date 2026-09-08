"""Configurações (SPEC §6.7, §14.5): perfil, perfis instrumentais, rubricas, privacidade, diagnóstico, backups."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import gradio as gr

from ...core import codes
from ...core.models import Professor, Rubricas
from ...domains import limpar_cache
from ...utils import dates
from ...utils.logging import ultimas_linhas
from .. import common as C
from .. import texts as T
from ..session import Sessao

FUSOS = ["America/Sao_Paulo", "America/Manaus", "America/Belem", "America/Fortaleza", "America/Recife", "America/Bahia", "America/Cuiaba", "America/Campo_Grande", "America/Rio_Branco", "America/Noronha", "America/Boa_Vista", "America/Porto_Velho", "America/Araguaina", "America/Maceio", "UTC"]


def montar(sessao: Sessao) -> dict:
    prof = sessao.repo.ler_professor()
    with gr.Tab(T.ABA_CONFIG, id="config") as tab:
        gr.Markdown(f"## {T.CONFIG_TITULO}")
        # ------------------------------------------------------- perfil
        with gr.Accordion(T.CONFIG_PERFIL, open=not prof.onboarding_concluido):
            with gr.Row():
                nome = gr.Textbox(label=T.CONFIG_NOME, value=prof.nome)
                instituicao = gr.Textbox(label=T.CONFIG_INSTITUICAO, value=prof.instituicao)
            with gr.Row():
                cidade = gr.Textbox(label=T.CONFIG_CIDADE, value=prof.cidade)
                estado = gr.Textbox(label=T.CONFIG_ESTADO, value=prof.estado, max_lines=1)
                area = gr.Dropdown(label=T.CONFIG_AREA, choices=C.opcoes_instrumentos(sessao), value=prof.area_principal or None, allow_custom_value=True)
            niveis = gr.CheckboxGroup(label=T.CONFIG_NIVEIS, choices=T.NIVEIS_ENSINO, value=prof.niveis_ensino)
            with gr.Row():
                duracao = gr.Number(label=T.CONFIG_DURACAO, value=prof.duracao_padrao_min, precision=0, minimum=5, maximum=300)
                curriculo = gr.Dropdown(label=T.CONFIG_CURRICULO, choices=T.opcoes(T.CURRICULOS), value=prof.curriculo_padrao)
                fuso = gr.Dropdown(label=T.CONFIG_FUSO, choices=FUSOS, value=prof.fuso_horario if prof.fuso_horario in FUSOS else "America/Sao_Paulo", allow_custom_value=True)
            metodologias = gr.CheckboxGroup(label=T.CONFIG_METODOLOGIAS, choices=T.opcoes(T.METODOLOGIAS), value=prof.metodologias_preferidas)
            preferencias = gr.Textbox(label=T.CONFIG_PREFERENCIAS, value=prof.preferencias_pedagogicas, lines=2)
            email = gr.Textbox(label=T.CONFIG_EMAIL, value=prof.email_contato)
            btn_salvar = gr.Button(T.BTN_SALVAR_PERFIL, variant="primary")
            msg_perfil = gr.HTML("")

            def salvar_perfil(n, i, c, e, a, nv, d, cur, f, met, pref, em):
                p = sessao.repo.ler_professor()
                p.nome, p.instituicao, p.cidade, p.estado = (n or "").strip(), (i or "").strip(), (c or "").strip(), (e or "").strip().upper()[:2]
                p.area_principal = a or ""
                p.niveis_ensino = list(nv or [])
                p.duracao_padrao_min = int(d or 50)
                p.curriculo_padrao = cur or "nenhum"
                p.fuso_horario = f or dates.FUSO_PADRAO
                p.metodologias_preferidas = list(met or [])
                p.preferencias_pedagogicas = (pref or "").strip()
                p.email_contato = (em or "").strip()
                p.onboarding_concluido = True
                sessao.repo.gravar_professor(p)
                return C.ok(T.PERFIL_SALVO)

            btn_salvar.click(C.protegido(salvar_perfil, T.ERRO_GRAVACAO), [nome, instituicao, cidade, estado, area, niveis, duracao, curriculo, fuso, metodologias, preferencias, email], [msg_perfil])

        # ------------------------------------------- perfis instrumentais
        with gr.Accordion(T.CONFIG_PERFIS_INSTRUMENTAIS, open=False):
            with gr.Row():
                perfil_sel = gr.Dropdown(label=T.CONFIG_ESCOLHER_PERFIL, choices=C.opcoes_instrumentos(sessao), value="piano")
                btn_carregar_perfil = gr.Button(T.BTN_CARREGAR_PERFIL)
            perfil_json = gr.Code(label="Perfil (JSON editável)", language="json", lines=24)
            with gr.Row():
                btn_salvar_perfil_instr = gr.Button(T.BTN_SALVAR_PERFIL_INSTR, variant="primary")
                btn_restaurar = gr.Button(T.BTN_RESTAURAR_PERFIL)
            msg_perfil_instr = gr.HTML("")

            def carregar_perfil(pid):
                p = sessao.adaptador().perfil_especialidade(pid)
                return json.dumps(p, ensure_ascii=False, indent=2)

            btn_carregar_perfil.click(C.protegido(carregar_perfil), [perfil_sel], [perfil_json])

            def salvar_perfil_instr(pid, texto):
                try:
                    dados = json.loads(texto or "")
                    if not isinstance(dados, dict):
                        raise ValueError
                except ValueError:
                    return C.erro(T.PERFIL_INSTR_INVALIDO)
                dados["id"] = pid
                dados.pop("editado_pelo_professor", None)
                sessao.repo.gravar_perfil_editado(pid, dados)
                limpar_cache()
                return C.ok(T.PERFIL_INSTR_SALVO)

            btn_salvar_perfil_instr.click(C.protegido(salvar_perfil_instr, T.ERRO_GRAVACAO), [perfil_sel, perfil_json], [msg_perfil_instr])

            def restaurar(pid):
                sessao.repo.remover_perfil_editado(pid)
                limpar_cache()
                return C.ok(T.PERFIL_INSTR_RESTAURADO), carregar_perfil(pid)

            btn_restaurar.click(C.protegido(restaurar), [perfil_sel], [msg_perfil_instr, perfil_json])

        # --------------------------------------------------------- rubricas
        with gr.Accordion(T.CONFIG_RUBRICAS, open=False):
            rub_lista = gr.Markdown(_rubricas_md(sessao))
            with gr.Row():
                rub_id = gr.Textbox(label=T.CONFIG_RUBRICA_NOVO_ID)
                rub_rotulo = gr.Textbox(label=T.CONFIG_RUBRICA_NOVO_ROTULO)
                btn_rub_add = gr.Button(T.BTN_ADICIONAR_CRITERIO)
                btn_rub_rm = gr.Button(T.BTN_REMOVER_CRITERIO)
            msg_rub = gr.HTML("")

            def rub_add(cid, rot):
                cid = "".join(ch for ch in (cid or "").strip().lower().replace(" ", "_") if ch.isalnum() or ch == "_")
                if not cid or not (rot or "").strip():
                    return C.aviso(T.CONFIG_RUBRICA_NOVO_ROTULO), _rubricas_md(sessao)
                r = sessao.repo.ler_rubricas()
                r.criterios_proprios[cid] = rot.strip()
                sessao.repo.gravar_rubricas(r)
                return C.ok(T.CRITERIO_SALVO), _rubricas_md(sessao)

            def rub_rm(cid):
                cid = (cid or "").strip().lower()
                r = sessao.repo.ler_rubricas()
                r.criterios_proprios.pop(cid, None)
                sessao.repo.gravar_rubricas(r)
                return C.ok(T.CRITERIO_SALVO), _rubricas_md(sessao)

            btn_rub_add.click(C.protegido(rub_add, T.ERRO_GRAVACAO), [rub_id, rub_rotulo], [msg_rub, rub_lista])
            btn_rub_rm.click(C.protegido(rub_rm, T.ERRO_GRAVACAO), [rub_id], [msg_rub, rub_lista])

        # ------------------------------------------------------ privacidade
        with gr.Accordion(T.CONFIG_PRIVACIDADE, open=False):
            gr.Markdown(T.TRANSPARENCIA_DRIVE)
            with gr.Row():
                btn_exportar_tudo = gr.Button(T.BTN_EXPORTAR_TUDO)
                cod_export = gr.Textbox(label=T.DIGITE_CODIGO, placeholder=T.PLACEHOLDER_CODIGO)
                btn_exportar_reg = gr.Button(T.BTN_EXPORTAR_REGISTRO)
            arquivo_export = gr.File(label="Arquivo exportado", visible=False)
            msg_priv = gr.HTML("")
            with gr.Row():
                cod_excluir = gr.Textbox(label=T.DIGITE_CODIGO, placeholder=T.PLACEHOLDER_CODIGO)
                btn_excluir_reg = gr.Button(T.BTN_EXCLUIR_REGISTRO, variant="stop")
                btn_excluir_bib = gr.Button(T.BTN_EXCLUIR_BIBLIOTECA, variant="stop")
                btn_apagar_locais = gr.Button(T.BTN_APAGAR_LOCAIS)
            lista_exclusao = gr.Markdown("")
            with gr.Row(visible=False) as linha_confirmar:
                btn_confirmar = gr.Button(T.BTN_CONFIRMAR, variant="stop")
                btn_cancelar = gr.Button(T.BTN_CANCELAR)
            alvo_exclusao = gr.State("")

            def exportar_tudo():
                destino = sessao.repo.caminhos.exportacoes / f"percurso_{dates.carimbo_arquivo(sessao.fuso)}.zip"
                sessao.repo.exportar_zip(destino)
                return C.ok(T.EXPORTACAO_PRONTA.format(arquivo=destino.name)), gr.update(value=str(destino), visible=True)

            def exportar_reg(cod):
                try:
                    c = codes.normalizar_e_validar(cod)
                except ValueError:
                    return C.erro(T.CODIGO_INVALIDO), gr.update(visible=False)
                if not sessao.repo.registro_existe(c):
                    return C.erro(T.CODIGO_NAO_ENCONTRADO), gr.update(visible=False)
                destino = sessao.repo.caminhos.exportacoes / f"registro_{c}_{dates.carimbo_arquivo(sessao.fuso)}.zip"
                sessao.repo.exportar_zip(destino, apenas_registro=c)
                return C.ok(T.EXPORTACAO_PRONTA.format(arquivo=destino.name)), gr.update(value=str(destino), visible=True)

            btn_exportar_tudo.click(C.protegido(exportar_tudo), None, [msg_priv, arquivo_export])
            btn_exportar_reg.click(C.protegido(exportar_reg), [cod_export], [msg_priv, arquivo_export])

            def pedir_excluir_reg(cod):
                try:
                    c = codes.normalizar_e_validar(cod)
                except ValueError:
                    return C.erro(T.CODIGO_INVALIDO), "", gr.update(visible=False), ""
                itens = sessao.repo.descrever_exclusao_registro(c)
                if not itens:
                    return C.erro(T.CODIGO_NAO_ENCONTRADO), "", gr.update(visible=False), ""
                return C.aviso(T.CONFIRMAR_EXCLUSAO), "\n".join(f"- registros/{c}/{i}" for i in itens), gr.update(visible=True), f"registro:{c}"

            def pedir_excluir_bib():
                itens = _descrever_biblioteca(sessao)
                if not itens:
                    return C.aviso("A biblioteca está vazia."), "", gr.update(visible=False), ""
                return C.aviso(T.CONFIRMAR_EXCLUSAO), "\n".join(f"- {i}" for i in itens[:200]) + (f"\n- … e mais {len(itens) - 200}" if len(itens) > 200 else ""), gr.update(visible=True), "biblioteca"

            btn_excluir_reg.click(C.protegido(pedir_excluir_reg), [cod_excluir], [msg_priv, lista_exclusao, linha_confirmar, alvo_exclusao])
            btn_excluir_bib.click(C.protegido(pedir_excluir_bib), None, [msg_priv, lista_exclusao, linha_confirmar, alvo_exclusao])

            def confirmar(alvo):
                if alvo.startswith("registro:"):
                    c = alvo.split(":", 1)[1]
                    pasta = sessao.repo.excluir_registro(c)
                    if sessao.contexto and sessao.contexto.codigo == c:
                        sessao.descarregar()
                    return C.ok(T.EXCLUSAO_CONCLUIDA.format(pasta=pasta.name)), "", gr.update(visible=False), ""
                if alvo == "biblioteca":
                    pasta = _excluir_biblioteca(sessao)
                    return C.ok(T.BIBLIOTECA_EXCLUIDA.format(pasta=pasta.name)), "", gr.update(visible=False), ""
                return "", "", gr.update(visible=False), ""

            btn_confirmar.click(C.protegido(confirmar, T.ERRO_GRAVACAO), [alvo_exclusao], [msg_priv, lista_exclusao, linha_confirmar, alvo_exclusao])
            btn_cancelar.click(lambda: ("", "", gr.update(visible=False), ""), None, [msg_priv, lista_exclusao, linha_confirmar, alvo_exclusao])

            def apagar_locais():
                sessao.plataforma.limpar_dados_locais()
                sessao.chave_temporaria = None
                sessao.gemini_pronto = False
                sessao.modo_ia = "essencial"
                sessao.cliente_gemini = None
                sessao.consentimento_trechos = False
                sessao.mapa_pseudonimos.clear()
                sessao.cache_ia.clear()
                sessao.descarregar()
                return C.ok(T.LOCAIS_APAGADOS)

            btn_apagar_locais.click(C.protegido(apagar_locais), None, [msg_priv])

        # --------------------------------------------------------- backups
        with gr.Accordion(T.CONFIG_BACKUPS, open=False):
            backups = gr.Dropdown(label=T.CONFIG_BACKUPS, choices=sessao.repo.listar_backups(), value=None)
            btn_rm_backup = gr.Button(T.BTN_REMOVER_BACKUP, variant="stop")
            msg_backup = gr.HTML("")

            def rm_backup(nome):
                if nome and sessao.repo.remover_backup(nome):
                    return C.ok(T.BACKUP_REMOVIDO), gr.update(choices=sessao.repo.listar_backups(), value=None)
                return "", gr.update(choices=sessao.repo.listar_backups())

            btn_rm_backup.click(C.protegido(rm_backup), [backups], [msg_backup, backups])

        # ------------------------------------------------------ diagnóstico
        with gr.Accordion(T.CONFIG_DIAGNOSTICO, open=False):
            btn_diag = gr.Button(T.BTN_DIAGNOSTICO)
            diag = gr.Textbox(label=T.DIAGNOSTICO_INTRO, lines=14, interactive=False)

            def diagnostico():
                partes = [f"Plataforma: {sessao.plataforma.nome} · base: {sessao.repo.base}", f"Modo IA: {sessao.modo_ia} (pronto: {sessao.gemini_pronto})"]
                partes.append(ultimas_linhas(sessao.plataforma.caminho_log_runtime(), 40))
                partes.append(ultimas_linhas(sessao.repo.caminhos.diagnostico_log, 20))
                return "\n".join(partes)

            btn_diag.click(diagnostico, None, [diag])

        def ao_selecionar():
            return gr.update(choices=sessao.repo.listar_backups()), _rubricas_md(sessao)

        tab.select(ao_selecionar, None, [backups, rub_lista])

    return {"tab": tab}


def _rubricas_md(sessao: Sessao) -> str:
    r = sessao.repo.ler_rubricas()
    if not r.criterios_proprios:
        return "_Nenhum critério próprio. Os critérios padrão vêm do perfil do instrumento._"
    return "\n".join(f"- `{k}` → {v}" for k, v in r.criterios_proprios.items())


def _descrever_biblioteca(sessao: Sessao) -> list:
    cam = sessao.repo.caminhos
    itens = []
    for pasta in [cam.biblioteca, cam.indices]:
        if pasta.exists():
            for p in sorted(pasta.rglob("*")):
                if p.is_file() and not p.name.endswith((".bak", ".tmp")):
                    itens.append(str(p.relative_to(sessao.repo.base)))
    return itens


def _excluir_biblioteca(sessao: Sessao) -> Path:
    cam = sessao.repo.caminhos
    destino = sessao.repo.backup_pasta(cam.biblioteca, "exclusao-biblioteca")
    if cam.indices.exists():
        sessao.repo.backup_pasta(cam.indices, "exclusao-biblioteca")
    for pasta in [cam.biblioteca, cam.indices]:
        if pasta.exists():
            shutil.rmtree(pasta)
    cam.criar_estrutura()
    return destino
