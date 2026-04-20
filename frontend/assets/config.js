// config.js — Configuration centralisée de l'URL backend
// ⚠️ Modifiez BACKEND_URL selon votre environnement

const CONFIG = {
  // En production (Railway/Render)
  // BACKEND_URL: 'https://votre-app.up.railway.app',
  
  // En développement local (commentez la ligne prod, décommentez celle-ci)
  BACKEND_URL: 'http://192.168.11.249:8000',
  
  // Numéro WhatsApp admin
  WA_ADMIN: '212681314877',
};

// Auto-détection de l'environnement
if (window.location.hostname === 'localhost' || 
    window.location.hostname === '127.0.0.1') {
  CONFIG.BACKEND_URL = 'http://127.0.0.1:8000';
} else if (window.location.hostname.includes('192.168')) {
  CONFIG.BACKEND_URL = `http://${window.location.hostname}:8000`;
}
// Sinon utilise l'URL de production définie ci-dessus

window.BACKEND_URL = CONFIG.BACKEND_URL;
