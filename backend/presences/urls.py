from django.urls import path
from . import views

urlpatterns = [
    path('pointage/', views.creer_pointage, name='creer_pointage'),
    path('pointages/', views.lister_pointages, name='lister_pointages'),
    path('pointage/<int:pointage_id>/', views.supprimer_pointage, name='supprimer_pointage'),
    path('historique/', views.historique_stagiaire, name='historique'),
    path('absence/creer/', views.creer_absence, name='creer_absence'),
    path('absence/justification/', views.upload_justification, name='upload_justification'),
    path('absence/<int:pk>/', views.supprimer_absence, name='supprimer_absence'),
]
