"""Edição e reinicialização explícita, com backup e estado recalculado."""
from __future__ import annotations
import shutil
from uuid import uuid4
from .models import Registro, Aula, Plano, Repertorio, EstadoAtual, ResumoPedagogico
from . import state, schedule
from ..utils import dates


def backup(repo, codigo, motivo):
    repo.ler_registro(codigo)
    return repo.backup_pasta(repo.caminhos.registro(codigo), f'{motivo}-{uuid4().hex[:8]}')


def editar_registro(repo, codigo, alteracoes):
    original = repo.ler_registro(codigo)
    dados = original.model_dump()
    permitidos = set(Registro.model_fields) - {'codigo','criado_em','atualizado_em','schema_version','dominio','tipo'}
    if set(alteracoes) - permitidos:
        raise ValueError('O código e o tipo do cadastro não podem ser alterados nesta edição.')
    dados.update(alteracoes)
    novo = Registro.model_validate(dados)
    if not novo.identificacao.strip() and not (novo.turma and novo.turma.nome.strip()):
        raise ValueError('Informe a identificação do aluno ou o nome da turma.')
    if novo.idade is not None and not 2 <= novo.idade <= 120:
        raise ValueError('Informe uma idade entre 2 e 120 anos ou deixe em branco.')
    if not 5 <= novo.agenda.duracao_min <= 300:
        raise ValueError('A duração deve ficar entre 5 e 300 minutos.')
    if novo.agenda.inicio:
        dates.parse_hora(novo.agenda.inicio)
        novo.agenda.termino = dates.somar_minutos(novo.agenda.inicio, novo.agenda.duracao_min)
    if novo.turma:
        ids = [a.id for a in novo.turma.alunos]
        if len(set(ids)) != len(ids) or any(not i for i in ids):
            raise ValueError('Cada aluno da turma precisa de um ID único.')
        antigos = {a.id for a in original.turma.alunos} if original.turma else set()
        removidos = antigos - set(ids)
        for a in repo.listar_aulas(codigo):
            ft = a.frequencia_turma
            if ft and removidos.intersection(ft.presentes + ft.ausentes):
                raise ValueError('Não remova alunos com frequência registrada. Você pode corrigir seus nomes mantendo o ID.')
        novo.turma.quantidade_alunos = max(novo.turma.quantidade_alunos, len(ids))
    backup(repo,codigo,'antes-editar-cadastro')
    repo.gravar_registro(novo)
    state.atualizar_apos_aula(repo,codigo)
    return novo


def editar_aula(repo,codigo,identificador,alteracoes):
    original = repo.ler_aula(codigo,identificador)
    if {'id','criado_em','plano_origem','schema_version'} & set(alteracoes):
        raise ValueError('A identidade da aula deve ser preservada.')
    dados=original.model_dump(); dados.update(alteracoes)
    if 'conteudo_realizado' in alteracoes:
        anteriores = {c.conteudo: c.model_dump() for c in original.classificacao_conteudos}
        dados['classificacao_conteudos'] = [anteriores.get(c, {'conteudo':c,'situacao':'em_desenvolvimento'}) for c in alteracoes['conteudo_realizado']]
    novo=Aula.model_validate(dados)
    data=dates.parse_data(novo.data)
    novo.data=data.isoformat(); novo.dia_semana=dates.dia_semana(data)
    if not 0 <= novo.duracao_real_min <= 600:
        raise ValueError('Informe uma duração real entre 0 e 600 minutos.')
    if novo.frequencia not in ('presente','reposicao','aula_extra'):
        novo.duracao_real_min=0
    backup(repo,codigo,'antes-editar-aula')
    repo.gravar_aula(codigo,novo)
    state.atualizar_apos_aula(repo,codigo)
    return novo


def editar_plano(repo,codigo,identificador,alteracoes):
    original=repo.ler_plano(codigo,identificador)
    if original.status == 'realizado':
        raise ValueError('Este plano já foi realizado. Edite a aula correspondente para corrigir o registro.')
    permitidos={'tema','data','duracao_min','objetivo_geral','objetivos_especificos','conteudos','metodologia','avaliacao','continuidade','adaptacoes','recursos'}
    if set(alteracoes)-permitidos:
        raise ValueError('Campo de plano não editável.')
    dados=original.model_dump();dados.update(alteracoes)
    novo=Plano.model_validate(dados)
    novo.data=dates.parse_data(novo.data).isoformat()
    if not 5<=novo.duracao_min<=300:
        raise ValueError('A duração deve ficar entre 5 e 300 minutos.')
    if novo.duracao_min!=original.duracao_min:
        novo.cronograma=schedule.adaptar_duracao(original.cronograma,novo.duracao_min)
        for atividade in novo.atividades:
            for bloco in novo.cronograma:
                if atividade.bloco==bloco.etapa and atividade.bloco!='alternativa':
                    atividade.duracao_min=bloco.fim_min-bloco.inicio_min
                    break
    schedule.exigir_valido(novo.cronograma,novo.duracao_min)
    backup(repo,codigo,'antes-editar-plano')
    repo.gravar_plano(novo)
    # A data pode alterar o nome do arquivo; só remove o anterior depois de gravar.
    if original.nome_arquivo()!=novo.nome_arquivo():
        (repo.caminhos.planos(codigo)/original.nome_arquivo()).unlink(missing_ok=True)
    return novo


def resetar(repo,codigo,escopo,identificador=None):
    repo.ler_registro(codigo)
    if escopo=='aula':
        aula=repo.ler_aula(codigo,identificador)
    elif escopo=='plano':
        plano=repo.ler_plano(codigo,identificador)
        if plano.status=='realizado':
            raise ValueError('Não remova um plano vinculado a uma aula realizada.')
    elif escopo not in ('historico','cadastro'):
        raise ValueError('Escolha uma opção de reset válida.')
    destino=backup(repo,codigo,'antes-reset-'+escopo)
    if escopo=='cadastro':
        shutil.rmtree(repo.caminhos.registro(codigo))
    elif escopo=='aula':
        repo.excluir_aula(codigo,aula.id)
        if aula.plano_origem:
            for p in repo.listar_planos(codigo):
                if p.nome_arquivo()==aula.plano_origem.split('/')[-1] and not any(a.plano_origem==aula.plano_origem for a in repo.listar_aulas(codigo)):
                    p.status='gerado';repo.gravar_plano(p)
        state.atualizar_apos_aula(repo,codigo)
    elif escopo=='plano':
        arq=repo.caminhos.planos(codigo)/plano.nome_arquivo()
        arq.unlink(); arq.with_name(arq.name+'.bak').unlink(missing_ok=True)
    else:
        for pasta in (repo.caminhos.aulas(codigo),repo.caminhos.planos(codigo),repo.caminhos.materiais(codigo)):
            if pasta.exists(): shutil.rmtree(pasta)
            pasta.mkdir(parents=True,exist_ok=True)
        repo.gravar_repertorio(codigo,Repertorio())
        repo.gravar_estado(codigo,EstadoAtual())
        repo.gravar_resumo(codigo,ResumoPedagogico())
        state.atualizar_apos_aula(repo,codigo)
    return destino
