from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('rh', 'RH'),
        ('manager', 'Manager'),
        ('stagiaire', 'Stagiaire'),
    ]
    
    STATUT_CHOICES = [
        ('Accepté', 'Accepté'),
        ('En attente', 'En attente'),
        ('Refusé', 'Refusé'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='stagiaire')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='Accepté')
    phone = models.CharField(max_length=20, blank=True, default='')
    cv = models.FileField(upload_to='cv/', blank=True, null=True, verbose_name='CV')
    date_debut_stage = models.DateField(blank=True, null=True, verbose_name='Date début stage')
    date_fin_stage = models.DateField(blank=True, null=True, verbose_name='Date fin stage')
    ecole = models.CharField(max_length=100, blank=True, default='', verbose_name='École')
    formation = models.CharField(max_length=100, blank=True, default='', verbose_name='Formation')
    departement = models.CharField(max_length=100, blank=True, default='', verbose_name='Département')
    created_at = models.DateTimeField(auto_now_add=True)
    absences_non_justifiees = models.IntegerField(default=0, verbose_name='Absences non justifiées')
    mot_de_passe_clair = models.CharField(max_length=100, blank=True, default='')
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    
    def __str__(self):
        return f"{self.email} ({self.role})"