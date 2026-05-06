from django.db import models
from django.conf import settings

class Projet(models.Model):
    STATUT_CHOICES = [('en_cours', 'En cours'), ('termine', 'Terminé'), ('en_retard', 'En retard')]
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    progression = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre
