from django.urls import path
from . import views

urlpatterns = [
    path('', views.lister_rapports, name='lister_rapports'),
    path('creer/', views.creer_rapport, name='creer_rapport'),
    path('<int:pk>/supprimer/', views.supprimer_rapport, name='supprimer_rapport'),
]
