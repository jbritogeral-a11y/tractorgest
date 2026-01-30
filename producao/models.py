from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Posto(models.Model):
    nome = models.CharField(max_length=100)
    ordem_sequencia = models.IntegerField(unique=True, help_text="Ordem do posto no fluxo (ex: 1, 2, 3...)")
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ['ordem_sequencia']

    def __str__(self):
        return f"{self.ordem_sequencia} - {self.nome}"

class Funcionario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, help_text="Nome completo do funcionário (ex: João Silva)")
    postos = models.ManyToManyField(Posto, related_name='funcionarios', help_text="Postos onde este funcionário pode trabalhar")
    telefone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nome

class Peca(models.Model):
    """Matéria-prima ou componentes necessários para criar um acessório"""
    nome = models.CharField(max_length=200)
    referencia = models.CharField(max_length=50, unique=True)
    stock_atual = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.referencia} - {self.nome}"

class Acessorio(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    pecas_necessarias = models.ManyToManyField(Peca, blank=True, help_text="Peças necessárias para fabricar este acessório")
    
    def __str__(self):
        return self.nome

class OrdemProducao(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO', 'Concluído'),
    ]
    numero_serie = models.CharField(max_length=50, unique=True)
    acessorio = models.ForeignKey(Acessorio, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    # Agora liga à tabela Posto em vez de ser um número fixo
    posto_atual = models.ForeignKey(Posto, on_delete=models.PROTECT, null=True, blank=True)
    
    # Campo para agendar/atribuir a um funcionário específico (opcional)
    funcionario_designado = models.ForeignKey(Funcionario, on_delete=models.PROTECT, null=True, blank=True, help_text="Atribuir a um funcionário específico (Opcional)")
    data_prevista = models.DateField(null=True, blank=True, help_text="Data prevista para conclusão")
    
    status_global = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')

    def __str__(self):
        return f"SN: {self.numero_serie} - {self.acessorio.nome}"

class TarefaProducao(models.Model):
    ordem = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, related_name='tarefas')
    posto = models.ForeignKey(Posto, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    inicio = models.DateTimeField(null=True, blank=True)
    fim = models.DateTimeField(null=True, blank=True)
    concluido = models.BooleanField(default=False)

    def iniciar_tarefa(self):
        self.inicio = timezone.now()
        self.save()

    def finalizar_tarefa(self):
        self.fim = timezone.now()
        self.concluido = True
        
        # Lógica automática: Procura o próximo posto baseado na sequência
        proximo = Posto.objects.filter(ordem_sequencia__gt=self.posto.ordem_sequencia).order_by('ordem_sequencia').first()
        
        if proximo:
            self.ordem.posto_atual = proximo
            self.ordem.status_global = 'PENDENTE' # Reseta status para o novo posto
        else:
            self.ordem.status_global = 'CONCLUIDO'
        
        self.ordem.save()
        self.save()
