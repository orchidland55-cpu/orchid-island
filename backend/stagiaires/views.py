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

    # ✅ Upload vers Cloudinary en raw (pas image) + accès public
    upload_result = cloudinary.uploader.upload(
        fichier,
        resource_type='raw',
        folder='cv/',
        use_filename=True,
        unique_filename=True,
        access_control=[{"access_type": "anonymous"}],  # ← public
    )

    # ✅ Stocker l'URL Cloudinary dans le modèle
    user.cv_url = upload_result.get('secure_url')
    user.cv_name = fichier.name
    user.cv_public_id = upload_result.get('public_id')
    user.save()

    return Response({
        'success': True,
        'cv_url': user.cv_url,
        'cv_name': user.cv_name,
    })


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

    if not user.cv_public_id and not user.cv_url:
        return HttpResponse('Pas de CV', status=404)

    # Si on a un public_id Cloudinary, générer URL signée
    if user.cv_public_id:
        import time
        from cloudinary.utils import cloudinary_url
        signed_url, _ = cloudinary_url(
            user.cv_public_id,
            resource_type='raw',
            sign_url=True,
            expires_at=int(time.time()) + 3600,
        )
        fetch_url = signed_url
    else:
        fetch_url = user.cv_url

    try:
        resp = requests.get(fetch_url, timeout=30, stream=True)
        resp.raise_for_status()
    except Exception as e:
        return HttpResponse(f'Erreur: {e}', status=502)

    nom = user.cv_name or 'cv.pdf'
    content_type = 'application/pdf' if nom.lower().endswith('.pdf') else 'application/octet-stream'

    response = StreamingHttpResponse(
        resp.iter_content(chunk_size=8192),
        content_type=content_type,
    )
    response['Content-Disposition'] = f'inline; filename="{nom}"'
    response['Access-Control-Allow-Origin'] = '*'
    response['X-Frame-Options'] = 'ALLOWALL'
    return response
