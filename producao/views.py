from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import OrdemProducao, TarefaProducao, Funcionario

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
    
    # 2. Verifica se o funcionário já tem alguma tarefa "aberta" (cronómetro a contar)
    tarefa_em_curso = TarefaProducao.objects.filter(
        funcionario=request.user,
        concluido=False
    ).first()

    # 3. Procura ordens pendentes NOS POSTOS AUTORIZADOS
    ordens_pendentes = OrdemProducao.objects.filter(
        posto_atual__in=postos_autorizados
    ).exclude(status_global='CONCLUIDO')

    # Filtro de Agendamento: Mostra se for para MIM ou se for para QUALQUER UM (None)
    ordens_pendentes = ordens_pendentes.filter(
        Q(funcionario_designado=request.user) | Q(funcionario_designado__isnull=True)
    )

    # Se já estiver a trabalhar numa, não mostramos essa na lista de "pendentes" para não confundir
    if tarefa_em_curso:
        ordens_pendentes = ordens_pendentes.exclude(id=tarefa_em_curso.ordem.id)

    return render(request, 'producao/dashboard.html', {
        'funcionario': funcionario,
        'postos': postos_autorizados,
        'tarefa_em_curso': tarefa_em_curso,
        'ordens_pendentes': ordens_pendentes,
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
