from django.urls import path
from . import views

urlpatterns = [
    path('', views.lister_projets, name='lister_projets'),
    path('creer/', views.creer_projet, name='creer_projet'),
    path('<int:pk>/', views.detail_projet, name='detail_projet'),
    path('<int:pk>/modifier/', views.modifier_projet, name='modifier_projet'),
    path('<int:pk>/supprimer/', views.supprimer_projet, name='supprimer_projet'),
]
