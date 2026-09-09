"""Novo registro (SPEC §6.4): individual, dupla ou turma. Ao final, código + QR."""
from __future__ import annotations

import gradio as gr

from ...core.models import Agenda, AlunoTurma, Registro, Turma
from ...support import donations
from ...utils import dates
from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_NOVO, id="novo") as tab:
        gr.Markdown(f"## {T.NOVO_TITULO}")
        with gr.Accordion("Como preencher este cadastro", open=False):
            gr.Markdown(T.TUTORIAL_CADASTRO)
        tipo = gr.Radio(label=T.NOVO_TIPO, choices=T.opcoes(T.TIPOS_REGISTRO), value="individual")
        with gr.Row(equal_height=True, elem_classes=["percurso-identificacao"]):
            identificacao = gr.Textbox(label=T.NOVO_IDENTIFICACAO, placeholder="Ex.: Ana ou A. S.")
            idade = gr.Number(label=T.NOVO_IDADE, value=None, placeholder="Opcional", precision=0, minimum=2, maximum=120)
        gr.Markdown(T.NOVO_IDENTIFICACAO_AJUDA + " A idade é opcional; deixe em branco se não quiser informar.", elem_classes=["percurso-ajuda-campo"])
        with gr.Group(visible=False) as grupo_turma:
            with gr.Row():
                turma_nome = gr.Textbox(label=T.NOVO_TURMA_NOME)
                turma_qtd = gr.Number(label=T.NOVO_TURMA_QTD, value=0, precision=0, minimum=0)
                turma_faixa = gr.Textbox(label=T.NOVO_FAIXA_ETARIA)
            turma_alunos = gr.Textbox(label=T.NOVO_TURMA_ALUNOS, lines=4)
        with gr.Row():
            instrumento = gr.Dropdown(label=T.NOVO_INSTRUMENTO, choices=C.opcoes_instrumentos(sessao), value="piano")
            instrumento_outro = gr.Textbox(label=T.NOVO_INSTRUMENTO_OUTRO)
        with gr.Row():
            nivel = gr.Dropdown(label=T.NOVO_NIVEL, choices=T.opcoes(T.NIVEIS), value="iniciante")
            modalidade = gr.Dropdown(label=T.NOVO_MODALIDADE, choices=T.opcoes(T.MODALIDADES), value="individual")
            modalidade_outro = gr.Textbox(label=T.NOVO_MODALIDADE_OUTRO)
        with gr.Row():
            contexto = gr.Dropdown(label=T.NOVO_CONTEXTO, choices=T.opcoes(T.CONTEXTOS), value="aula_particular")
            curriculo = gr.Dropdown(label=T.NOVO_CURRICULO, choices=T.opcoes(T.CURRICULOS), value=sessao.repo.ler_professor().curriculo_padrao)
        with gr.Row():
            dia = gr.Dropdown(label=T.NOVO_DIA, choices=T.opcoes(T.DIAS), value="segunda")
            inicio = gr.Textbox(label=T.NOVO_INICIO, value="15:00")
            duracao = gr.Number(label=T.NOVO_DURACAO, value=sessao.repo.ler_professor().duracao_padrao_min or 50, precision=0, minimum=5, maximum=300)
        with gr.Row():
            conhecimentos = gr.Textbox(label=T.NOVO_CONHECIMENTOS, lines=3)
            objetivos = gr.Textbox(label=T.NOVO_OBJETIVOS, lines=3)
        recursos = gr.CheckboxGroup(label=T.NOVO_RECURSOS, choices=T.opcoes(T.RECURSOS), value=["instrumentos"])
        metodologias = gr.CheckboxGroup(label=T.NOVO_METODOLOGIAS, choices=T.opcoes(T.METODOLOGIAS), value=[])
        adaptacoes = gr.Textbox(label=T.NOVO_ADAPTACOES, lines=2)
        observacoes = gr.Textbox(label=T.NOVO_OBSERVACOES, lines=2)
        btn_criar = gr.Button(T.BTN_CRIAR_REGISTRO, variant="primary")
        resultado = gr.Markdown("")
        qr = gr.Image(label="QR Code do código", visible=False, type="filepath", height=220)

        def ao_mudar_tipo(t):
            return gr.update(visible=(t == "turma")), gr.update(value="turma" if t == "turma" else ("dupla" if t == "dupla" else "individual"))

        tipo.change(ao_mudar_tipo, [tipo], [grupo_turma, modalidade])

        def criar(tipo_v, ident, idade_v, t_nome, t_qtd, t_faixa, t_alunos, instr, instr_outro, nivel_v, mod, mod_outro, ctx_v, cur, dia_v, ini, dur, conh, obj, rec, met, adap, obs):
            ident = (ident or "").strip()
            if tipo_v != "turma" and not ident:
                return C.erro(T.IDENTIFICACAO_OBRIGATORIA), gr.update(visible=False)
            if tipo_v == "turma" and not (t_nome or "").strip() and not ident:
                return C.erro(T.IDENTIFICACAO_OBRIGATORIA), gr.update(visible=False)
            try:
                dates.parse_hora(ini or "15:00")
            except ValueError:
                return C.erro(T.AULA_HORA_INVALIDA), gr.update(visible=False)
            dur_i = int(dur or 50)
            agenda = Agenda(dia_habitual=dia_v or "", inicio=ini or "", termino=dates.somar_minutos(ini or "15:00", dur_i), duracao_min=dur_i)
            turma = None
            if tipo_v == "turma":
                alunos = [AlunoTurma(id=f"A{i + 1:02d}", identificacao=n) for i, n in enumerate(C.linhas(t_alunos))]
                turma = Turma(nome=(t_nome or ident).strip(), quantidade_alunos=int(t_qtd or len(alunos)), nivel_geral=nivel_v, faixa_etaria=(t_faixa or "").strip(), alunos=alunos)
            reg = Registro(
                codigo="",
                tipo=tipo_v,
                modalidade=mod or ("turma" if tipo_v == "turma" else "individual"),
                modalidade_outro=(mod_outro or "").strip() or None,
                identificacao=ident or (turma.nome if turma else ""),
                idade=int(idade_v) if idade_v not in (None, "") else None,
                instrumento=instr or "outro",
                instrumento_outro=(instr_outro or "").strip() or None,
                nivel=nivel_v,
                contexto=ctx_v,
                curriculo=cur or "nenhum",
                agenda=agenda,
                conhecimentos_previos=C.linhas(conh),
                objetivos=C.linhas(obj),
                adaptacoes=(adap or "").strip(),
                recursos_habituais=list(rec or []),
                metodologias=list(met or []),
                observacoes=(obs or "").strip(),
                turma=turma,
            )
            reg = sessao.repo.criar_registro(reg)
            sessao.carregar(reg.codigo)
            caminho = sessao.repo.caminhos.materiais(reg.codigo) / "qr_codigo.png"
            try:
                donations.salvar_qr(reg.codigo, caminho)
                qr_update = gr.update(value=str(caminho), visible=True)
            except Exception:
                qr_update = gr.update(visible=False)
            return T.REGISTRO_CRIADO.format(codigo=reg.codigo) + "\n\n" + T.REGISTRO_CRIADO_DICA, qr_update

        btn_criar.click(
            C.protegido(criar, T.ERRO_GRAVACAO),
            [tipo, identificacao, idade, turma_nome, turma_qtd, turma_faixa, turma_alunos, instrumento, instrumento_outro, nivel, modalidade, modalidade_outro, contexto, curriculo, dia, inicio, duracao, conhecimentos, objetivos, recursos, metodologias, adaptacoes, observacoes],
            [resultado, qr],
        )

        def ao_selecionar():
            prof = sessao.repo.ler_professor()
            return gr.update(value=prof.curriculo_padrao), gr.update(value=prof.duracao_padrao_min or 50), gr.update(choices=C.opcoes_instrumentos(sessao))

        tab.select(ao_selecionar, None, [curriculo, duracao, instrumento])

    return {"tab": tab, "resultado": resultado}
