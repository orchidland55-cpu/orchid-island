from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Projet

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_projets(request):
    projets = Projet.objects.all().values('id','titre','description','statut','progression','date_debut','date_fin')
    return Response(list(projets))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_projet(request):
    p = Projet.objects.create(
        titre=request.data.get('titre',''),
        description=request.data.get('description',''),
        statut=request.data.get('statut','en_cours'),
        progression=request.data.get('progression',0),
        date_debut=request.data.get('date_debut') or None,
        date_fin=request.data.get('date_fin') or None,
    )
    return Response({'id': p.id, 'titre': p.titre, 'statut': p.statut})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_projet(request, pk):
    try:
        p = Projet.objects.get(pk=pk)
        return Response({'id':p.id,'titre':p.titre,'description':p.description,'statut':p.statut,'progression':p.progression})
    except Projet.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def modifier_projet(request, pk):
    try:
        p = Projet.objects.get(pk=pk)
        for field in ['titre','description','statut','progression','date_debut','date_fin']:
            if field in request.data:
                setattr(p, field, request.data[field])
        p.save()
        return Response({'success': True})
    except Projet.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_projet(request, pk):
    try:
        Projet.objects.get(pk=pk).delete()
        return Response({'success': True})
    except Projet.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
