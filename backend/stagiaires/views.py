from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lister_stagiaires(request):
    stagiaires = CustomUser.objects.filter(role='stagiaire').values('id','email','first_name','last_name','is_active')
    return Response(list(stagiaires))
