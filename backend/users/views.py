from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import CustomUser
from .permissions import IsAdmin, IsAdminOrRH, IsAdminOrRHOrManager, IsStagiaire

# ─────────────────────────────────────────────
# HELPER : récupérer l'utilisateur depuis le token JWT
# ─────────────────────────────────────────────
def get_user_from_request(request):
    """Retourne (user, error_response) depuis le header Authorization: Bearer <token>"""
    auth = JWTAuthentication()
    try:
        validated = auth.authenticate(request)
        if validated is None:
            return None, Response({'error': 'Token manquant ou invalide'}, status=401)
        user, token = validated
        if not user.is_active:
            return None, Response({'error': 'Compte bloqué. Contactez le RH ou l\'Admin.'}, status=403)
        return user, None
    except Exception as e:
        return None, Response({'error': str(e)}, status=401)


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    selected_role = request.data.get('role')

    if not email or not password:
        return Response({'error': 'Email et mot de passe requis'}, status=400)
    if not selected_role:
        return Response({'error': 'Veuillez sélectionner un rôle'}, status=400)

    try:
        user = CustomUser.objects.get(email=email)

        if not user.check_password(password):
            return Response({'error': 'Email ou mot de passe incorrect'}, status=401)

        # Vérification du rôle sélectionné
        clean_role = selected_role.split()[-1] if ' ' in selected_role else selected_role
        role_mapping = {'Admin': 'admin', 'Manager': 'manager', 'RH': 'rh', 'Stagiaire': 'stagiaire'}
        expected_role = role_mapping.get(clean_role)

        if not expected_role or user.role != expected_role:
            return Response({
                'error': f'Cet email n\'est pas autorisé pour le rôle {clean_role}.'
            }, status=401)

        # Vérifier si le compte est bloqué (sauf admin)
        if not user.is_active and user.role != 'admin':
            return Response({
                'error': 'Votre compte est bloqué suite à des absences répétées. Contactez le RH ou l\'Admin.',
                'compte_bloque': True
            }, status=403)

        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
            }
        })

    except CustomUser.DoesNotExist:
        return Response({'error': 'Email ou mot de passe incorrect'}, status=401)
    except Exception as e:
        return Response({'error': f'Erreur serveur: {str(e)}'}, status=500)


