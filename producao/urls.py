from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_funcionario, name='dashboard_funcionario'),
    path('iniciar/<int:ordem_id>/', views.iniciar_tarefa, name='iniciar_tarefa'),
    path('finalizar/<int:tarefa_id>/', views.finalizar_tarefa, name='finalizar_tarefa'),
]
