from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser
import cloudinary.uploader
import requests
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework_simplejwt.tokens import AccessToken

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_stagiaires(request):
    stagiaires = CustomUser.objects.filter(role='stagiaire').values(
        'id', 'email', 'first_name', 'last_name', 'is_active',
        'absences_non_justifiees', 'ecole', 'formation', 'departement',
        'date_debut_stage', 'date_fin_stage',
        'cv_url',      # ✅ URL Cloudinary directe
        'cv_name',     # ✅ Nom du fichier original
        'mot_de_passe_clair',
        'statut',
    )
    return Response({'success': True, 'stagiaires': list(stagiaires)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_cv(request):
    email = request.data.get('email')
    fichier = request.FILES.get('cv')

    if not email or not fichier:
        return Response({'success': False, 'error': 'Email et fichier requis'}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

    # ✅ Supprimer l'ancien CV local si existant
    if user.cv_public_id:
        try:
            from django.core.files.storage import default_storage
            if default_storage.exists(user.cv_public_id):
                default_storage.delete(user.cv_public_id)
        except Exception as e:
            print(f'[CV UPLOAD] Erreur suppression ancien CV: {e}')

    # ✅ Stocker localement au lieu de Cloudinary
    from django.core.files.storage import default_storage
    from django.conf import settings
    import os
    import uuid

    try:
        # ✅ Créer le dossier media s'il n'existe pas
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            os.makedirs(media_root, exist_ok=True)
            print(f'[CV UPLOAD] Créé dossier media: {media_root}')

        cv_dir = os.path.join(media_root, 'cv')
        if not os.path.exists(cv_dir):
            os.makedirs(cv_dir, exist_ok=True)
            print(f'[CV UPLOAD] Créé dossier cv: {cv_dir}')

        # Générer un nom de fichier unique
        ext = os.path.splitext(fichier.name)[1]
        unique_filename = f"cv_{uuid.uuid4().hex}{ext}"
        path = default_storage.save(f'cv/{unique_filename}', fichier)
        cv_url = f"/media/{path}"

        print(f'[CV UPLOAD] Fichier sauvegardé: {path}')
        print(f'[CV UPLOAD] URL: {cv_url}')

        user.cv_url = cv_url
        user.cv_name = fichier.name
        user.cv_public_id = path  # Stocker le chemin local comme public_id
        user.save()

        print(f'[CV UPLOAD] User mis à jour: cv_url={user.cv_url}')

        return Response({
            'success': True,
            'cv_url': user.cv_url,
            'cv_name': user.cv_name,
        })
    except Exception as e:
        print(f'[CV UPLOAD] Erreur lors de l\'upload: {e}')
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Erreur lors de l\'upload: {str(e)}'
        }, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cv(request):
    email = request.GET.get('email')
    if not email:
        return Response({'success': False, 'error': 'Email requis'}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

    # ✅ Supprimer de Cloudinary si public_id disponible
    if user.cv_public_id:
        try:
            cloudinary.uploader.destroy(user.cv_public_id, resource_type='raw')
        except Exception as e:
            print(f'[CV DELETE] Erreur Cloudinary: {e}')

    user.cv_url = None
    user.cv_name = None
    user.cv_public_id = None
    user.save()

    return Response({'success': True})


@api_view(['GET'])
def proxy_cv(request, user_id):
    # ✅ Accepter token depuis query param (pour iframe)
    token_str = request.GET.get('token')
    if token_str:
        try:
            token = AccessToken(token_str)
            user = CustomUser.objects.get(id=token['user_id'])
        except Exception:
            return HttpResponse('Token invalide', status=401)
    elif not request.user.is_authenticated:
        return HttpResponse('Non authentifié', status=401)

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return HttpResponse('Not found', status=404)

    print(f'[PROXY CV] User trouvé: {user.email}, cv_public_id: {user.cv_public_id}, cv_url: {user.cv_url}')

    if not user.cv_public_id:
        return HttpResponse('Pas de CV', status=404)

    # ✅ Servir le fichier local
    from django.core.files.storage import default_storage
    from django.conf import settings

    try:
        # Le cv_public_id contient maintenant le chemin local
        file_path = user.cv_public_id
        print(f'[PROXY CV] Chemin fichier: {file_path}')
        print(f'[PROXY CV] MEDIA_ROOT: {settings.MEDIA_ROOT}')
        print(f'[PROXY CV] Fichier existe: {default_storage.exists(file_path)}')

        if not default_storage.exists(file_path):
            print(f'[PROXY CV] Fichier non trouvé: {file_path}')
            return HttpResponse('Fichier non trouvé', status=404)

        file = default_storage.open(file_path, 'rb')
        file_content = file.read()
        print(f'[PROXY CV] Fichier lu, taille: {len(file_content)} bytes')

        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="{user.cv_name or "cv.pdf"}"'
        response['Access-Control-Allow-Origin'] = '*'
        response['X-Frame-Options'] = 'ALLOWALL'

        # Déterminer le Content-Type basé sur l'extension
        nom = user.cv_name or 'cv.pdf'
        if nom.lower().endswith('.pdf'):
            response['Content-Type'] = 'application/pdf'
        elif nom.lower().endswith('.docx'):
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        file.close()
        print(f'[PROXY CV] Réponse envoyée')
        return response
    except Exception as e:
        print(f'[PROXY CV] Erreur: {e}')
        import traceback
        traceback.print_exc()
        return HttpResponse(f'Erreur lecture fichier: {e}', status=500)
