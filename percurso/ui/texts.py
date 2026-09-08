"""Todo texto visível ao professor, em Português do Brasil (SPEC §6.1). Fonte única."""

APP_NOME = "Percurso"
APP_SUBTITULO = "Plataforma de inteligência pedagógica"
APP_FRASE = "Cada aula começa de onde a anterior terminou."

# --- modos -------------------------------------------------------------------
MODO_ESSENCIAL = "Modo Essencial ativo"
MODO_INTELIGENTE = "Modo Inteligente (Gemini) ativo"
AVISO_ESSENCIAL = "Modo Essencial ativo. Alguns recursos avançados de geração e síntese estarão indisponíveis nesta sessão."
PERGUNTA_GEMINI = "Deseja utilizar inteligência Gemini nesta sessão?"
BTN_USAR_GEMINI = "USAR GEMINI"
BTN_SEM_GEMINI = "CONTINUAR SEM GEMINI"
GEMINI_NAO_CONFIGURADO = "Gemini ainda não está configurado."
BTN_APRENDER_CONFIGURAR = "APRENDER A CONFIGURAR"
GEMINI_CHAVE_INVALIDA = "A chave informada não foi aceita pelo Google. Verifique e tente novamente, ou continue em Modo Essencial."
GEMINI_SEM_RESPOSTA = "Gemini não respondeu. Você pode tentar novamente ou continuar em Modo Essencial."
GEMINI_VALIDANDO = "A resposta não passou pela validação. Tentando corrigir…"
GEMINI_FALLBACK = "Não foi possível obter uma resposta válida da Gemini. Usando o modelo pedagógico do Modo Essencial."
GEMINI_CHAVE_SESSAO = "Chave para usar apenas nesta sessão (não é gravada em lugar nenhum)"
GEMINI_ATIVADO = "Gemini ativado para esta sessão."
CONSENTIMENTO_TRECHOS = "Permitir que trechos da minha biblioteca sejam enviados à Gemini API para análise?"

# --- transparência / LGPD ---------------------------------------------------
TRANSPARENCIA_DRIVE = (
    "O Percurso utilizará uma pasta própria no seu Google Drive para armazenar seus dados pedagógicos "
    "e sua biblioteca. Nenhum arquivo fora dessa área será alterado automaticamente."
)
DRIVE_CONECTADO = "Drive conectado ✓"
ESTRUTURA_CRIADA = "Estrutura criada ✓"
DADOS_RECUPERADOS = "Seus dados foram recuperados ✓"
MIGRACAO = "Versão antiga detectada. Fazendo backup e atualizando seus dados…"
ERRO_CLONE = "Não foi possível baixar o Percurso agora (problema de rede). Aguarde alguns segundos e execute a célula novamente."

# --- tela inicial -------------------------------------------------------------
BTN_CONTINUAR = "CONTINUAR ALUNO OU TURMA"
BTN_NOVO_REGISTRO = "NOVO REGISTRO"
BTN_PLANEJAR = "PLANEJAR AULA"
BTN_PESQUISAR = "PESQUISAR"
BTN_BIBLIOTECA = "MINHA BIBLIOTECA"
BTN_RELATORIOS = "RELATÓRIOS"
BTN_CONFIGURACOES = "CONFIGURAÇÕES"
BTN_APOIAR = "♡ Apoiar o Percurso"
BTN_AJUDA = "AJUDA"

ABA_INICIO = "Início"
ABA_CONTINUAR = "Continuar"
ABA_NOVO = "Novo registro"
ABA_AULA = "Registrar aula"
ABA_PLANEJAR = "Planejar aula"
ABA_HISTORICO = "Histórico"
ABA_BIBLIOTECA = "Minha biblioteca"
ABA_PESQUISAR = "Pesquisar"
ABA_RELATORIOS = "Relatórios"
ABA_CONFIG = "Configurações"
ABA_APOIO = "Apoiar"
ABA_AJUDA = "Ajuda"

