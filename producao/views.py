from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.admin.views.decorators import staff_member_required
from .models import OrdemProducao, TarefaProducao, Funcionario, Posto, Acessorio

def login_funcionario(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        try:
            funcionario = Funcionario.objects.get(codigo=codigo)
            request.session['funcionario_id'] = funcionario.id
            return redirect('dashboard_funcionario')
        except Funcionario.DoesNotExist:
            return render(request, 'producao/login_funcionario.html', {'erro': 'Código inválido'})
    return render(request, 'producao/login_funcionario.html')

def logout_funcionario(request):
    if 'funcionario_id' in request.session:
        del request.session['funcionario_id']
    return redirect('login_funcionario')

def dashboard_funcionario(request):
    # Verificação de Sessão Manual (Substitui o @login_required)
    if 'funcionario_id' not in request.session:
        return redirect('login_funcionario')

    try:
        funcionario = Funcionario.objects.get(id=request.session['funcionario_id'])
    except Funcionario.DoesNotExist:
        return redirect('logout_funcionario')

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
        funcionario=funcionario,
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

def iniciar_tarefa(request, ordem_id):
    if 'funcionario_id' not in request.session:
        return redirect('login_funcionario')
        
    ordem = get_object_or_404(OrdemProducao, id=ordem_id)
    funcionario = Funcionario.objects.get(id=request.session['funcionario_id'])

    # Impede iniciar duas tarefas ao mesmo tempo
    if TarefaProducao.objects.filter(funcionario=funcionario, concluido=False).exists():
        return redirect('dashboard_funcionario')

    # Verifica se o funcionário tem acesso ao posto atual da ordem
    if ordem.posto_atual not in funcionario.postos.all():
        return redirect('dashboard_funcionario') # Ou mostrar erro de permissão

    # Cria o registo de início de trabalho
    TarefaProducao.objects.create(
        ordem=ordem,
        posto=ordem.posto_atual,
        funcionario=funcionario,
        inicio=timezone.now()
    )

    # Atualiza o estado da ordem para "Em Andamento"
    ordem.status_global = 'EM_ANDAMENTO'
    ordem.save()

    return redirect('dashboard_funcionario')

def finalizar_tarefa(request, tarefa_id):
    if 'funcionario_id' not in request.session:
        return redirect('login_funcionario')
        
    funcionario = Funcionario.objects.get(id=request.session['funcionario_id'])
    tarefa = get_object_or_404(TarefaProducao, id=tarefa_id, funcionario=funcionario)
    # Chama a função que criámos no models.py (fecha tempo e muda posto)
    tarefa.finalizar_tarefa() 
    return redirect('dashboard_funcionario')

# --- DASHBOARD DE ESTATÍSTICAS (ADMIN) ---
@staff_member_required
def dashboard_estatisticas(request):
    # 1. Total Produzido
    total_concluido = OrdemProducao.objects.filter(status_global='CONCLUIDO').count()
    
    # 2. Peças por Funcionário
    pecas_por_func = TarefaProducao.objects.filter(concluido=True).values('funcionario__nome').annotate(total=Count('id'))
    
    # 3. Ordens Atrasadas (Agendadas para o passado e não concluídas)
    hoje = timezone.now().date()
    atrasadas = OrdemProducao.objects.filter(data_prevista__lt=hoje).exclude(status_global='CONCLUIDO')

    return render(request, 'producao/estatisticas.html', {
        'total_concluido': total_concluido,
        'pecas_por_func': pecas_por_func,
        'atrasadas': atrasadas,
    })
