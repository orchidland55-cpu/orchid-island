// config.js — URL du backend selon l'environnement
const CONFIG = {
  // En production : URL Render
  BACKEND_URL: 'https://orchid-island-api.onrender.com',
  
  // En local : commenter la ligne ci-dessus et décommenter celle-ci
  // BACKEND_URL: 'http://192.168.11.249:8000',
};

window.BACKEND_URL = CONFIG.BACKEND_URL;