BOAS_VINDAS = "Bem-vindo(a) ao Percurso."
ONBOARDING_INTRO = (
    "O Percurso guarda a memória pedagógica de cada aluno ou turma: o que foi trabalhado, o que consolidou, "
    "o que ainda está em desenvolvimento e o que deve acontecer na próxima aula. "
    "Comece criando um registro ou, se já tem um código, use **Continuar**."
)
ONBOARDING_PERFIL = "Se quiser, preencha seu perfil em **Configurações** (opcional)."

# --- continuar ---------------------------------------------------------------
DIGITE_CODIGO = "Digite o código do aluno ou turma"
PLACEHOLDER_CODIGO = "PCR-XXXXXX"
BTN_CARREGAR = "CARREGAR"
CODIGO_NAO_ENCONTRADO = "Não encontramos nenhum registro com este código. Verifique se digitou corretamente."
CODIGO_INVALIDO = "Código inválido. O formato é PCR seguido de 6 letras ou números (ex.: PCR-7K4M2Q)."
SEM_AULAS = "Este registro ainda não possui aulas."
BTN_PRIMEIRA_AULA = "CRIAR PRIMEIRA AULA"
BTN_AULA_JA_REALIZADA = "REGISTRAR AULA JÁ REALIZADA"
BTN_CONTINUAR_DE_ONDE_PARAMOS = "CONTINUAR DE ONDE PARAMOS"
BTN_FAZER_REVISAO = "FAZER REVISÃO"
BTN_NOVA_UNIDADE = "CRIAR NOVA AULA (nova unidade)"
BTN_EXTRAORDINARIA = "AULA EXTRAORDINÁRIA"
BTN_ALTERAR_PLANEJAMENTO = "ALTERAR PLANEJAMENTO"
BTN_VER_HISTORICO = "VER HISTÓRICO"
BTN_GERAR_RELATORIO = "GERAR RELATÓRIO"
NENHUM_REGISTRO_CARREGADO = "Nenhum aluno ou turma carregado. Use a aba **Continuar** e digite o código."

# --- novo registro -----------------------------------------------------------
NOVO_TITULO = "Novo registro"
NOVO_TIPO = "Tipo de registro"
NOVO_IDENTIFICACAO = "Identificação (primeiro nome, iniciais ou pseudônimo)"
NOVO_IDENTIFICACAO_AJUDA = "Recomendamos não usar sobrenome. Nunca pedimos CPF, RG ou endereço."
NOVO_INSTRUMENTO = "Instrumento ou área"
NOVO_INSTRUMENTO_OUTRO = "Se escolheu 'Outro', qual?"
NOVO_NIVEL = "Nível"
NOVO_IDADE = "Idade (opcional)"
NOVO_FAIXA_ETARIA = "Faixa etária da turma (ex.: 9–11 anos)"
NOVO_MODALIDADE = "Modalidade"
NOVO_MODALIDADE_OUTRO = "Se escolheu 'Outro', qual?"
NOVO_CONTEXTO = "Contexto"
NOVO_CURRICULO = "Referência curricular"
NOVO_DIA = "Dia habitual"
NOVO_INICIO = "Horário de início (HH:MM)"
NOVO_DURACAO = "Duração da aula (minutos)"
NOVO_CONHECIMENTOS = "Conhecimentos prévios (um por linha)"
NOVO_OBJETIVOS = "Objetivos (um por linha)"
NOVO_RECURSOS = "Recursos habituais"
NOVO_ADAPTACOES = "Adaptações (texto livre, opcional)"
NOVO_METODOLOGIAS = "Metodologias"
NOVO_OBSERVACOES = "Observações"
NOVO_TURMA_NOME = "Nome da turma"
NOVO_TURMA_QTD = "Quantidade de alunos"
NOVO_TURMA_ALUNOS = "Lista de alunos (opcional; um por linha, primeiro nome ou iniciais)"
BTN_CRIAR_REGISTRO = "CRIAR REGISTRO"
REGISTRO_CRIADO = "**Registro criado. Código: {codigo}. Guarde este código.**"
REGISTRO_CRIADO_DICA = "Você usará este código para continuar de onde parou em qualquer sessão. Ele não revela nome, idade, instrumento ou turma."
IDENTIFICACAO_OBRIGATORIA = "Informe uma identificação (pode ser só o primeiro nome ou iniciais)."

