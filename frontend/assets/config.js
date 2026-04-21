// config.js — URL du backend selon l'environnement
const CONFIG = {
  // En local : utiliser l'adresse IP locale
  BACKEND_URL: 'http://192.168.11.249:8000',
  
  // En production : commenter la ligne ci-dessus et décommenter celle-ci
  // BACKEND_URL: 'https://orchid-island-api.onrender.com',
};

window.BACKEND_URL = CONFIG.BACKEND_URL;
