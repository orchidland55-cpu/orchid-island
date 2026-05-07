from django.urls import path
from . import views

urlpatterns = [
    path('', views.lister_stagiaires, name='lister_stagiaires_api'),
    path('cv/upload/', views.upload_cv, name='upload_cv'),
    path('cv/delete/', views.delete_cv, name='delete_cv'),
    path('cv/proxy/<int:user_id>/', views.proxy_cv, name='proxy_cv'),   # ✅ NOUVEAU proxy
]
