from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Projet
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_projets(request):
    projets = Projet.objects.all()
    data = []
    for p in projets:
        data.append({
            'id': p.id,
            'titre': p.titre,
            'description': p.description,
            'statut': p.statut,
            'progression': p.progression,
            'date_debut': str(p.date_debut) if p.date_debut else None,
            'date_fin': str(p.date_fin) if p.date_fin else None,
            'responsable_nom': p.responsable_nom or '',
            'tasks_json': p.tasks_json or [],
        })
    return Response(data)

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
        responsable_nom=request.data.get('responsable_nom',''),
        tasks_json=request.data.get('tasks_json', []),
    )
    return Response({'id': p.id, 'titre': p.titre, 'statut': p.statut})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_projet(request, pk):
    try:
        p = Projet.objects.get(pk=pk)
        return Response({
            'id': p.id, 'titre': p.titre, 'description': p.description,
            'statut': p.statut, 'progression': p.progression,
            'responsable_nom': p.responsable_nom,
            'tasks_json': p.tasks_json or [],
        })
    except Projet.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def modifier_projet(request, pk):
    try:
        p = Projet.objects.get(pk=pk)
        for field in ['titre','description','statut','progression','date_debut','date_fin','responsable_nom']:
            if field in request.data:
                setattr(p, field, request.data[field] or None if field in ['date_debut','date_fin'] else request.data[field])
        if 'tasks_json' in request.data:
            p.tasks_json = request.data['tasks_json']
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
