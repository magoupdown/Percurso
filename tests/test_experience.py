"""Regressões de integridade e dos fluxos de continuidade."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from conftest import registro_piano
from percurso.core import planner
from percurso.ui import common
from percurso.ui.screens.continuar import _recentes
from percurso.storage.atomic import escrever_json, ler_json


def test_trocar_aluno_limpa_plano_formulario_e_pseudonimos(sessao):
    a = registro_piano(sessao.repo, 'João')
    b = registro_piano(sessao.repo, 'Bia')
    sessao.carregar(a.codigo)
    sessao.ultimo_plano = planner.gerar_plano(sessao.entrada_planejamento())
    sessao.formulario_aula = {'observacoes': 'Somente João'}
    sessao.pseudonimizar('João')
    sessao.cache_ia['resposta'] = 'Somente João'
    sessao.carregar(b.codigo)
    assert sessao.contexto.codigo == b.codigo
    assert sessao.ultimo_plano is None
    assert not sessao.formulario_aula
    assert not sessao.mapa_pseudonimos
    assert not sessao.cache_ia


def test_recarregar_mesmo_aluno_preserva_plano(sessao):
    a = registro_piano(sessao.repo)
    sessao.carregar(a.codigo)
    plano = planner.gerar_plano(sessao.entrada_planejamento())
    sessao.ultimo_plano = plano
    sessao.recarregar()
    assert sessao.ultimo_plano is plano


def test_falha_ao_carregar_nao_perde_contexto(sessao):
    a = registro_piano(sessao.repo)
    sessao.carregar(a.codigo)
    with pytest.raises(Exception):
        sessao.carregar('PCR-ZZZZZZ')
    assert sessao.contexto.codigo == a.codigo


def test_desativar_gemini_revoga_consentimento(sessao):
    sessao.chave_temporaria = 'chave-ficticia'
    sessao.consentimento_trechos = True
    sessao.gemini_pronto = True
    sessao.cliente_gemini = object()
    sessao.modo_ia = 'gemini'
    sessao.cache_ia['x'] = 'y'
    sessao.desativar_gemini()
    assert sessao.modo_ia == 'essencial'
    assert sessao.chave_temporaria is None
    assert sessao.cliente_gemini is None
    assert not sessao.consentimento_trechos
    assert not sessao.gemini_pronto
    assert not sessao.cache_ia


@pytest.mark.parametrize('render', [common.ok, common.aviso, common.erro])
def test_mensagens_nao_interpretam_html(render):
    html = render('<img src=x onerror=alert(1)>')
    assert '<img' not in html
    assert '&lt;img' in html
    assert 'role=' in html


def test_cabecalho_escapa_nome(sessao):
    a = registro_piano(sessao.repo, '<svg onload=alert(1)>')
    sessao.carregar(a.codigo)
    assert '<svg' not in common.cabecalho_registro(sessao)


def test_busca_nome_sem_acento_instrumento_codigo(sessao):
    a = registro_piano(sessao.repo, 'João')
    registro_piano(sessao.repo, 'Bia')
    assert [x[1] for x in _recentes(sessao, 'joao piano')] == [a.codigo]
    assert [x[1] for x in _recentes(sessao, a.codigo.lower())] == [a.codigo]
    assert len(_recentes(sessao, 'piano')) == 2
    assert not _recentes(sessao, 'violino')


def test_escritas_concorrentes_nao_colidem_tmp(tmp_path):
    alvo = tmp_path / 'estado.json'
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda n: escrever_json(alvo, {'n': n, 'payload': str(n)*10000}), range(30)))
    r = ler_json(alvo)
    assert r['payload'] == str(r['n'])*10000
    assert not list(tmp_path.glob('*.tmp'))


def test_validacao_falha_preserva_original(tmp_path):
    alvo = tmp_path / 'estado.json'
    escrever_json(alvo, {'n': 1})
    def rejeitar(obj):
        raise ValueError('invalido')
    with pytest.raises(Exception):
        escrever_json(alvo, {'n': 2}, rejeitar)
    assert ler_json(alvo) == {'n': 1}
    assert not list(tmp_path.glob('*.tmp'))


def test_exportacao_nao_inclui_exports_anteriores_ou_logs(sessao):
    import zipfile
    registro_piano(sessao.repo)
    pasta = sessao.repo.caminhos.exportacoes
    primeiro = pasta / 'primeiro.zip'
    segundo = pasta / 'segundo.zip'
    sessao.repo.exportar_zip(primeiro)
    sessao.repo.exportar_zip(segundo)
    with zipfile.ZipFile(segundo) as z:
        nomes = z.namelist()
    assert any(n.endswith('perfil.json') for n in nomes)
    assert not any(n.endswith(('.zip', '.log', '.log.1')) for n in nomes)


@pytest.mark.parametrize('instrumento', ['../../fora', '/tmp/fora', '../professor', 'piano/../../fora'])
def test_perfil_nao_escapa_pasta(sessao, instrumento):
    with pytest.raises(ValueError):
        sessao.repo.gravar_perfil_editado(instrumento, {'id': instrumento})


def test_pseudonimizacao_inclui_nome_da_turma(sessao):
    from percurso.core.models import Registro, Turma
    turma = Registro(codigo='', tipo='turma', identificacao='Grupo', instrumento='piano', turma=Turma(nome='Coral Aurora'))
    reg = sessao.repo.criar_registro(turma)
    sessao.carregar(reg.codigo)
    texto = sessao.pseudonimizar('Coral Aurora está preparado. Grupo canta.')
    assert 'Coral Aurora' not in texto and 'Grupo' not in texto


def test_formulario_sem_presenca_inferida_e_sem_textos_anteriores(sessao):
    import gradio as gr
    from percurso.ui.screens import aula
    a = registro_piano(sessao.repo)
    sessao.carregar(a.codigo)
    with gr.Blocks():
        tela = aula.montar(sessao)
    valores = tela['preencher']()
    assert len(valores) == len(tela['saidas_preencher'])
    por_label = {getattr(c, 'label', ''): v for c, v in zip(tela['saidas_preencher'], valores)}
    from percurso.ui import texts as T
    assert por_label[T.AULA_FREQUENCIA] is None
    assert por_label[T.AULA_OBSERVACOES] == ''
    assert por_label[T.AULA_AVALIACAO] == ''
