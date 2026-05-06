from django.db import models
from django.conf import settings

class Rapport(models.Model):
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    contenu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rapport {self.auteur} - {self.date}"
