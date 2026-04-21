from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.http import FileResponse
from django.conf import settings
from django.conf.urls.static import static
import os

def serve_frontend(request, page='pointage_qr.html'):
    """Sert les fichiers HTML du frontend"""
    frontend_dir = '/Users/mac/Desktop/orchid-island/frontend/pages'
    # Sécurité: s'assurer que le fichier demandé est dans le dossier pages
    safe_page = os.path.basename(page)
    file_path = os.path.join(frontend_dir, safe_page)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    return FileResponse(open(os.path.join(frontend_dir, 'pointage_qr.html'), 'rb'))

def serve_frontend_js(request, path):
    """Sert les fichiers JavaScript du frontend"""
    frontend_dir = '/Users/mac/Desktop/orchid-island/frontend'
    file_path = os.path.join(frontend_dir, path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/javascript')
    return FileResponse(open(os.path.join(frontend_dir, 'assets', path)), content_type='application/javascript')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include('users.urls')),
    path("api/presences/", include('presences.urls')),
    # Frontend JavaScript files - servir depuis assets/ et racine
    re_path(r'^assets/(?P<path>[\w\-\.]+\.js)$', serve_frontend_js),
    re_path(r'^(?P<path>[\w\-\.]+\.js)$', serve_frontend_js),
    # Frontend pages - URL spécifiques
    path("", serve_frontend, name='pointage'),
    path("pointage/", serve_frontend, name='pointage_qr'),
    path("scan/", lambda r: serve_frontend(r, 'scan_mobile.html'), name='scan'),
    # URL générique pour toutes les pages .html
    re_path(r'^(?P<page>[\w\-\.]+\.html)$', serve_frontend),
    # Redirections pour les pages sans extension
    path('taches/', lambda r: serve_frontend(r, 'taches.html')),
    path('stagiaires/', lambda r: serve_frontend(r, 'stagiaires.html')),
    path('projets/', lambda r: serve_frontend(r, 'projets.html')),
    path('dashboard/', lambda r: serve_frontend(r, 'dashboard.html')),
    path('rapports/', lambda r: serve_frontend(r, 'rapports.html')),
    path('alertes/', lambda r: serve_frontend(r, 'alertes.html')),
]

# ============================================================
# CRITIQUE : Sans ces lignes, les CV ne s'affichent PAS
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)