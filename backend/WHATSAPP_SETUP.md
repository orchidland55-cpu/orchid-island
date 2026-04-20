# Configuration de l'envoi automatique WhatsApp

## Problème résolu
Le système envoie maintenant automatiquement les messages WhatsApp lors de chaque pointage.

## Étapes de configuration

### 1. Créer un compte Twilio
1. Allez sur https://www.twilio.com/
2. Créez un compte gratuit
3. Vérifiez votre numéro de téléphone

### 2. Obtenir les credentials
Une fois connecté :
1. Allez dans la console Twilio : https://www.twilio.com/console
2. Copiez votre **Account SID** (commence par AC...)
3. Copiez votre **Auth Token**
4. Notez votre numéro WhatsApp Twilio (format : whatsapp:+14155238886)

### 3. Configurer le fichier .env
Éditez le fichier `/Users/mac/Desktop/orchid-island/backend/.env` et remplacez les valeurs :

```env
TWILIO_ACCOUNT_SID=votre_account_sid_ici
TWILIO_AUTH_TOKEN=votre_auth_token_ici
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
WHATSAPP_DESTINATION_NUMBER=212681314877
```

### 4. Installer python-dotenv
```bash
cd /Users/mac/Desktop/orchid-island/backend
source env/bin/activate
pip install python-dotenv
```

### 5. Modifier settings.py pour charger le .env
Ajoutez au début du fichier settings.py :
```python
from dotenv import load_dotenv
load_dotenv()
```

### 6. Redémarrer le serveur
```bash
cd /Users/mac/Desktop/orchid-island/backend
source env/bin/activate
python manage.py runserver 0.0.0.0:8000
```

## Test
Faites un pointage depuis l'application mobile. Vous devriez recevoir un message WhatsApp automatiquement.

## Dépannage
- Si le message ne s'envoie pas, vérifiez les logs du serveur
- Assurez-vous que le numéro de destination est au bon format (sans le +)
- Vérifiez que vous avez des crédits Twilio (le compte gratuit offre des crédits de test)
