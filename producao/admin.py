from django.contrib import admin
from .models import Acessorio, OrdemProducao, TarefaProducao, Funcionario, Posto, Peca

class TarefaInline(admin.TabularInline):
    model = TarefaProducao
    extra = 0
    readonly_fields = ('inicio', 'fim', 'funcionario')

@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = ('numero_serie', 'acessorio', 'posto_atual', 'funcionario_designado', 'status_global')
    list_editable = ('funcionario_designado',) # <--- Permite agendar diretamente na lista
    list_filter = ('posto_atual', 'status_global', 'acessorio')
    search_fields = ('numero_serie',)
    inlines = [TarefaInline]

@admin.register(Acessorio)
class AcessorioAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    filter_horizontal = ('pecas_necessarias',) # Interface bonita para selecionar muitas peças

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'telefone')
    filter_horizontal = ('postos',)

@admin.register(Posto)
class PostoAdmin(admin.ModelAdmin):
    list_display = ('ordem_sequencia', 'nome')
    ordering = ('ordem_sequencia',)

@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'nome', 'stock_atual')
    search_fields = ('referencia', 'nome')
