(function() {
  const hostname = window.location.hostname;
  console.log('[CONFIG] hostname:', hostname);
  
  if (hostname === '127.0.0.1' || hostname === 'localhost') {
    window.BACKEND_URL = 'http://127.0.0.1:8000';
  } else if (hostname.startsWith('192.168.')) {
    window.BACKEND_URL = `http://${hostname}:8000`;
  } else {
    // ✅ Vercel et tout autre domaine → Railway
    window.BACKEND_URL = 'https://orchid-island-production.up.railway.app';
  }
  
  console.log('[CONFIG] BACKEND_URL:', window.BACKEND_URL);
  console.log('[CONFIG] Script loaded at:', new Date().toISOString());
})();
