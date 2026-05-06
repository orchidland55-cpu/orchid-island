from django.urls import path
from . import views

urlpatterns = [
    path('', views.lister_stagiaires, name='lister_stagiaires_api'),
]