# --- registrar aula ----------------------------------------------------------
AULA_TITULO = "Registrar aula"
AULA_DATA = "Data (AAAA-MM-DD ou DD/MM/AAAA)"
AULA_TIPO = "Tipo de aula"
AULA_HORARIO_PREVISTO = "Horário previsto"
AULA_MANTER = "MANTER"
AULA_ALTERAR = "ALTERAR"
AULA_INICIO_REAL = "Início real (HH:MM)"
AULA_TERMINO_REAL = "Término real (HH:MM)"
AULA_FREQUENCIA = "Frequência"
AULA_FREQUENCIA_TURMA = "Presenças (marque os presentes)"
AULA_N_PRESENTES = "Quantos alunos presentes?"
AULA_CONTEUDO_PLANEJADO = "Conteúdo planejado (um por linha)"
AULA_CONTEUDO_REALIZADO = "Conteúdos trabalhados (um por linha)"
AULA_CLASSIFICACAO = "Classifique cada conteúdo trabalhado"
BTN_CLASSIFICAR = "PREPARAR CLASSIFICAÇÃO"
AULA_OBJETIVOS = "Objetivos (um por linha)"
AULA_ATIVIDADES = "Atividades realizadas (uma por linha)"
AULA_MATERIAIS = "Materiais usados (um por linha)"
AULA_RENDIMENTO = "Rendimento (1 a 5; deixe em branco o que não observou)"
AULA_AVALIACAO = "Avaliação qualitativa"
AULA_DIFICULDADES = "Dificuldades observadas (uma por linha)"
AULA_CONQUISTAS = "Conquistas (uma por linha)"
AULA_OBSERVACOES = "Observações"
AULA_TAREFAS = "Tarefas para casa (uma por linha)"
AULA_PROXIMO_PASSO = "Próximo passo"
AULA_REPERTORIO = "Repertório trabalhado (um por linha)"
AULA_UNIDADE = "Unidade (deixe vazio para manter a atual)"
BTN_SALVAR_AULA = "SALVAR AULA"
AULA_SALVA = "Aula salva ✓ Estado pedagógico atualizado. Esta é a <b>Aula {numero}</b> de {codigo}."
AULA_DATA_INVALIDA = "Data inválida. Use AAAA-MM-DD ou DD/MM/AAAA."
AULA_HORA_INVALIDA = "Horário inválido. Use HH:MM (ex.: 15:00)."
AULA_CONTEUDO_OBRIGATORIO = "Informe ao menos um conteúdo trabalhado, ou marque a frequência como falta/cancelada."

# --- planejar ------------------------------------------------------------------
PLANEJAR_TITULO = "Planejar aula"
PLANEJAR_TIPO = "Tipo de aula"
PLANEJAR_CONTEUDO = "Conteúdo a trabalhar (vazio = 'O que devo trabalhar agora?')"
PLANEJAR_OBJETIVO = "Objetivo (opcional)"
PLANEJAR_DURACAO = "Duração (minutos)"
PLANEJAR_RECURSOS = "Recursos disponíveis hoje"
PLANEJAR_OBS = "Observações para esta aula"
PLANEJAR_NOVA_UNIDADE = "Nome da nova unidade (para 'nova unidade')"
PLANEJAR_ONDE = "Onde pesquisar?"
BTN_SUGERIR = "O QUE DEVO TRABALHAR AGORA?"
BTN_GERAR_PLANO = "GERAR PLANO"
BTN_REGISTRAR_A_PARTIR_DO_PLANO = "REGISTRAR AULA A PARTIR DESTE PLANO"
BTN_DESCARTAR_PLANO = "DESCARTAR PLANO"
PLANO_SALVO = "Plano salvo em planos/ ✓"
PLANO_DESCARTADO = "Plano descartado."
PLANO_PREENCHIDO = "Formulário de aula pré-preenchido com o plano. Vá para a aba **Registrar aula**."
PROXIMO_PASSO_SUGERIDO = "Próximo passo sugerido"
BTN_ADAPTAR_DURACAO = "ADAPTAR DURAÇÃO"
NENHUM_PLANO = "Nenhum plano gerado ainda nesta sessão."

