from django.db import models

class Pointage(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(max_length=200, default='')
    type_pointage = models.CharField(max_length=10, choices=[('entree', 'Entrée'), ('sortie', 'Sortie')])
    heure = models.CharField(max_length=10)
    wa_envoye = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'pointages'

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.type_pointage} ({self.heure})"


class Absence(models.Model):
    stagiaire = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='absences',
        null=True,
        blank=True
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date = models.DateField()
    justifiee = models.BooleanField(default=False)
    justification = models.FileField(upload_to='justifications/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('stagiaire', 'date')
        db_table = 'absences'

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.date} - Justifié: {self.justifiee}"
