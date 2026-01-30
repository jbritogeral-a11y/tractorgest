from django.contrib import admin
from django.urls import path, include  # <--- Não esqueças de importar o include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Adiciona as rotas de login/logout padrão
    path('', include('producao.urls')), # <--- Isto define que a página inicial vai para a produção
]
