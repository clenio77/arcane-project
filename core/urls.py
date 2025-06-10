from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

def landing_page(request):
    """Landing page comercial"""
    return render(request, 'landing_page.html')

urlpatterns = [
    path('', landing_page, name='home'),
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('oraculo/', include('oraculo.urls')),
    path('billing/', include('billing.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
