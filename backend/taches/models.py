from django.db import models
from projets.models import Projet
from django.conf import settings

class Tache(models.Model):
    STATUT_CHOICES = [('a_faire', 'À faire'), ('en_cours', 'En cours'), ('termine', 'Terminé')]
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='taches')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='a_faire')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre
