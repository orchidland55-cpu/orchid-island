from django.urls import path
from . import views

urlpatterns = [
    path('', views.lister_rapports, name='lister_rapports'),
    path('creer/', views.creer_rapport, name='creer_rapport'),
    path('<int:pk>/supprimer/', views.supprimer_rapport, name='supprimer_rapport'),
    path('<int:pk>/', views.detail_rapport, name='detail_rapport'),
    path('<int:pk>/valider/', views.valider_rapport, name='valider_rapport'),
    path('<int:pk>/fichier/', views.proxy_fichier, name='proxy_fichier'),   # ✅ NOUVEAU proxy
]
