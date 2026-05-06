from django.db import models
from django.conf import settings

class Rapport(models.Model):
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    contenu = models.TextField()
    # ✅ NOUVEAU si absent :
    statut = models.CharField(max_length=20, default='attente', choices=[
        ('attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rapport {self.auteur} - {self.date}"
