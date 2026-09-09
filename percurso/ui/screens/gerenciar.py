"""Editores vinculados ao cadastro escolhido e resets com confirmação explícita."""
import gradio as gr
from ...core import management as M
from .. import common as C, texts as T
from .continuar import _recentes


def montar(sessao):
    repo = sessao.repo
    def seguro(fn):
        def executar(*args):
            try:
                return fn(*args)
            except ValueError as e:
                raise gr.Error(str(e)) from None
            except Exception:
                raise gr.Error('Não foi possível concluir. Confira a seleção e tente novamente.') from None
        executar.__name__ = fn.__name__
        return executar

    def invalidar(codigo):
        if sessao.contexto and sessao.contexto.codigo == codigo:
            sessao.descarregar()
            if codigo in repo.listar_codigos():
                sessao.carregar(codigo)

    with gr.Tab('Editar e resetar', id='gerenciar') as tab:
        gr.Markdown('## Editar e resetar\nSelecione um cadastro. **Restaurar campos salvos** desfaz apenas o que ainda não foi salvo. Edições e resets criam backup automático em Configurações.')
        cadastro = gr.Dropdown(label='Aluno ou turma', choices=_recentes(sessao))
        tab.select(lambda: gr.update(choices=_recentes(sessao), value=None), None, cadastro)
        with gr.Accordion('Editar aluno ou turma', open=True):
            carregar = gr.Button('Carregar cadastro / Restaurar campos salvos')
            vinculo = gr.State(None)
            with gr.Row(equal_height=True):
                nome = gr.Textbox(label='Identificação do aluno ou nome da turma')
                idade = gr.Number(label='Idade (opcional)', precision=0, value=None)
                nivel = gr.Dropdown(label='Nível', choices=T.opcoes(T.NIVEIS))
            with gr.Row(equal_height=True):
                instrumento = gr.Dropdown(label='Instrumento', choices=C.opcoes_instrumentos(sessao))
                inicio = gr.Textbox(label='Horário habitual (HH:MM)')
                duracao = gr.Number(label='Duração habitual em minutos', precision=0, value=50)
            objetivos = gr.Textbox(label='Objetivos (um por linha)', lines=3)
            conhecimentos = gr.Textbox(label='Conhecimentos prévios (um por linha)', lines=3)
            adaptacoes = gr.Textbox(label='Adaptações', lines=2)
            observacoes = gr.Textbox(label='Observações', lines=3)
            alunos = gr.Dataframe(headers=['ID', 'Nome do aluno'], datatype=['str','str'], type='array', column_count=2, label='Alunos da turma: mantenha o ID ao corrigir nomes', visible=False)
            salvar = gr.Button('Salvar edição do cadastro', variant='primary')
            msg = gr.HTML()
            campos = [nome,idade,nivel,instrumento,inicio,duracao,objetivos,conhecimentos,adaptacoes,observacoes,alunos]
            def ler_cadastro(c):
                r=repo.ler_registro(c)
                return [c,r.turma.nome if r.turma else r.identificacao,r.idade,r.nivel,r.instrumento,r.agenda.inicio,r.agenda.duracao_min,C.juntar(r.objetivos),C.juntar(r.conhecimentos_previos),r.adaptacoes,r.observacoes,gr.update(value=[[a.id,a.identificacao] for a in r.turma.alunos] if r.turma else [],visible=bool(r.turma))]
            carregar.click(seguro(ler_cadastro),cadastro,[vinculo]+campos)
            def salvar_cadastro(c,b,n,i,nv,ins,h,d,obj,con,ad,obs,lista):
                if not c or c!=b: raise ValueError('Carregue o cadastro selecionado antes de salvar.')
                r=repo.ler_registro(c)
                alteracoes=dict(identificacao=n,idade=i,nivel=nv,instrumento=ins,agenda={**r.agenda.model_dump(),'inicio':h,'duracao_min':d},objetivos=C.linhas(obj),conhecimentos_previos=C.linhas(con),adaptacoes=ad,observacoes=obs)
                if r.turma:
                    alteracoes['turma']={**r.turma.model_dump(),'nome':n,'alunos':[{'id':str(row[0]).strip(),'identificacao':str(row[1]).strip()} for row in lista if any(row)]}
                M.editar_registro(repo,c,alteracoes);invalidar(c)
                return C.ok('Cadastro atualizado. Backup da versão anterior disponível em Configurações.')
            salvar.click(seguro(salvar_cadastro),[cadastro,vinculo]+campos,msg)

        # Mesma interação para cada registro: carregar, editar e restaurar.
        seletores={}
        for escopo,titulo,especificacao in [
            ('aula','Editar aula',[('data','Data (AAAA-MM-DD)',False),('frequencia','Frequência',False),('duracao_real_min','Duração real em minutos',False),('conteudo_realizado','Conteúdos realizados',True),('objetivos','Objetivos',True),('materiais','Materiais',True),('avaliacao_qualitativa','Avaliação qualitativa',False),('dificuldades','Dificuldades',True),('conquistas','Conquistas',True),('observacoes','Observações',False),('tarefas','Tarefas',True),('proximo_passo','Próximo passo',False)]),
            ('plano','Editar plano',[('data','Data (AAAA-MM-DD)',False),('tema','Tema',False),('duracao_min','Duração em minutos',False),('objetivo_geral','Objetivo geral',False),('objetivos_especificos','Objetivos específicos',True),('conteudos','Conteúdos',True),('recursos','Recursos',True),('metodologia','Metodologia',False),('avaliacao','Avaliação',False),('continuidade','Continuidade',False),('adaptacoes','Adaptações',False)])]:
            def editor(escopo,titulo,spec):
                with gr.Accordion(titulo,open=False):
                    atualizar=gr.Button('Listar '+('aulas' if escopo=='aula' else 'planos')+' do cadastro selecionado')
                    selecao=gr.Dropdown(label='Escolha o item')
                    seletores[escopo]=selecao
                    vinc=gr.State(None)
                    ler=gr.Button('Carregar item / Restaurar campos salvos')
                    campos=[]
                    for chave,label,multi in spec:
                        if chave=='frequencia': campo=gr.Dropdown(label=label,choices=T.opcoes(T.FREQUENCIAS))
                        elif 'duracao' in chave: campo=gr.Number(label=label,precision=0)
                        else: campo=gr.Textbox(label=label+(' (um por linha)' if multi else ''),lines=2 if multi else 1)
                        campos.append(campo)
                    salvar=gr.Button('Salvar edição',variant='primary');status=gr.HTML()
                    def listar(c):
                        repo.ler_registro(c)
                        itens=repo.listar_aulas(c) if escopo=='aula' else repo.listar_planos(c)
                        return gr.update(choices=[(f'{x.data} · {getattr(x,"tema","") or x.id}',x.id) for x in itens],value=None)
                    def carregar(c,i):
                        x=(repo.ler_aula if escopo=='aula' else repo.ler_plano)(c,i)
                        return [(c,i)]+[C.juntar(getattr(x,k)) if multi else getattr(x,k) for k,_,multi in spec]
                    def gravar(c,i,b,*valores):
                        if not c or list(b or [])!=[c,i]: raise ValueError('Carregue o item selecionado antes de salvar.')
                        alteracoes={k:C.linhas(v) if multi else v for (k,_,multi),v in zip(spec,valores)}
                        (M.editar_aula if escopo=='aula' else M.editar_plano)(repo,c,i,alteracoes)
                        invalidar(c)
                        return C.ok('Edição salva. A versão anterior está no backup. Exporte novamente os documentos para incluir as correções.')
                    atualizar.click(seguro(listar),cadastro,selecao)
                    ler.click(seguro(carregar),[cadastro,selecao],[vinc]+campos)
                    salvar.click(seguro(gravar),[cadastro,selecao,vinc]+campos,status)
            editor(escopo,titulo,especificacao)

        with gr.Accordion('Resetar dados salvos',open=False):
            gr.Markdown('**Atenção:** resetar uma aula remove essa aula; resetar o histórico apaga aulas, planos, materiais e repertório, preservando o cadastro. Excluir cadastro remove a pasta inteira. Documentos já exportados não são atualizados. Um backup é criado antes da remoção.')
            escopo=gr.Radio(choices=[('Remover aula selecionada','aula'),('Remover plano selecionado','plano'),('Zerar histórico do aluno ou turma','historico'),('Excluir aluno ou turma e todo o histórico','cadastro')],label='O que deseja resetar?')
            revisar=gr.Button('Revisar reset')
            pendente=gr.State(None)
            aviso=gr.HTML()
            confirmacao=gr.Textbox(label='Digite o código do cadastro para confirmar')
            with gr.Row():
                confirmar=gr.Button('Confirmar reset',variant='stop')
                cancelar=gr.Button('Cancelar')
            resultado=gr.HTML()
            def revisar_reset(c,e,a,p):
                r=repo.ler_registro(c)
                if e not in ('aula','plano','historico','cadastro'): raise ValueError('Escolha o que deseja resetar.')
                i=a if e=='aula' else p if e=='plano' else None
                if e in ('aula','plano'):
                    (repo.ler_aula if e=='aula' else repo.ler_plano)(c,i)
                return dict(codigo=c,escopo=e,id=i),C.aviso(f'Confirme: {e} de {r.identificacao or c}, código {c}. Item: {i or "todos os dados deste escopo"}.'),'',''
            def executar_reset(p,confirmado,c,e,a,pl):
                if not p or confirmado.strip()!=p['codigo']: raise ValueError('Revise o reset e digite o código exato do cadastro.')
                atual=a if e=='aula' else pl if e=='plano' else None
                if (c,e,atual)!=(p['codigo'],p['escopo'],p['id']): raise ValueError('A seleção mudou. Revise o reset novamente.')
                destino=M.resetar(repo,c,e,atual);invalidar(c)
                return None,'','',C.ok(f'Reset concluído. Backup criado: {destino.name}. Atualize a lista antes de editar outro item.')
            saidas=[pendente,aviso,confirmacao,resultado]
            revisar.click(seguro(revisar_reset),[cadastro,escopo,seletores['aula'],seletores['plano']],saidas)
            confirmar.click(seguro(executar_reset),[pendente,confirmacao,cadastro,escopo,seletores['aula'],seletores['plano']],saidas)
            cancelar.click(lambda:(None,'','',''),None,saidas)
    return {'tab':tab}
