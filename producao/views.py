from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import OrdemProducao, TarefaProducao, Funcionario, Posto, Acessorio

@login_required
def dashboard_funcionario(request):
    # 1. Tenta obter o perfil do funcionário
    try:
        funcionario = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'producao/erro_perfil.html', {
            'mensagem': 'Utilizador sem Perfil de Funcionário. Contacte o Admin.'
        })

    # Obtém todos os postos onde este funcionário pode trabalhar
    postos_autorizados = funcionario.postos.all()
    
    # --- LÓGICA PARA O POSTO 1 (INÍCIO DE PRODUÇÃO) ---
    # Verifica se o funcionário tem acesso ao primeiro posto da linha
    primeiro_posto = Posto.objects.order_by('ordem_sequencia').first()
    e_posto_inicial = False
    acessorios_disponiveis = []

    if primeiro_posto and primeiro_posto in postos_autorizados:
        e_posto_inicial = True
        acessorios_disponiveis = Acessorio.objects.all()

        # Se for um pedido para CRIAR uma nova ordem (Botão Iniciar Produção)
        if request.method == 'POST' and 'criar_ordem' in request.POST:
            numero_serie = request.POST.get('numero_serie')
            acessorio_id = request.POST.get('acessorio')
            
            if numero_serie and acessorio_id:
                # 1. Cria a Ordem
                nova_ordem = OrdemProducao.objects.create(
                    numero_serie=numero_serie,
                    acessorio_id=acessorio_id,
                    posto_atual=primeiro_posto,
                    status_global='PENDENTE'
                )
                # 2. Redireciona para "iniciar_tarefa" para começar o cronómetro logo
                return redirect('iniciar_tarefa', ordem_id=nova_ordem.id)

    # 2. Verifica se o funcionário já tem alguma tarefa "aberta" (cronómetro a contar)
    tarefa_em_curso = TarefaProducao.objects.filter(
        funcionario=request.user,
        concluido=False
    ).first()

    # 3. Base de procura: Ordens pendentes NOS POSTOS AUTORIZADOS
    base_ordens = OrdemProducao.objects.filter(
        posto_atual__in=postos_autorizados
    ).exclude(status_global='CONCLUIDO')

    # Se já estiver a trabalhar numa, não mostramos essa na lista de "pendentes" para não confundir
    if tarefa_em_curso:
        base_ordens = base_ordens.exclude(id=tarefa_em_curso.ordem.id)

    # SISTEMA DE AGENDAMENTO: Separar o que é "Meu" do que é "Geral"
    # Lista 1: Agendadas especificamente para este funcionário (Prioridade Alta)
    ordens_agendadas = base_ordens.filter(funcionario_designado=funcionario).order_by('data_prevista', 'id')

    # Lista 2: Livres (Ninguém designado) - Qualquer um no posto pode pegar
    ordens_gerais = base_ordens.filter(funcionario_designado__isnull=True)

    return render(request, 'producao/dashboard.html', {
        'funcionario': funcionario,
        'postos': postos_autorizados,
        'e_posto_inicial': e_posto_inicial,
        'acessorios': acessorios_disponiveis,
        'tarefa_em_curso': tarefa_em_curso,
        'ordens_agendadas': ordens_agendadas,
        'ordens_gerais': ordens_gerais,
    })

@login_required
def iniciar_tarefa(request, ordem_id):
    ordem = get_object_or_404(OrdemProducao, id=ordem_id)
    
    try:
        funcionario = request.user.funcionario
    except Funcionario.DoesNotExist:
        return redirect('dashboard_funcionario')

    # Impede iniciar duas tarefas ao mesmo tempo
    if TarefaProducao.objects.filter(funcionario=request.user, concluido=False).exists():
        return redirect('dashboard_funcionario')

    # Verifica se o funcionário tem acesso ao posto atual da ordem
    if ordem.posto_atual not in funcionario.postos.all():
        return redirect('dashboard_funcionario') # Ou mostrar erro de permissão

    # Cria o registo de início de trabalho
    TarefaProducao.objects.create(
        ordem=ordem,
        posto=ordem.posto_atual,
        funcionario=request.user,
        inicio=timezone.now()
    )

    # Atualiza o estado da ordem para "Em Andamento"
    ordem.status_global = 'EM_ANDAMENTO'
    ordem.save()

    return redirect('dashboard_funcionario')

@login_required
def finalizar_tarefa(request, tarefa_id):
    tarefa = get_object_or_404(TarefaProducao, id=tarefa_id, funcionario=request.user)
    # Chama a função que criámos no models.py (fecha tempo e muda posto)
    tarefa.finalizar_tarefa() 
    return redirect('dashboard_funcionario')
