from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Definição dos Postos
POSTOS = [
    (1, 'Posto 1 - Preparação'),
    (2, 'Posto 2 - Pré-Montagem'),
    (3, 'Posto 3 - Soldadura'),
    (4, 'Posto 4 - Limpeza'),
    (5, 'Posto 5 - Pintura'),
    (6, 'Posto 6 - Montagem'),
]

class PerfilFuncionario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    posto_padrao = models.IntegerField(choices=POSTOS, default=1)

    def __str__(self):
        return f"{self.user.username} - {self.get_posto_padrao_display()}"

class Acessorio(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
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
    posto_atual = models.IntegerField(choices=POSTOS, default=1)
    status_global = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')

    def __str__(self):
        return f"SN: {self.numero_serie} - {self.acessorio.nome}"

class TarefaProducao(models.Model):
    ordem = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, related_name='tarefas')
    posto = models.IntegerField(choices=POSTOS)
    funcionario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    inicio = models.DateTimeField(null=True, blank=True)
    fim = models.DateTimeField(null=True, blank=True)
    concluido = models.BooleanField(default=False)

    def iniciar_tarefa(self):
        self.inicio = timezone.now()
        self.save()

    def finalizar_tarefa(self):
        self.fim = timezone.now()
        self.concluido = True
        # Lógica automática: Se não for o último posto, avança para o próximo
        if self.posto < 6:
            self.ordem.posto_atual = self.posto + 1
        else:
            self.ordem.status_global = 'CONCLUIDO'
        
        self.ordem.save()
        self.save()
