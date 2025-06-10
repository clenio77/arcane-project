from django.urls import path
from . import views, views_advanced

urlpatterns = [
    # URLs básicas
    path('treinar_ia', views.treinar_ia, name="treinar_ia"),
    path('chat', views.chat, name="chat"),
    path('stream_response', views.stream_response, name="stream_response"),
    path('ver_fontes/<int:id>', views.ver_fontes, name='ver_fontes'),

    # URLs avançadas
    path('chat_inteligente', views_advanced.chat_inteligente, name="chat_inteligente"),
    path('iniciar_conversa', views_advanced.iniciar_conversa, name="iniciar_conversa"),
    path('listar_conversas', views_advanced.listar_conversas, name="listar_conversas"),
    path('avaliar_resposta', views_advanced.avaliar_resposta, name="avaliar_resposta"),
    path('dashboard', views_advanced.dashboard_analytics, name="dashboard_analytics"),
    path('exportar_conversa/<int:conversa_id>', views_advanced.exportar_conversa, name="exportar_conversa"),
]