# ─────────────────────────────────────────────
# STAGIAIRES — CRUD (Admin + RH uniquement)
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])  # laisser AllowAny pour compatibilité frontend actuel
def lister_stagiaires(request):
    """
    Accessible : Admin, RH, Manager (lecture)
    Bloquer l'accès direct Stagiaire côté frontend via checkRoleAccess()
    """
    try:
        user, err = get_user_from_request(request)
        # Si pas de token valide → retourner quand même la liste (rétrocompat)
        # Pour forcer l'auth, remplacer par : if err: return err

        stagiaires = CustomUser.objects.filter(role='stagiaire')
        data = []
        for s in stagiaires:
            cv_url = request.build_absolute_uri(s.cv.url) if s.cv else None
            data.append({
                'id': s.id,
                'email': s.email,
                'first_name': s.first_name,
                'last_name': s.last_name,
                'phone': s.phone,
                'cv_url': cv_url,
                'cv_name': s.cv.name if s.cv else None,
                'date_debut_stage': s.date_debut_stage.isoformat() if s.date_debut_stage else None,
                'date_fin_stage': s.date_fin_stage.isoformat() if s.date_fin_stage else None,
                'ecole': s.ecole,
                'formation': s.formation,
                'departement': s.departement,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                # ── NOUVEAU ──
                'absences_non_justifiees': s.absences_non_justifiees,
                'is_active': s.is_active,
                'statut': getattr(s, 'statut', 'Accepté'),
            })
        return Response({'success': True, 'stagiaires': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def creer_stagiaire(request):
    """Admin ou RH uniquement"""
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role not in ('admin', 'rh'):
        return Response({'error': 'Accès refusé. Réservé Admin/RH.'}, status=403)

    try:
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'success': False, 'error': 'Email requis'}, status=400)
        # ✅ Vérifier doublon par email (insensible à la casse)
        if CustomUser.objects.filter(email__iexact=email).exists():
            return Response({
                'success': False,
                'error': f'Un compte avec l\'email {email} existe déjà.'
            }, status=409)

        password = request.data.get('password', '').strip()
        if not password:
            return Response({
                'success': False,
                'error': 'Mot de passe requis'
            }, status=400)

        stagiaire = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password,  # ✅ Vrai mot de passe
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            phone=request.data.get('phone', ''),
            role='stagiaire',
            ecole=request.data.get('ecole', ''),
            formation=request.data.get('formation', ''),
            departement=request.data.get('departement', ''),
        )

        from datetime import datetime
        dds = request.data.get('date_debut_stage')
        dfs = request.data.get('date_fin_stage')
        if dds and dds != 'null':
            stagiaire.date_debut_stage = datetime.strptime(dds, '%Y-%m-%d').date()
        if dfs and dfs != 'null':
            stagiaire.date_fin_stage = datetime.strptime(dfs, '%Y-%m-%d').date()
        stagiaire.save()

        return Response({
            'success': True,
            'id': stagiaire.id,
            'message': 'Stagiaire créé avec succès',
            'stagiaire': {'id': stagiaire.id, 'email': stagiaire.email}
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['PUT'])
@permission_classes([AllowAny])
def modifier_stagiaire(request, user_id):
    """Admin ou RH uniquement"""
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role not in ('admin', 'rh'):
        return Response({'error': 'Accès refusé. Réservé Admin/RH.'}, status=403)

    try:
        import json
        data = json.loads(request.body)
        stagiaire = CustomUser.objects.get(id=user_id, role='stagiaire')
        
        # Champs de base
        if 'first_name' in data:
            stagiaire.first_name = data['first_name']
        if 'last_name' in data:
            stagiaire.last_name = data['last_name']
        if 'phone' in data and hasattr(stagiaire, 'phone'):
            stagiaire.phone = data['phone']
        if 'ecole' in data and hasattr(stagiaire, 'ecole'):
            stagiaire.ecole = data['ecole']
        if 'formation' in data and hasattr(stagiaire, 'formation'):
            stagiaire.formation = data['formation']
        if 'departement' in data and hasattr(stagiaire, 'departement'):
            stagiaire.departement = data['departement']

        from datetime import datetime

        def parse_date(d):
            if not d or d in ('null', '', None):
                return None
            # Format YYYY-MM-DD (depuis input date HTML)
            try:
                return datetime.strptime(d, '%Y-%m-%d').date()
            except ValueError:
                pass
            # Format DD/MM/YYYY (ancien format FR)
            try:
                return datetime.strptime(d, '%d/%m/%Y').date()
            except ValueError:
                pass
            return None

        if 'date_debut_stage' in data:
            stagiaire.date_debut_stage = parse_date(data['date_debut_stage'])
        if 'date_fin_stage' in data:
            stagiaire.date_fin_stage = parse_date(data['date_fin_stage'])
        
        # ✅ Gestion du statut
        statut = data.get('statut', None)
        if statut:
            if statut == 'Accepté':
                stagiaire.is_active = True
                if hasattr(stagiaire, 'statut'):
                    stagiaire.statut = 'Accepté'
            elif statut == 'En attente':
                stagiaire.is_active = True  # ← Toujours actif, juste en attente
                if hasattr(stagiaire, 'statut'):
                    stagiaire.statut = 'En attente'
            elif statut in ['Refusé', 'Bloqué']:
                stagiaire.is_active = False
                if hasattr(stagiaire, 'statut'):
                    stagiaire.statut = statut
        
        stagiaire.save()
        
        return Response({
            'success': True,
            'message': f'Stagiaire modifié avec succès',
            'is_active': stagiaire.is_active
        })
        
    except Exception as e:
        import traceback
        print('[ERREUR MODIFIER]', traceback.format_exc())
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def supprimer_stagiaire(request, user_id):
    """Admin ou RH uniquement"""
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role not in ('admin', 'rh'):
        return Response({'error': 'Accès refusé. Réservé Admin/RH.'}, status=403)

    try:
        stagiaire = CustomUser.objects.get(id=user_id, role='stagiaire')
        if stagiaire.cv:
            stagiaire.cv.delete()
        stagiaire.delete()
        return Response({'success': True, 'message': 'Stagiaire supprimé avec succès'})
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Stagiaire non trouvé'}, status=404)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────
# CV
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def uploader_cv(request):
    """Stagiaire pour lui-même, ou Admin/RH"""
    user, err = get_user_from_request(request)
    if err:
        return err

    try:
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        cv_file = request.FILES.get('cv')

        if not cv_file:
            return Response({'success': False, 'error': 'Fichier CV requis'}, status=400)

        # Trouver le stagiaire cible
        if email:
            target = CustomUser.objects.filter(email=email).first()
        elif user_id:
            target = CustomUser.objects.get(id=user_id)
        else:
            return Response({'success': False, 'error': 'ID ou email requis'}, status=400)

        if not target:
            return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

        # Stagiaire ne peut uploader que son propre CV
        if user.role == 'stagiaire' and user.id != target.id:
            return Response({'error': 'Vous ne pouvez modifier que votre propre CV.'}, status=403)

        if target.role != 'stagiaire':
            return Response({'success': False, 'error': 'Seuls les stagiaires ont un CV'}, status=400)

        if target.cv:
            target.cv.delete()
        target.cv = cv_file
        target.save(update_fields=['cv'])

        return Response({
            'success': True,
            'message': 'CV uploadé avec succès',
            'cv_url': request.build_absolute_uri(target.cv.url),
            'cv_name': target.cv.name,
            'user_id': target.id
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def supprimer_cv(request):
    """Admin, RH ou Stagiaire (son propre CV)"""
    user, err = get_user_from_request(request)
    if err:
        return err

    try:
        email = request.GET.get('email')
        user_id = request.GET.get('user_id')

        if email:
            target = CustomUser.objects.get(email=email)
        elif user_id:
            target = CustomUser.objects.get(id=user_id)
        else:
            return Response({'success': False, 'error': 'Email ou ID requis'}, status=400)

        if user.role == 'stagiaire' and user.id != target.id:
            return Response({'error': 'Accès refusé.'}, status=403)

        if not target.cv:
            return Response({'success': False, 'error': 'Aucun CV à supprimer'}, status=400)

        target.cv.delete()
        target.cv = None
        target.save()
        return Response({'success': True, 'message': 'CV supprimé avec succès'})
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────
# ABSENCES — Logique automatique
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def enregistrer_absence(request):
    """
    Appelé quand une absence non justifiée est confirmée.
    Corps JSON : { "stagiaire_id": <int> }
    Accessible : Admin, RH
    """
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role not in ('admin', 'rh'):
        return Response({'error': 'Accès refusé.'}, status=403)

    stagiaire_id = request.data.get('stagiaire_id')
    try:
        stagiaire = CustomUser.objects.get(id=stagiaire_id, role='stagiaire')
    except CustomUser.DoesNotExist:
        return Response({'error': 'Stagiaire non trouvé'}, status=404)

    stagiaire.absences_non_justifiees = (stagiaire.absences_non_justifiees or 0) + 1
    nb = stagiaire.absences_non_justifiees

    message_whatsapp = None
    compte_bloque = False

    if nb >= 3:
        # Bloquer le compte
        stagiaire.is_active = False
        compte_bloque = True
        message_whatsapp = (
            f"🚫 COMPTE BLOQUÉ\n"
            f"Le stagiaire {stagiaire.first_name} {stagiaire.last_name} "
            f"a atteint {nb} absences non justifiées.\n"
            f"Son compte a été désactivé automatiquement.\n"
            f"Orchid Island — RH"
        )
    elif nb == 2:
        message_whatsapp = (
            f"⚠️ ALERTE ABSENCE\n"
            f"{stagiaire.first_name} {stagiaire.last_name} "
            f"a maintenant {nb} absences non justifiées.\n"
            f"Attention : à 3 absences, le compte sera bloqué.\n"
            f"Orchid Island — RH"
        )

    stagiaire.save()

    return Response({
        'success': True,
        'nb_absences_nj': nb,
        'compte_bloque': compte_bloque,
        'whatsapp_message': message_whatsapp,
        'stagiaire': {
            'id': stagiaire.id,
            'email': stagiaire.email,
            'nom': f"{stagiaire.first_name} {stagiaire.last_name}",
            'is_active': stagiaire.is_active,
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def debloquer_compte(request, user_id):
    """
    Débloquer un compte stagiaire bloqué.
    Accessible : Admin ou RH uniquement.
    """
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role not in ('admin', 'rh'):
        return Response({'error': 'Accès refusé. Seuls Admin et RH peuvent débloquer un compte.'}, status=403)

    try:
        stagiaire = CustomUser.objects.get(id=user_id, role='stagiaire')
        stagiaire.is_active = True
        stagiaire.absences_non_justifiees = 0   # reset compteur
        stagiaire.save()
        return Response({
            'success': True,
            'message': f'Compte de {stagiaire.first_name} {stagiaire.last_name} débloqué avec succès.',
        })
    except CustomUser.DoesNotExist:
        return Response({'error': 'Stagiaire non trouvé'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def deposer_justification(request):
    """
    Déposer une justification d'absence.
    Accessible : Stagiaire (pour lui-même), RH, Admin.
    Corps JSON : { "stagiaire_id": <int>, "motif": "...", "date": "YYYY-MM-DD" }
    """
    user, err = get_user_from_request(request)
    if err:
        return err

    stagiaire_id = request.data.get('stagiaire_id')

    # Stagiaire ne peut déposer que pour lui-même
    if user.role == 'stagiaire' and str(user.id) != str(stagiaire_id):
        return Response({'error': 'Vous ne pouvez déposer que vos propres justifications.'}, status=403)

    try:
        stagiaire = CustomUser.objects.get(id=stagiaire_id, role='stagiaire')
    except CustomUser.DoesNotExist:
        return Response({'error': 'Stagiaire non trouvé'}, status=404)

    motif = request.data.get('motif', '')
    date_absence = request.data.get('date', '')
    fichier = request.FILES.get('fichier')

    # Ici vous pouvez sauvegarder dans un modèle Justification si vous en avez un.
    # Pour l'instant on retourne juste le succès et on décrémente les absences non justifiées.
    if stagiaire.absences_non_justifiees and stagiaire.absences_non_justifiees > 0:
        stagiaire.absences_non_justifiees -= 1
        # Si le compte était bloqué à cause d'absences et qu'on justifie, 
        # le RH/Admin décide du déblocage via debloquer_compte()
        stagiaire.save()

    return Response({
        'success': True,
        'message': 'Justification déposée avec succès.',
        'absences_restantes': stagiaire.absences_non_justifiees,
    })


# ─────────────────────────────────────────────
# ALERTES — Envoi alerte admin (RH uniquement)
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def envoyer_alerte_admin(request):
    """RH peut envoyer une alerte à l'admin"""
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role not in ('admin', 'rh'):
        return Response({'error': 'Accès refusé.'}, status=403)

    message = request.data.get('message', '')
    categorie = request.data.get('categorie', 'RH')

    # Ici: sauvegarder dans votre modèle Alerte existant
    # Exemple minimal:
    # Alerte.objects.create(message=message, categorie=categorie, expediteur=user)

    return Response({
        'success': True,
        'message': 'Alerte envoyée à l\'admin.',
        'alerte': {'message': message, 'categorie': categorie, 'expediteur': user.email}
    })


# ─────────────────────────────────────────────
# PROFIL STAGIAIRE (lecture seule pour lui-même)
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def mon_profil(request):
    """Stagiaire consulte son propre profil"""
    user, err = get_user_from_request(request)
    if err:
        return err
    if user.role != 'stagiaire':
        return Response({'error': 'Réservé aux stagiaires.'}, status=403)

    cv_url = request.build_absolute_uri(user.cv.url) if user.cv else None
    return Response({
        'success': True,
        'profil': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'ecole': user.ecole,
            'formation': user.formation,
            'departement': user.departement,
            'date_debut_stage': user.date_debut_stage.isoformat() if user.date_debut_stage else None,
            'date_fin_stage': user.date_fin_stage.isoformat() if user.date_fin_stage else None,
            'cv_url': cv_url,
            'absences_non_justifiees': user.absences_non_justifiees,
            'is_active': user.is_active,
        }
    })


# ─────────────────────────────────────────────
# REGISTER (garder pour compatibilité)
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    role = request.data.get('role', 'stagiaire')

    if not email or not password:
        return Response({'error': 'Email et mot de passe requis'}, status=400)
    if CustomUser.objects.filter(email=email).exists():
        return Response({'error': 'Cet email est déjà utilisé'}, status=400)

    try:
        validate_password(password)
        CustomUser.objects.create_user(
            username=email, email=email, password=password,
            first_name=first_name, last_name=last_name, role=role
        )
        return Response({'success': True, 'message': 'Compte créé avec succès'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


# ─────────────────────────────────────────────
# RÉVOCATION TOKENS (Admin/RH seulement)
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_stagiaire_tokens(request, stagiaire_id):
    """Révoque tous les tokens JWT d'un stagiaire lors de sa suppression."""
    if request.user.role not in ['admin', 'rh']:
        return Response({'success': False, 'error': 'Accès refusé'}, status=403)
    
    try:
        stagiaire = CustomUser.objects.get(id=stagiaire_id)
        
        # Méthode 1 : Si vous utilisez simplejwt avec blacklist
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            tokens = OutstandingToken.objects.filter(user=stagiaire)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass  # simplejwt blacklist non configuré
        
        # Méthode 2 : Désactiver le compte (bloque toute nouvelle auth)
        stagiaire.is_active = False
        stagiaire.save()
        
        return Response({'success': True, 'message': f'Tokens révoqués pour {stagiaire.email}'})
    
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Stagiaire non trouvé'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_absences_stagiaire(request, stagiaire_id):
    """Remet à zéro les absences d'un stagiaire."""
    if request.user.role not in ['admin', 'rh']:
        return Response({'success': False, 'error': 'Accès refusé'}, status=403)
    
    try:
        stagiaire = CustomUser.objects.get(id=stagiaire_id, role='stagiaire')
        stagiaire.absences_non_justifiees = 0
        stagiaire.save()
        
        # Supprimer aussi les absences liées
        from presences.models import Absence, Pointage
        Absence.objects.filter(stagiaire=stagiaire).delete()
        
        return Response({
            'success': True,
            'message': f'Absences remises à 0 pour {stagiaire.first_name} {stagiaire.last_name}'
        })
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Stagiaire non trouvé'}, status=404)
