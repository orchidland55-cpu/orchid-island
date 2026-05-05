// config.js — détection automatique selon l'hostname
(function() {
  const hostname = window.location.hostname;

  if (hostname === '127.0.0.1' || hostname === 'localhost') {
    // Navigateur sur le Mac → backend local
    window.BACKEND_URL = 'http://127.0.0.1:8000';
  } else if (hostname.startsWith('192.168.')) {
    // Téléphone sur le réseau WiFi → backend local sur même IP
    window.BACKEND_URL = `http://${hostname}:8000`;
  } else {
    // Téléphone sur le réseau WiFi ou autre → backend Render
    window.BACKEND_URL = 'https://orchid-island-api.onrender.com';
  }

  console.log('[CONFIG] BACKEND_URL:', window.BACKEND_URL);
})();
