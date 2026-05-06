from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from .models import Pointage, Absence
import logging

logger = logging.getLogger(__name__)


def envoyer_whatsapp_message(prenom, nom, type_pointage, heure):
    """Générer l'URL WhatsApp pour l'envoi manuel automatique"""
    try:
        import urllib.parse
        
        # Numéro de destination (avec le code pays, sans le +)
        phone_number = settings.WHATSAPP_DESTINATION_NUMBER
        
        # Créer le message
        type_label = "ARRIVÉE" if type_pointage == "entree" else "DÉPART"
        message_body = f"""*Pointage {type_label} - Orchid Island Real Estate*

*Stagiaire :* {prenom} {nom}

*Heure de {"l'arrivée" if type_pointage == "entree" else "départ"} :* {heure}
*Date :* {timezone.now().strftime('%d/%m/%Y')}

Pointage enregistré automatiquement via QR Code
Orchid Island - Système RH"""
        
        # URL encoder le message
        encoded_message = urllib.parse.quote(message_body)
        
        # Générer l'URL WhatsApp
        whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
        
        logger.info(f"URL WhatsApp générée pour {prenom} {nom}")
        print(f"[WHATSAPP] 📱 URL générée: {whatsapp_url}")
        return whatsapp_url
        
    except Exception as e:
        logger.error(f"Erreur génération URL WhatsApp: {e}")
        print(f"[WHATSAPP] ❌ Erreur: {e}")
        return None


def check_absences_and_alert(prenom, nom):
    """Vérifier les absences du stagiaire et envoyer une alerte après 3 absences"""
    try:
        from datetime import timedelta
        today = timezone.now().date()
        last_7_days = [today - timedelta(days=i) for i in range(7)]
        
        # Compter les jours où le stagiaire n'a aucun pointage (absence)
        absences = 0
        for day in last_7_days:
            has_pointage = Pointage.objects.filter(
                nom__iexact=nom,
                prenom__iexact=prenom,
                date=day
            ).exists()
            
            if not has_pointage:
                absences += 1
        
        print(f"[ABSENCES] {prenom} {nom}: {absences} absences sur les 7 derniers jours")
        
        # Si 3 absences ou plus, envoyer une alerte
        if absences >= 3:
            print(f"[ALERT] ⚠️ {prenom} {nom} a {absences} absences - Envoi d'alerte")
            logger.warning(f"Alerte absence: {prenom} {nom} a {absences} absences sur les 7 derniers jours")
            # Ici, vous pouvez ajouter une logique pour envoyer une notification réelle
            # Par exemple, créer une entrée dans une table d'alertes, envoyer un email, etc.
            
            # Créer une alerte dans localStorage ou dans une table d'alertes
            # Pour l'instant, on peut simplement logger l'alerte
            
    except Exception as e:
        print(f"[ABSENCES] Erreur lors de la vérification des absences: {e}")
        logger.error(f"Erreur vérification absences: {e}")