# --- histórico ---------------------------------------------------------------
HISTORICO_TITULO = "Histórico"
HISTORICO_BUSCA = "Buscar no histórico"
HISTORICO_BUSCA_CONTEUDO = "Conteúdo contém"
HISTORICO_BUSCA_DIFICULDADE = "Dificuldade contém"
HISTORICO_BUSCA_INICIO = "De (AAAA-MM-DD)"
HISTORICO_BUSCA_FIM = "Até (AAAA-MM-DD)"
HISTORICO_BUSCA_SITUACAO = "Situação"
HISTORICO_PERGUNTA_LIVRE = "Pergunta livre sobre o histórico (Modo Inteligente)"
BTN_BUSCAR = "BUSCAR"
BTN_ABRIR_AULA = "ABRIR AULA"
HISTORICO_SELECIONE = "Selecione uma aula"
HISTORICO_VAZIO = "Nenhuma aula encontrada."
BTN_EXCLUIR_AULA = "EXCLUIR ESTA AULA"
AULA_EXCLUIDA = "Aula excluída. Estado pedagógico recalculado."

# --- repertório --------------------------------------------------------------
REPERTORIO_TITULO = "Repertório"
REPERTORIO_OBRA = "Obra"
REPERTORIO_COMPOSITOR = "Compositor"
REPERTORIO_ARRANJO = "Arranjo"
REPERTORIO_NIVEL = "Nível"
REPERTORIO_ESTADO = "Estado"
BTN_ADICIONAR_REPERTORIO = "ADICIONAR AO REPERTÓRIO"
BTN_ATUALIZAR_REPERTORIO = "ATUALIZAR ESTADO"
REPERTORIO_SALVO = "Repertório atualizado ✓"

# --- configurações -----------------------------------------------------------
CONFIG_TITULO = "Configurações"
CONFIG_PERFIL = "Perfil do professor (todos os campos são opcionais)"
CONFIG_NOME = "Nome"
CONFIG_INSTITUICAO = "Instituição"
CONFIG_CIDADE = "Cidade"
CONFIG_ESTADO = "Estado (UF)"
CONFIG_AREA = "Área principal"
CONFIG_NIVEIS = "Níveis de ensino"
CONFIG_DURACAO = "Duração padrão de aula (minutos)"
CONFIG_CURRICULO = "Currículo padrão"
CONFIG_PREFERENCIAS = "Preferências pedagógicas"
CONFIG_METODOLOGIAS = "Metodologias preferidas"
CONFIG_FUSO = "Fuso horário"
CONFIG_EMAIL = "E-mail de contato (opcional)"
BTN_SALVAR_PERFIL = "SALVAR PERFIL"
PERFIL_SALVO = "Perfil salvo ✓"
CONFIG_PERFIS_INSTRUMENTAIS = "Perfis instrumentais (hipóteses pedagógicas editáveis)"
CONFIG_ESCOLHER_PERFIL = "Instrumento ou área"
BTN_CARREGAR_PERFIL = "CARREGAR PERFIL"
BTN_SALVAR_PERFIL_INSTR = "SALVAR MINHA VERSÃO"
BTN_RESTAURAR_PERFIL = "RESTAURAR ORIGINAL"
PERFIL_INSTR_SALVO = "Sua versão do perfil foi salva em configuracoes/perfis/ ✓ O original do Percurso permanece intacto."
PERFIL_INSTR_RESTAURADO = "Perfil restaurado para o original ✓"
PERFIL_INSTR_INVALIDO = "O texto não é um JSON válido. Corrija e tente novamente."
CONFIG_RUBRICAS = "Critérios próprios de avaliação"
CONFIG_RUBRICA_NOVO_ID = "Identificador (sem espaços, ex.: expressao)"
CONFIG_RUBRICA_NOVO_ROTULO = "Nome do critério"
BTN_ADICIONAR_CRITERIO = "ADICIONAR CRITÉRIO"
BTN_REMOVER_CRITERIO = "REMOVER CRITÉRIO"
CRITERIO_SALVO = "Critérios atualizados ✓"
CONFIG_PRIVACIDADE = "Privacidade e seus dados"
BTN_EXPORTAR_TUDO = "EXPORTAR MEUS DADOS"
BTN_EXPORTAR_REGISTRO = "EXPORTAR UM REGISTRO"
BTN_EXCLUIR_REGISTRO = "EXCLUIR REGISTRO"
BTN_EXCLUIR_BIBLIOTECA = "EXCLUIR BIBLIOTECA"
BTN_APAGAR_LOCAIS = "APAGAR DADOS LOCAIS"
BTN_CONFIRMAR = "TEM CERTEZA? CONFIRMAR"
BTN_CANCELAR = "CANCELAR"
CONFIRMAR_EXCLUSAO = "Tem certeza? Os itens abaixo serão removidos (um backup ficará em backups/ por 30 dias):"
EXCLUSAO_CONCLUIDA = "Registro excluído. Backup salvo em backups/{pasta}."
BIBLIOTECA_EXCLUIDA = "Biblioteca excluída (arquivos, textos e índices). Backup salvo em backups/{pasta}."
LOCAIS_APAGADOS = "Dados locais da sessão apagados. Nada foi removido do seu Drive."
EXPORTACAO_PRONTA = "Exportação pronta: {arquivo}"
CONFIG_DIAGNOSTICO = "Diagnóstico"
BTN_DIAGNOSTICO = "DIAGNÓSTICO"
DIAGNOSTICO_INTRO = "Últimas linhas do registro técnico (sem chaves nem dados de alunos):"
CONFIG_BACKUPS = "Backups"
BTN_REMOVER_BACKUP = "REMOVER BACKUP SELECIONADO"
BACKUP_REMOVIDO = "Backup removido."

