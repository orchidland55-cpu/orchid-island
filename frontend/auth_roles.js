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
  
  // ✅ Si on est déjà sur la page d'auth, ne pas rediriger
  const currentPage = window.location.pathname;
  const isAuthPage = currentPage.includes('authentification') || 
                     currentPage === '/' ||
                     currentPage.includes('/login');
  
  if (!user || !token) {
    if (!isAuthPage) {
      window.location.href = 'authentification.html';
    }
    return null;
  }
  if (!user.is_active && user.role !== 'admin') {
    alert('⛔ Votre compte est bloqué. Contactez le RH ou l\'Admin.');
    localStorage.clear();
    if (!isAuthPage) {
      window.location.href = 'authentification.html';
    }
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

  const role = user.role || '';
  const path = window.location.pathname;

  // ✅ Si stagiaire essaie d'accéder à une page admin
  if (role === 'stagiaire') {
    const forbidden = ['stagiaires', 'pointage_qr', 'alertes', 'projets'];
    const isForbidden = forbidden.some(p => path.includes(p));
    
    if (isForbidden) {
      // ✅ Afficher belle page d'erreur au lieu de alert()
      showAccessDenied(role);
      return null;
    }
  }

  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  const allowed = ROLE_PAGES[user.role] || [];

  if (!allowed.includes(currentPage)) {
    showAccessDenied(user.role);
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

// ── Afficher une belle page d'erreur pour accès refusé ─────────
function showAccessDenied(role) {
  // Masquer tout le contenu
  document.body.innerHTML = `
    <div style="
      min-height: 100vh;
      background: #07070A;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Inter', sans-serif;
    ">
      <!-- Orbes animés -->
      <div style="position:fixed;inset:0;pointer-events:none;overflow:hidden;">
        <div style="position:absolute;width:500px;height:500px;background:radial-gradient(circle,#004BA8,transparent);
          border-radius:50%;filter:blur(80px);opacity:0.15;top:-100px;right:-100px;
          animation:float 8s ease-in-out infinite;"></div>
        <div style="position:absolute;width:400px;height:400px;background:radial-gradient(circle,#E74C3C,transparent);
          border-radius:50%;filter:blur(80px);opacity:0.1;bottom:-80px;left:10%;
          animation:float 8s ease-in-out infinite 3s;"></div>
      </div>

      <div style="
        text-align: center;
        position: relative;
        z-index: 1;
        max-width: 480px;
        padding: 20px;
      ">
        <!-- Icône -->
        <div style="
          width: 100px; height: 100px;
          background: linear-gradient(135deg, rgba(231,76,60,0.2), rgba(231,76,60,0.05));
          border: 1px solid rgba(231,76,60,0.3);
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-size: 48px;
          margin: 0 auto 32px;
          box-shadow: 0 0 60px rgba(231,76,60,0.2);
          animation: pulse 2s ease-in-out infinite;
        ">🔒</div>

        <!-- Titre -->
        <div style="
          font-family: 'Syne', sans-serif;
          font-size: 32px;
          font-weight: 800;
          color: #F0F4F8;
          margin-bottom: 12px;
        ">Accès Restreint</div>

        <!-- Sous-titre -->
        <div style="
          color: #B8C5D6;
          font-size: 16px;
          margin-bottom: 8px;
          line-height: 1.5;
        ">
          Cette page est réservée aux administrateurs et responsables RH.
        </div>

        <!-- Badge rôle -->
        <div style="
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: rgba(231,76,60,0.1);
          border: 1px solid rgba(231,76,60,0.25);
          border-radius: 20px;
          padding: 6px 16px;
          margin-bottom: 40px;
          font-size: 13px;
          color: #E74C3C;
          font-weight: 600;
        ">
          <span style="width:8px;height:8px;border-radius:50%;background:#E74C3C;display:inline-block;"></span>
          Votre rôle : ${role.toUpperCase()}
        </div>

        <!-- Boutons -->
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
          <button onclick="window.history.back()" style="
            padding: 14px 28px;
            background: transparent;
            border: 1px solid #4A525A;
            border-radius: 12px;
            color: #B8C5D6;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Inter', sans-serif;
          " onmouseover="this.style.borderColor='#B8C5D6';this.style.color='#F0F4F8'"
             onmouseout="this.style.borderColor='#4A525A';this.style.color='#B8C5D6'">
            ← Retour
          </button>

          <button onclick="window.location.href='dashboard.html'" style="
            padding: 14px 28px;
            background: linear-gradient(135deg, #004BA8, #3E78B2);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 8px 24px rgba(0,75,168,0.3);
          ">
            🏠 Mon Espace
          </button>

          <button onclick="localStorage.clear();window.location.href='authentification.html'" style="
            padding: 14px 28px;
            background: rgba(231,76,60,0.1);
            border: 1px solid rgba(231,76,60,0.3);
            border-radius: 12px;
            color: #E74C3C;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
          ">
            Déconnexion
          </button>
        </div>
      </div>

      <style>
        @keyframes float {
          0%,100%{transform:translateY(0) scale(1);}
          50%{transform:translateY(-20px) scale(1.05);}
        }
        @keyframes pulse {
          0%,100%{box-shadow:0 0 60px rgba(231,76,60,0.2);}
          50%{box-shadow:0 0 80px rgba(231,76,60,0.4);}
        }
      </style>
    </div>
  `;
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