@api_view(['POST'])
@permission_classes([AllowAny])
def creer_pointage(request):
    """Créer un nouveau pointage - une seule entrée ET une seule sortie par jour par élève"""

    data = request.data
    logger.info(f"Pointage reçu: {data}")
    print(f"[POINTAGE] Données reçues: {data}")

    nom = data.get('nom', '').strip()
    prenom = data.get('prenom', '').strip()
    email = data.get('email', '').strip()
    type_pointage = data.get('type', 'entree')
    heure = data.get('heure', '')
    if not heure:
        heure = timezone.now().strftime('%H:%M')
    # S'assurer que c'est bien HH:MM (pas HH:MM:SS)
    if len(heure) > 5:
        heure = heure[:5]
    wa_envoye = data.get('wa', False)
    today = timezone.now().date()

    # Validation des champs obligatoires
    if not nom or not prenom:
        return Response({
            'success': False,
            'error': 'Le nom et le prénom sont obligatoires.'
        }, status=400)

    if type_pointage not in ['entree', 'sortie']:
        return Response({
            'success': False,
            'error': 'Le type de pointage doit être "entree" ou "sortie".'
        }, status=400)

    try:
        # Vérifier si le stagiaire existe dans la liste des stagiaires par nom, prénom (email optionnel)
        from users.models import CustomUser
        # Chercher par nom+prénom, affiner avec email si fourni
        qs = CustomUser.objects.filter(
            first_name__iexact=prenom,
            last_name__iexact=nom,
            role='stagiaire'
        ) | CustomUser.objects.filter(
            first_name__iexact=nom,
            last_name__iexact=prenom,
            role='stagiaire'
        )
        if email:
            qs = qs.filter(email__iexact=email)

        stagiaire_exists = qs.exists()

        if not stagiaire_exists:
            print(f"[POINTAGE] ❌ STAGIAIRE NON TROUVÉ: {prenom} {nom}")
            return Response({
                'success': False,
                'error': f'{prenom} {nom} n\'est pas autorisé à pointer. Veuillez contacter l\'administration.'
            }, status=403)

        # Vérifier si ce type de pointage existe déjà aujourd'hui pour cet élève
        existing_pointages = Pointage.objects.filter(
            nom__iexact=nom,
            prenom__iexact=prenom,
            type_pointage=type_pointage,
            date=today
        )
        
        print(f"[POINTAGE] Vérification doublons: nom={nom}, prenom={prenom}, type={type_pointage}, date={today}")
        print(f"[POINTAGE] Pointages existants trouvés: {existing_pointages.count()}")
        
        if existing_pointages.exists():
            type_label = 'entrée' if type_pointage == 'entree' else 'sortie'
            print(f"[POINTAGE] ❌ DOUBLON DÉTECTÉ: {prenom} {nom} a déjà été pointé(e) en {type_label} aujourd'hui")
            logger.warning(f"Tentative de doublon: {prenom} {nom} - {type_label} déjà pointé aujourd'hui")
            return Response({
                'success': False,
                'error': f'{prenom} {nom} a déjà été pointé(e) en {type_label} aujourd\'hui.'
            }, status=409)

        pointage = Pointage.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            type_pointage=type_pointage,
            heure=heure,
            wa_envoye=wa_envoye
        )

        print(f"[POINTAGE] ✅ Pointage enregistré avec ID: {pointage.id}")
        
        # Générer l'URL WhatsApp
        whatsapp_url = envoyer_whatsapp_message(prenom, nom, type_pointage, heure)
        
        # Vérifier les absences après le pointage (après 3 absences, envoyer une alerte)
        check_absences_and_alert(prenom, nom)
        
        return Response({
            'success': True,
            'id': pointage.id,
            'message': f'Pointage {"entrée" if type_pointage == "entree" else "sortie"} enregistré avec succès pour {prenom} {nom}.',
            'whatsapp_url': whatsapp_url
        }, status=201)

    except Exception as e:
        print(f"[POINTAGE] ERREUR: {e}")
        logger.error(f"Erreur création pointage: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def lister_pointages(request):
    """Lister les pointages du jour avec filtres optionnels"""

    today = timezone.now().date()
    queryset = Pointage.objects.filter(date=today)

    # Filtres optionnels via query params
    email = request.query_params.get('email')
    type_pointage = request.query_params.get('type')
    nom = request.query_params.get('nom')

    if email:
        queryset = queryset.filter(email__iexact=email)
    if type_pointage:
        queryset = queryset.filter(type_pointage=type_pointage)
    if nom:
        queryset = queryset.filter(nom__icontains=nom)

    queryset = queryset.order_by('-timestamp')[:100]

    data = []
    for p in queryset:
        data.append({
            'id': p.id,
            'nom': p.nom,
            'prenom': p.prenom,
            'email': p.email,
            'type': p.type_pointage,
            'heure': p.heure,
            'wa': p.wa_envoye,
            'date': p.date.isoformat(),
            'timestamp': p.timestamp.isoformat()
        })

    return Response({
        'success': True,
        'pointages': data,
        'count': len(data),
        'date': today.isoformat()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def detail_pointage(request, pk):
    """Récupérer le détail d'un pointage"""
    try:
        pointage = Pointage.objects.get(pk=pk)
        return Response({
            'success': True,
            'pointage': {
                'id': pointage.id,
                'nom': pointage.nom,
                'prenom': pointage.prenom,
                'email': pointage.email,
                'type': pointage.type_pointage,
                'heure': pointage.heure,
                'wa': pointage.wa_envoye,
                'date': pointage.date.isoformat(),
                'timestamp': pointage.timestamp.isoformat()
            }
        })
    except Pointage.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Pointage non trouvé.'
        }, status=404)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_pointage(request, pointage_id):
    """Supprimer un pointage individuel."""
    if request.user.role not in ['admin', 'rh', 'manager']:
        return Response({'success': False, 'error': 'Accès refusé'}, status=403)
    try:
        pointage = Pointage.objects.get(pk=pointage_id)
        pointage.delete()
        return Response({'success': True, 'message': 'Pointage supprimé'})
    except Pointage.DoesNotExist:
        return Response({'success': False, 'error': 'Pointage non trouvé'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def statut_eleve(request):
    """
    Vérifier le statut d'un élève aujourd'hui :
    - a-t-il été pointé en entrée ?
    - a-t-il été pointé en sortie ?
    """
    nom = request.query_params.get('nom', '').strip()
    prenom = request.query_params.get('prenom', '').strip()

    if not nom or not prenom:
        return Response({
            'success': False,
            'error': 'Paramètres "nom" et "prenom" requis.'
        }, status=400)

    today = timezone.now().date()

    entree = Pointage.objects.filter(
        nom__iexact=nom,
        prenom__iexact=prenom,
        type_pointage='entree',
        date=today
    ).first()

    sortie = Pointage.objects.filter(
        nom__iexact=nom,
        prenom__iexact=prenom,
        type_pointage='sortie',
        date=today
    ).first()

    return Response({
        'success': True,
        'nom': nom,
        'prenom': prenom,
        'date': today.isoformat(),
        'entree': {
            'fait': entree is not None,
            'heure': entree.heure if entree else None
        },
        'sortie': {
            'fait': sortie is not None,
            'heure': sortie.heure if sortie else None
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def historique_stagiaire(request):
    """Retourne les 7 derniers jours de pointage pour chaque stagiaire"""
    from datetime import timedelta
    from users.models import CustomUser

    today = timezone.now().date()
    stagiaires = CustomUser.objects.filter(role='stagiaire')
    result = []

    def toMinutes(timeStr):
        if not timeStr: return None
        parts = timeStr.split(':')
        return int(parts[0]) * 60 + int(parts[1])

    for s in stagiaires:
        date_debut = s.date_debut_stage if s.date_debut_stage else today
        jours = [today - timedelta(days=i) for i in range(6, -1, -1)]

        jours_data = []
        for jour in jours:
            if jour.weekday() >= 5:
                jours_data.append({'date': jour.isoformat(), 'statut': 'na', 'entree': None, 'sortie': None})
                continue
            if jour < s.date_joined.date():
                jours_data.append({'date': jour.isoformat(), 'statut': 'na', 'entree': None, 'sortie': None})
                continue
            if jour < date_debut:
                jours_data.append({'date': jour.isoformat(), 'statut': 'na', 'entree': None, 'sortie': None})
                continue
            if jour > today:
                jours_data.append({'date': jour.isoformat(), 'statut': 'na', 'entree': None, 'sortie': None})
                continue

            entree = Pointage.objects.filter(
                prenom__iexact=s.first_name,
                nom__iexact=s.last_name,
                type_pointage='entree',
                date=jour
            ).first()
            sortie = Pointage.objects.filter(
                prenom__iexact=s.first_name,
                nom__iexact=s.last_name,
                type_pointage='sortie',
                date=jour
            ).first()

            if not entree:
                statut = 'absent'
            elif toMinutes(entree.heure) > (9*60 + 35):
                statut = 'retard'
            else:
                statut = 'present'

            jours_data.append({
                'date': jour.isoformat(),
                'statut': statut,
                'entree': entree.heure if entree else None,
                'sortie': sortie.heure if sortie else None,
            })

        # ✅ Compter depuis jours_data (source de vérité)
        total_absences = sum(1 for j in jours_data if j['statut'] == 'absent')
        total_retards  = sum(1 for j in jours_data if j['statut'] == 'retard')

        # ✅ Compter les absences justifiées dans le modèle Absence
        absences_justifiees = Absence.objects.filter(
            stagiaire=s,
            justifiee=True,
            date__in=[
                (today - timedelta(days=i)).isoformat()
                for i in range(7)
            ]
        ).count()

        # ✅ Absences NJ = absences réelles - justifiées
        absences_nj = max(0, total_absences - absences_justifiees)

        # ✅ Synchroniser le champ du modèle
        if s.absences_non_justifiees != absences_nj:
            s.absences_non_justifiees = absences_nj
            s.save(update_fields=['absences_non_justifiees'])

        result.append({
            'prenom': s.first_name,
            'nom': s.last_name,
            'email': s.email,
            'ecole': s.ecole if hasattr(s, 'ecole') else '',
            'absences_non_justifiees': absences_nj,   # ✅ Calculé dynamiquement
            'total_absences': total_absences,
            'total_retards': total_retards,
            'jours': jours_data,
        })

    return Response({'success': True, 'stagiaires': result})


@api_view(['POST'])
@permission_classes([AllowAny])
def upload_justification(request):
    """Upload justification et supprime l'absence automatiquement"""
    try:
        from datetime import date
        from users.models import CustomUser
        
        nom = request.data.get('nom', '')
        prenom = request.data.get('prenom', '')
        date_absence = request.data.get('date', date.today().isoformat())
        justification_file = request.FILES.get('justification')
        
        if not justification_file:
            return Response({'success': False, 'error': 'Fichier requis'})
        
        # Trouver le stagiaire
        try:
            stagiaire = CustomUser.objects.get(
                last_name__iexact=nom,
                first_name__iexact=prenom,
                role='stagiaire'
            )
        except CustomUser.DoesNotExist:
            return Response({'success': False, 'error': 'Stagiaire non trouvé'})
        
        # Chercher l'absence du jour
        try:
            absence = Absence.objects.get(
                stagiaire=stagiaire,
                date=date_absence
            )
            # Marquer comme justifiée
            absence.justifiee = True
            absence.justification = justification_file
            absence.save()
            
        except Absence.DoesNotExist:
            # Créer une absence justifiée
            Absence.objects.create(
                stagiaire=stagiaire,
                nom=nom,
                prenom=prenom,
                date=date_absence,
                justifiee=True,
                justification=justification_file
            )
        
        # Recalculer les absences non justifiées
        nb_absences_nj = Absence.objects.filter(
            stagiaire=stagiaire,
            justifiee=False
        ).count()
        
        # Débloquer si moins de 3 absences NJ
        if nb_absences_nj < 3 and not stagiaire.is_active:
            stagiaire.is_active = True
            stagiaire.save()
        
        return Response({
            'success': True,
            'message': 'Justification enregistrée, absence supprimée',
            'nb_absences_nj': nb_absences_nj,
            'debloque': stagiaire.is_active
        })
        
    except Exception as e:
        import traceback
        print(f"[ERROR] upload_justification: {traceback.format_exc()}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def supprimer_absence(request, pk):
    """Supprimer une absence"""
    try:
        absence = Absence.objects.get(pk=pk)
        absence.delete()
        return Response({'success': True})
    except Absence.DoesNotExist:
        return Response({'success': False, 'error': 'Absence non trouvée'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def creer_absence(request):
    """Créer une absence et bloquer si >= 3 absences non justifiées"""
    try:
        from datetime import date
        from users.models import CustomUser
        
        nom = request.data.get('nom', '')
        prenom = request.data.get('prenom', '')
        date_absence = request.data.get('date', date.today().isoformat())
        justifiee = request.data.get('justifiee', False)
        
        # Trouver le stagiaire
        try:
            stagiaire = CustomUser.objects.get(
                last_name__iexact=nom,
                first_name__iexact=prenom,
                role='stagiaire'
            )
        except CustomUser.DoesNotExist:
            return Response({'success': False, 'error': 'Stagiaire non trouvé'})
        
        # Créer l'absence
        absence = Absence.objects.create(
            stagiaire=stagiaire,
            nom=nom,
            prenom=prenom,
            date=date_absence,
            justifiee=justifiee
        )
        
        # Compter les absences non justifiées
        nb_absences_nj = Absence.objects.filter(
            stagiaire=stagiaire,
            justifiee=False
        ).count()
        
        bloque = False
        whatsapp_url = None
        
        # Bloquer si >= 3 absences non justifiées
        if nb_absences_nj >= 3:
            stagiaire.is_active = False
            stagiaire.save()
            bloque = True
            
            # Générer message WhatsApp pour admin
            message = f"""🚨 *ALERTE BLOCAGE - Orchid Island*

Le stagiaire *{prenom} {nom}* a atteint 3 absences non justifiées.

📊 Absences non justifiées: {nb_absences_nj}/3
🔒 Compte: BLOQUÉ AUTOMATIQUEMENT

Veuillez prendre les mesures nécessaires.

_Orchid Island - Système RH_"""
            
            wa_number = settings.WHATSAPP_DESTINATION_NUMBER
            import urllib.parse
            whatsapp_url = f"https://wa.me/{wa_number}?text={urllib.parse.quote(message)}"
        
        return Response({
            'success': True,
            'absence_id': absence.id,
            'nb_absences_nj': nb_absences_nj,
            'bloque': bloque,
            'whatsapp_url': whatsapp_url,
            'message': f'Absence enregistrée. {"Stagiaire bloqué (3 absences NJ)!" if bloque else ""}'
        })
        
    except Exception as e:
        import traceback
        print(f"[ERROR] creer_absence: {traceback.format_exc()}")
        return Response({'success': False, 'error': str(e)}, status=500)