# --- apoio -------------------------------------------------------------------
APOIO_TITULO = "Apoie o Percurso"
APOIO_QR = "Escaneie com seu celular"
BTN_CONTRIBUIR = "CONTRIBUIR PELO MERCADO PAGO"
APOIO_FINALIDADE = "Seu apoio ajuda a financiar: novos recursos · manutenção · expansão para outras áreas · melhoria da biblioteca pedagógica · evolução da plataforma"
APOIO_LEMBRETE_TITULO = "Ajude o Percurso a continuar crescendo."
APOIO_LEMBRETE_CORPO = (
    "O Percurso é desenvolvido de forma independente e permanece gratuito. Se a ferramenta tem contribuído "
    "para seu trabalho, considere apoiar sua manutenção e o desenvolvimento de novos recursos."
)
BTN_APOIAR_MP = "APOIAR PELO MERCADO PAGO"
BTN_CONTINUAR_NO_PERCURSO = "CONTINUAR NO PERCURSO"
APOIO_SEM_BLOQUEIO = "Nenhuma função será bloqueada."
APOIO_LINK_NAO_CONFIGURADO = "O link de contribuição ainda não foi configurado pelo responsável pelo projeto."

# --- Modo Inteligente (E2) -----------------------------------------------------
BTN_CONSENTIR_TRECHOS_SIM = "SIM"
BTN_CONSENTIR_TRECHOS_NAO = "NÃO"
CONSENTIMENTO_REGISTRADO = "Preferência registrada para esta sessão."
RESUMO_TITULO = "Resumo pedagógico"
BTN_REESCREVER_RESUMO = "REESCREVER RESUMO COM GEMINI"
BTN_SALVAR_RESUMO = "SALVAR MINHA EDIÇÃO DO RESUMO"
RESUMO_REESCRITO = "Resumo reescrito com apoio de IA ✓ Você pode editar e salvar."
RESUMO_SALVO = "Resumo salvo ✓"
RESUMO_ORIGEM = {"template": "gerado por template (sem IA)", "gemini": "gerado com apoio de IA", "professor": "editado pelo professor"}
BTN_PROPOR_CLASSIFICACAO = "PEDIR PROPOSTA DE CLASSIFICAÇÃO À IA"
CLASSIFICACAO_PROPOSTA = "Proposta da IA aplicada. Confira cada item e corrija o que for preciso antes de salvar."
SOMENTE_MODO_INTELIGENTE = "Este recurso precisa do Modo Inteligente (Gemini) ativo nesta sessão."

