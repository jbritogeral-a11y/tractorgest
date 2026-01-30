from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_funcionario, name='login_funcionario'),
    path('logout/', views.logout_funcionario, name='logout_funcionario'),
    path('estatisticas/', views.dashboard_estatisticas, name='dashboard_estatisticas'),
    path('', views.dashboard_funcionario, name='dashboard_funcionario'),
    path('iniciar/<int:ordem_id>/', views.iniciar_tarefa, name='iniciar_tarefa'),
    path('finalizar/<int:tarefa_id>/', views.finalizar_tarefa, name='finalizar_tarefa'),
]
