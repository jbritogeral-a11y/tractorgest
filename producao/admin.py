from django.contrib import admin
from .models import Acessorio, OrdemProducao, TarefaProducao, PerfilFuncionario

class TarefaInline(admin.TabularInline):
    model = TarefaProducao
    extra = 0
    readonly_fields = ('inicio', 'fim', 'funcionario')

@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = ('numero_serie', 'acessorio', 'posto_atual', 'status_global', 'data_criacao')
    list_filter = ('posto_atual', 'status_global', 'acessorio')
    search_fields = ('numero_serie',)
    inlines = [TarefaInline]

@admin.register(Acessorio)
class AcessorioAdmin(admin.ModelAdmin):
    list_display = ('nome',)

admin.site.register(PerfilFuncionario)

