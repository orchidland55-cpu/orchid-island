from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

def serve_frontend(request):
    return JsonResponse({'status': 'Orchid Island API', 'version': '1.0'})

urlpatterns = [
    path("", serve_frontend, name='root'),
    path("admin/", admin.site.urls),
    path("api/auth/", include('users.urls')),
    path("api/presences/", include('presences.urls')),
    path("api/projets/", include('projets.urls')),
    path("api/taches/", include('taches.urls')),
    path("api/stagiaires/", include('stagiaires.urls')),
    path("api/rapports/", include('rapports.urls')),
]

# ============================================================
# Servir les fichiers média (CV, justifications)
# ============================================================
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)