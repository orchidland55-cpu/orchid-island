from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser
import cloudinary.uploader
import cloudinary
import requests
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import AccessToken


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_stagiaires(request):
    stagiaires = CustomUser.objects.filter(role='stagiaire').values(
        'id', 'email', 'first_name', 'last_name', 'is_active',
        'absences_non_justifiees', 'ecole', 'formation', 'departement',
        'date_debut_stage', 'date_fin_stage',
        'cv_url',
        'cv_name',
        'cv_public_id',
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

    # ✅ Supprimer l'ancien CV sur Cloudinary si existant
    if user.cv_public_id:
        try:
            cloudinary.uploader.destroy(user.cv_public_id, resource_type='raw')
            print(f'[CV UPLOAD] Ancien CV supprimé de Cloudinary: {user.cv_public_id}')
        except Exception as e:
            print(f'[CV UPLOAD] Erreur suppression ancien CV Cloudinary: {e}')

    # ✅ Upload vers Cloudinary (resource_type='raw' pour PDF/DOCX)
    try:
        upload_result = cloudinary.uploader.upload(
            fichier,
            resource_type='raw',
            folder='orchid_cv',
            public_id=f'cv_{user.id}_{fichier.name}',
            overwrite=True,
            use_filename=True,
        )

        cv_url = upload_result.get('secure_url')
        cv_public_id = upload_result.get('public_id')

        print(f'[CV UPLOAD] Cloudinary OK: {cv_url}')

        user.cv_url = cv_url
        user.cv_name = fichier.name
        user.cv_public_id = cv_public_id
        user.save()

        print(f'[CV UPLOAD] User mis à jour: cv_url={user.cv_url}, cv_name={user.cv_name}')

        return Response({
            'success': True,
            'cv_url': user.cv_url,
            'cv_name': user.cv_name,
        })

    except Exception as e:
        print(f'[CV UPLOAD] Erreur Cloudinary: {e}')
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Erreur upload Cloudinary: {str(e)}'
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

    # ✅ Supprimer de Cloudinary
    if user.cv_public_id:
        try:
            cloudinary.uploader.destroy(user.cv_public_id, resource_type='raw')
            print(f'[CV DELETE] Supprimé de Cloudinary: {user.cv_public_id}')
        except Exception as e:
            print(f'[CV DELETE] Erreur Cloudinary: {e}')

    user.cv_url = None
    user.cv_name = None
    user.cv_public_id = None
    user.save()

    return Response({'success': True})


@api_view(['GET'])
def proxy_cv(request, user_id):
    """
    Proxy pour servir les CVs depuis Cloudinary avec authentification JWT.
    Accepte le token via query param pour les iframes/liens directs.
    """
    # ✅ Authentification via token dans query param
    token_str = request.GET.get('token')
    if token_str:
        try:
            token = AccessToken(token_str)
            # Token valide, on continue
        except Exception:
            return HttpResponse('Token invalide', status=401)
    elif not request.user.is_authenticated:
        return HttpResponse('Non authentifié', status=401)

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return HttpResponse('Utilisateur non trouvé', status=404)

    print(f'[PROXY CV] User: {user.email}, cv_url: {user.cv_url}')

    if not user.cv_url:
        return HttpResponse('Pas de CV', status=404)

    # ✅ Rediriger directement vers l'URL Cloudinary (secure_url)
    # Cloudinary gère l'hébergement — pas besoin de proxy les bytes
    try:
        cv_response = requests.get(user.cv_url, timeout=15)
        cv_response.raise_for_status()

        # Détecter le content-type
        nom = user.cv_name or 'cv.pdf'
        if nom.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif nom.lower().endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            content_type = 'application/octet-stream'

        response = HttpResponse(cv_response.content, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{nom}"'
        response['Access-Control-Allow-Origin'] = '*'
        response['X-Frame-Options'] = 'ALLOWALL'
        return response

    except Exception as e:
        print(f'[PROXY CV] Erreur fetch Cloudinary: {e}')
        return HttpResponse(f'Erreur accès fichier: {e}', status=500)