# --- erros genéricos ---------------------------------------------------------
ERRO_GENERICO = "Algo não saiu como esperado. Seus dados anteriores estão preservados. Se o problema continuar, use DIAGNÓSTICO em Configurações."
ERRO_GRAVACAO = "Não foi possível gravar no Drive agora. Verifique a conexão e tente novamente. Nada do que já estava salvo foi alterado."

# --- rótulos de opções --------------------------------------------------------
TIPOS_REGISTRO = {"individual": "Individual", "dupla": "Dupla", "turma": "Turma"}
MODALIDADES = {
    "individual": "Individual",
    "dupla": "Dupla",
    "turma": "Turma",
    "coral": "Coral",
    "banda": "Banda",
    "percepcao_musical": "Percepção musical",
    "musicalizacao": "Musicalização",
    "oficina": "Oficina",
    "pratica_conjunto": "Prática de conjunto",
    "outro": "Outro",
}
NIVEIS = {"iniciante": "Iniciante", "basico": "Básico", "intermediario": "Intermediário", "avancado": "Avançado"}
CONTEXTOS = {
    "escola": "Escola",
    "conservatorio": "Conservatório",
    "aula_particular": "Aula particular",
    "projeto_social": "Projeto social",
    "curso_livre": "Curso livre",
    "outro": "Outro",
}
CURRICULOS = {
    "bncc": "BNCC",
    "bncc_crmg": "BNCC + CRMG",
    "proprio": "Currículo próprio",
    "curso_livre": "Curso livre",
    "conservatorio": "Conservatório",
    "nenhum": "Nenhuma",
}
DIAS = {
    "segunda": "Segunda-feira",
    "terca": "Terça-feira",
    "quarta": "Quarta-feira",
    "quinta": "Quinta-feira",
    "sexta": "Sexta-feira",
    "sabado": "Sábado",
    "domingo": "Domingo",
}
RECURSOS = {
    "quadro": "Quadro",
    "caixa_de_som": "Caixa de som",
    "instrumentos": "Instrumentos",
    "projetor": "Projetor",
    "celulares": "Celulares",
    "impressao": "Impressão",
    "nenhum": "Nenhum",
    "outro": "Outro",
}
METODOLOGIAS = {
    "dalcroze": "Dalcroze",
    "orff": "Orff",
    "kodaly": "Kodály",
    "gordon": "Gordon",
    "swanwick": "Swanwick",
    "propria": "Abordagem própria",
    "combinacao": "Combinação",
    "sem_preferencia": "Sem preferência",
}
FREQUENCIAS = {
    "presente": "Presente",
    "falta": "Falta",
    "falta_justificada": "Falta justificada",
    "reposicao": "Reposição",
    "aula_extra": "Aula extra",
    "cancelada_professor": "Cancelada pelo professor",
    "cancelada_instituicao": "Cancelada pela instituição",
}
TIPOS_AULA = {
    "continuidade": "Continuidade",
    "revisao": "Revisão",
    "nova_unidade": "Nova unidade",
    "extraordinaria": "Extraordinária",
    "retroativa": "Registro retroativo (aula já realizada)",
}
SITUACOES = {"consolidado": "Consolidado", "em_desenvolvimento": "Em desenvolvimento", "dificuldade": "Dificuldade"}
ESTADOS_REPERTORIO = {"em_estudo": "Em estudo", "concluido": "Concluído", "apresentacao": "Apresentação", "revisao": "Revisão"}
NIVEIS_ENSINO = ["Educação Infantil", "Ensino Fundamental I", "Ensino Fundamental II", "Ensino Médio", "Adultos", "Livre"]
ORIGENS_FONTE = {"biblioteca": "📚 Minha Biblioteca", "curricular": "🏛 Fonte curricular oficial", "academica": "🎓 Literatura acadêmica", "externa": "🌐 Fonte externa"}


def opcoes(mapa: dict) -> list:
    """[(rótulo, valor)] para componentes Gradio."""
    return [(v, k) for k, v in mapa.items()]


def rotulo(mapa: dict, valor: str) -> str:
    return mapa.get(valor, valor)
