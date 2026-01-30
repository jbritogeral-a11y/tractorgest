from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import OrdemProducao, TarefaProducao, PerfilFuncionario

@login_required
def dashboard_funcionario(request):
    # 1. Tenta obter o perfil do funcionário para saber o posto
    try:
        perfil = request.user.perfilfuncionario
    except PerfilFuncionario.DoesNotExist:
        return render(request, 'producao/erro_perfil.html', {
            'mensagem': 'Utilizador sem Perfil de Funcionário. Contacte o Admin.'
        })

    posto_id = perfil.posto_padrao
    
    # 2. Verifica se o funcionário já tem alguma tarefa "aberta" (cronómetro a contar)
    tarefa_em_curso = TarefaProducao.objects.filter(
        funcionario=request.user,
        concluido=False
    ).first()

    # 3. Procura ordens que estão neste posto à espera de atenção
    # Excluímos as que já estão concluídas globalmente
    ordens_pendentes = OrdemProducao.objects.filter(
        posto_atual=posto_id
    ).exclude(status_global='CONCLUIDO')

    # Se já estiver a trabalhar numa, não mostramos essa na lista de "pendentes" para não confundir
    if tarefa_em_curso:
        ordens_pendentes = ordens_pendentes.exclude(id=tarefa_em_curso.ordem.id)

    return render(request, 'producao/dashboard.html', {
        'posto_nome': perfil.get_posto_padrao_display(),
        'tarefa_em_curso': tarefa_em_curso,
        'ordens_pendentes': ordens_pendentes,
    })

@login_required
def iniciar_tarefa(request, ordem_id):
    ordem = get_object_or_404(OrdemProducao, id=ordem_id)
    
    try:
        perfil = request.user.perfilfuncionario
    except PerfilFuncionario.DoesNotExist:
        return redirect('dashboard_funcionario')

    # Impede iniciar duas tarefas ao mesmo tempo
    if TarefaProducao.objects.filter(funcionario=request.user, concluido=False).exists():
        return redirect('dashboard_funcionario')

    # Cria o registo de início de trabalho
    TarefaProducao.objects.create(
        ordem=ordem,
        posto=perfil.posto_padrao,
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
