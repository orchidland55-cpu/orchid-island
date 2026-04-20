/**
 * auth_roles.js
 * ─────────────────────────────────────────────────────────────
 * Coller ce script dans un fichier auth_roles.js
 * et l'inclure dans CHAQUE page HTML avec :
 *   <script src="auth_roles.js"></script>
 * 
 * OU coller le contenu directement dans le <script> de chaque page.
 * ─────────────────────────────────────────────────────────────
 */

// ── 1. Récupérer l'utilisateur connecté ──────────────────────
function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null');
  } catch { return null; }
}

function getToken() {
  return localStorage.getItem('access_token') || null;
}

// ── 2. Rediriger si non connecté ─────────────────────────────
function requireAuth() {
  const user = getCurrentUser();
  const token = getToken();
  if (!user || !token) {
    window.location.href = 'authentification.html';
    return null;
  }
  if (!user.is_active && user.role !== 'admin') {
    alert('⛔ Votre compte est bloqué. Contactez le RH ou l\'Admin.');
    localStorage.clear();
    window.location.href = 'authentification.html';
    return null;
  }
  return user;
}

// ── 3. Définir les pages autorisées par rôle ─────────────────
const ROLE_PAGES = {
  admin: [
    'dashboard.html',
    'stagiaires.html',
    'projets.html',
    'taches.html',
    'rapports.html',
    'alertes.html',
    'pointage_qr.html',
  ],
  rh: [
    'dashboard.html',
    'stagiaires.html',
    'rapports.html',
    'alertes.html',
  ],
  manager: [
    'dashboard.html',
    'projets.html',
    'taches.html',
    'rapports.html',
  ],
  stagiaire: [
    'dashboard.html',
    'scan_mobile.html',
    'rapports.html',       // déposer ses propres rapports
  ],
};

// ── 4. Vérifier si la page courante est autorisée ────────────
function checkRoleAccess() {
  const user = requireAuth();
  if (!user) return;

  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  const allowed = ROLE_PAGES[user.role] || [];

  if (!allowed.includes(currentPage)) {
    alert(`⛔ Accès refusé.\nVotre rôle (${user.role.toUpperCase()}) n'a pas accès à cette page.`);
    window.location.href = 'dashboard.html';
    return;
  }

  // Afficher le rôle dans la sidebar si l'élément existe
  const roleEl = document.getElementById('userRole');
  const nameEl = document.getElementById('userName');
  if (roleEl) {
    const labels = { admin: '👑 Administrateur', rh: '🛠️ RH', manager: '👤 Manager', stagiaire: '🎓 Stagiaire' };
    roleEl.textContent = labels[user.role] || user.role;
  }
  if (nameEl) {
    nameEl.textContent = `${user.first_name} ${user.last_name}`;
  }

  return user;
}

// ── 5. Navigation : masquer les liens non autorisés ──────────
function filterNavByRole() {
  const user = getCurrentUser();
  if (!user) return;

  // Mapping lien → rôles autorisés
  const NAV_PERMISSIONS = {
    'stagiaires.html':  ['admin', 'rh'],
    'projets.html':     ['admin', 'manager'],
    'taches.html':      ['admin', 'manager'],
    'rapports.html':    ['admin', 'rh', 'manager', 'stagiaire'],
    'alertes.html':     ['admin', 'rh'],
    'pointage_qr.html': ['admin'],
    'scan_mobile.html': ['stagiaire'],
    'dashboard.html':   ['admin', 'rh', 'manager', 'stagiaire'],
  };

  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href').split('/').pop();
    const allowed = NAV_PERMISSIONS[href];
    if (allowed && !allowed.includes(user.role)) {
      // Masquer le lien et son parent <li> si existe
      const li = link.closest('li') || link;
      li.style.display = 'none';
    }
  });
}

// ── 6. Redirection après login selon le rôle ─────────────────
function redirectAfterLogin(user) {
  const destinations = {
    admin:     'dashboard.html',
    rh:        'dashboard.html',
    manager:   'dashboard.html',
    stagiaire: 'dashboard.html',
  };
  window.location.href = destinations[user.role] || 'dashboard.html';
}

// ── 7. Headers avec token pour les appels API ─────────────────
function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}` 
  };
}

// ── 8. Déconnexion ────────────────────────────────────────────
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = 'authentification.html';
}

// ── 9. Appel API absences avec logique WhatsApp ───────────────
async function enregistrerAbsence(stagiaire_id, stagiaire_phone, stagiaire_nom) {
  const BACKEND_URL = 'http://localhost:8000'; // adapter si besoin
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/absence/enregistrer/`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ stagiaire_id })
    });
    const data = await res.json();

    if (data.whatsapp_message) {
      // Ouvrir WhatsApp avec le message pré-rempli
      const phone = (stagiaire_phone || '').replace(/\D/g, '');
      if (phone) {
        const url = `https://wa.me/${phone}?text=${encodeURIComponent(data.whatsapp_message)}`;
        window.open(url, '_blank');
      }
    }

    if (data.compte_bloque) {
      alert(`🚫 Le compte de ${stagiaire_nom} a été bloqué automatiquement (3 absences non justifiées).`);
    }

    return data;
  } catch (e) {
    console.error('Erreur enregistrement absence:', e);
  }
}

// ── 10. Débloquer un compte (Admin/RH seulement) ─────────────
async function debloquerCompte(stagiaire_id, stagiaire_nom) {
  const BACKEND_URL = 'http://localhost:8000';
  const user = getCurrentUser();
  if (!user || !['admin', 'rh'].includes(user.role)) {
    alert('⛔ Seuls Admin et RH peuvent débloquer un compte.');
    return;
  }
  if (!confirm(`Débloquer le compte de ${stagiaire_nom} et remettre le compteur d'absences à zéro ?`)) return;

  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/compte/debloquer/${stagiaire_id}/`, {
      method: 'POST',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (data.success) {
      alert(`✅ ${data.message}`);
      location.reload();
    } else {
      alert(`❌ ${data.error}`);
    }
  } catch (e) {
    console.error('Erreur déblocage:', e);
  }
}
