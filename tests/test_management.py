from conftest import registro_piano, aula
from percurso.core import management as M
import pytest


def test_editar_resetar_aula_preserva_cadastro_e_backup(repo):
    r=registro_piano(repo)
    a=repo.gravar_aula(r.codigo,aula('2026-01-01',obs='anterior'))
    M.editar_aula(repo,r.codigo,a.id,{'data':'2026-01-02','observacoes':'corrigida'})
    assert len(repo.listar_aulas(r.codigo))==1
    assert repo.ler_aula(r.codigo,a.id).observacoes=='corrigida'
    destino=M.resetar(repo,r.codigo,'aula',a.id)
    assert destino.exists()
    assert not repo.listar_aulas(r.codigo)
    assert repo.ler_registro(r.codigo).identificacao=='João'


def test_editar_cadastro_e_reset_historico(repo):
    r=registro_piano(repo)
    repo.gravar_aula(r.codigo,aula('2026-01-01'))
    M.editar_registro(repo,r.codigo,{'identificacao':'Nome corrigido'})
    assert repo.ler_registro(r.codigo).identificacao=='Nome corrigido'
    assert len(repo.listar_aulas(r.codigo))==1
    M.resetar(repo,r.codigo,'historico')
    assert not repo.listar_aulas(r.codigo)
    assert repo.ler_estado(r.codigo).total_aulas==0
    assert repo.ler_registro(r.codigo).identificacao=='Nome corrigido'


def test_excluir_cadastro_com_backup(repo):
    r=registro_piano(repo)
    destino=M.resetar(repo,r.codigo,'cadastro')
    assert destino.exists()
    assert r.codigo not in repo.listar_codigos()


def test_edicao_invalida_nao_altera_cadastro(repo):
    r=registro_piano(repo)
    with pytest.raises(ValueError): M.editar_registro(repo,r.codigo,{'idade':-1})
    assert repo.ler_registro(r.codigo).idade==10


def test_falha_gravacao_preserva_aula_antiga(repo,monkeypatch):
    r=registro_piano(repo)
    a=repo.gravar_aula(r.codigo,aula('2026-01-01'))
    a.data='2026-01-02'
    def falhar(*args,**kwargs): raise OSError('falha simulada')
    monkeypatch.setattr(repo,'_gravar',falhar)
    with pytest.raises(OSError): repo.gravar_aula(r.codigo,a)
    assert repo.ler_aula(r.codigo,a.id).data=='2026-01-01'


def test_plano_editado_adapta_cronograma_e_reset_desvincula_aula(sessao):
    from percurso.core import planner
    from percurso.core.models import Aula
    r=registro_piano(sessao.repo);sessao.carregar(r.codigo)
    p=sessao.repo.gravar_plano(planner.gerar_plano(sessao.entrada_planejamento()))
    p=M.editar_plano(sessao.repo,r.codigo,p.id,{'duracao_min':40,'data':'2026-02-01'})
    assert p.cronograma[-1].fim_min==40
    assert len(sessao.repo.listar_planos(r.codigo))==1
    sessao.registrar_aula(Aula(id='',data=p.data,plano_origem=p.nome_arquivo()))
    with pytest.raises(ValueError): M.resetar(sessao.repo,r.codigo,'plano',p.id)
    a=sessao.repo.listar_aulas(r.codigo)[0]
    M.resetar(sessao.repo,r.codigo,'aula',a.id)
    assert sessao.repo.ler_plano(r.codigo,p.id).status=='gerado'
    M.resetar(sessao.repo,r.codigo,'plano',p.id)
    assert not sessao.repo.listar_planos(r.codigo)


def test_feedback_chave_temporaria_e_segredo(sessao,monkeypatch):
    from percurso.ai import gemini
    from test_app import _ClienteFalso
    temporario=gemini.ativar(sessao,'teste-temporario',fabrica_cliente=_ClienteFalso)
    assert temporario.ok and 'não foi salva' in temporario.mensagem
    assert 'teste-temporario' not in temporario.mensagem
    sessao.desativar_gemini()
    monkeypatch.setattr(sessao.plataforma,'obter_segredo',lambda nome:'teste-segredo')
    segredo=gemini.ativar(sessao,fabrica_cliente=_ClienteFalso)
    assert segredo.ok and 'Não é necessário colá-la novamente' in segredo.mensagem
    assert sessao.chave_temporaria is None


def test_reset_ui_exige_confirmacao_e_selecao_estavel(sessao):
    import gradio as gr
    from percurso.ui.screens import gerenciar
    r=registro_piano(sessao.repo)
    with gr.Blocks() as demo: gerenciar.montar(sessao)
    funcoes={f.fn.__name__:f.fn for f in demo.fns.values() if f.fn}
    revisar=funcoes['revisar_reset']; executar=funcoes['executar_reset']
    pendente,*_=revisar(r.codigo,'cadastro',None,None)
    with pytest.raises(gr.Error): executar(pendente,'errado',r.codigo,'cadastro',None,None)
    with pytest.raises(gr.Error): executar(pendente,r.codigo,r.codigo,'historico',None,None)
    assert sessao.repo.ler_registro(r.codigo)
    executar(pendente,r.codigo,r.codigo,'cadastro',None,None)
    assert not sessao.repo.listar_codigos()
