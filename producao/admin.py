import calendar
import datetime
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Acessorio, OrdemProducao, TarefaProducao, Funcionario, Posto, Peca, Agendamento

class TarefaInline(admin.TabularInline):
    model = TarefaProducao
    extra = 0
    readonly_fields = ('inicio', 'fim', 'funcionario')

@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = ('numero_serie', 'acessorio', 'posto_atual', 'funcionario_designado', 'data_prevista', 'status_global')
    list_editable = ('funcionario_designado', 'data_prevista') # <--- Agenda completa (Quem e Quando) editável na lista
    list_filter = ('posto_atual', 'status_global', 'acessorio', 'data_prevista')
    search_fields = ('numero_serie',)
    inlines = [TarefaInline]

@admin.register(Acessorio)
class AcessorioAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    filter_horizontal = ('pecas_necessarias',) # Interface bonita para selecionar muitas peças

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo', 'telefone')
    filter_horizontal = ('postos',)

@admin.register(Posto)
class PostoAdmin(admin.ModelAdmin):
    list_display = ('ordem_sequencia', 'nome')
    ordering = ('ordem_sequencia',)

@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'nome', 'stock_atual')
    search_fields = ('referencia', 'nome')

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/producao/agendamento/change_list.html'
    list_display = ('numero_serie', 'acessorio', 'funcionario_designado', 'data_prevista', 'status_global')
    list_editable = ('funcionario_designado', 'data_prevista')
    
    def get_changeform_initial_data(self, request):
        # Preenche a data automaticamente quando clicas no dia do calendário
        initial = super().get_changeform_initial_data(request)
        if 'data_prevista' in request.GET:
            initial['data_prevista'] = request.GET.get('data_prevista')
        return initial

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Lógica do Calendário
        today = datetime.date.today()
        year = today.year
        month = today.month
        
        class ProductionCalendar(calendar.HTMLCalendar):
            def formatday(self, day, weekday):
                if day == 0:
                    return '<td class="noday">&nbsp;</td>'
                
                date_str = f"{year}-{month:02d}-{day:02d}"
                # Link para ADICIONAR nova tarefa neste dia
                add_url = reverse('admin:producao_agendamento_add') + f"?data_prevista={date_str}"
                # Contar tarefas existentes
                count = OrdemProducao.objects.filter(data_prevista=date_str).count()
                
                html = f'<td class="{self.cssclasses[weekday]}" style="height: 100px; vertical-align: top; border: 1px solid #ddd; padding: 5px; background: white;">'
                html += f'<div style="display:flex; justify-content:space-between;">'
                html += f'<strong>{day}</strong>'
                html += f'<a href="{add_url}" style="text-decoration:none; font-size:1.5em; color:#28a745; font-weight:bold;" title="Agendar Nova Tarefa">➕</a>'
                html += f'</div>'
                if count > 0:
                    html += f'<div style="margin-top:5px; background:#e3f2fd; padding:3px; border-radius:3px; font-size:0.8em;">📋 {count} tarefas</div>'
                return html + '</td>'

        html_cal = ProductionCalendar().formatmonth(year, month)
        extra_context['calendar'] = mark_safe(html_cal)
        return super().changelist_view(request, extra_context=extra_context)
