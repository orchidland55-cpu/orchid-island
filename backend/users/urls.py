from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),

    # ── Stagiaires (Admin + RH) ──
    path('stagiaires/', views.lister_stagiaires, name='lister_stagiaires'),
    path('stagiaire/creer/', views.creer_stagiaire, name='creer_stagiaire'),
    path('stagiaire/<int:user_id>/', views.supprimer_stagiaire, name='supprimer_stagiaire'),
    path('stagiaire/<int:user_id>/modifier/', views.modifier_stagiaire, name='modifier_stagiaire'),

    # ── CV ──
    path('cv/upload/', views.uploader_cv, name='uploader_cv'),
    path('cv/delete/', views.supprimer_cv, name='supprimer_cv'),

    # ── Absences (NOUVEAU) ──
    path('absence/enregistrer/', views.enregistrer_absence, name='enregistrer_absence'),
    path('absence/justifier/', views.deposer_justification, name='deposer_justification'),
    path('compte/debloquer/<int:user_id>/', views.debloquer_compte, name='debloquer_compte'),

    # ── Alertes (NOUVEAU) ──
    path('alerte/envoyer/', views.envoyer_alerte_admin, name='envoyer_alerte_admin'),

    # ── Profil stagiaire (NOUVEAU) ──
    path('profil/', views.mon_profil, name='mon_profil'),
]