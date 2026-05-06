from django.urls import path
from . import views

urlpatterns = [
    path('', views.lister_taches, name='lister_taches'),
    path('creer/', views.creer_tache, name='creer_tache'),
    path('<int:pk>/modifier/', views.modifier_tache, name='modifier_tache'),
    path('<int:pk>/supprimer/', views.supprimer_tache, name='supprimer_tache'),
]
