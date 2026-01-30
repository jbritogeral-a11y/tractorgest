from django.contrib import admin
from .models import Acessorio, OrdemProducao, TarefaProducao, Funcionario, Posto

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

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'telefone')
    filter_horizontal = ('postos',)

@admin.register(Posto)
class PostoAdmin(admin.ModelAdmin):
    list_display = ('ordem_sequencia', 'nome')
    ordering = ('ordem_sequencia',)
