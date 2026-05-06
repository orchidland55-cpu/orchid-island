// Fichier commun pour l'authentification, la navigation et le partage de données

// Système de données partagées entre toutes les interfaces
class SharedData {
  constructor() {
    this.initializeData();
    this.setupEventListeners();
  }

  initializeData() {
    // Initialiser les données si elles n'existent pas
    if (!localStorage.getItem('orchid_shared_data')) {
      const initialData = {
        stagiaires: {
          total: 0,
          actifs: 0,
          enAttente: 0,
          bloques: 0,
          absences: 0,
          list: []
        },
        projets: {
          total: 0,
          enCours: 0,
          termines: 0,
          enRetard: 0,
          avancementMoyen: 0,
          list: []
        },
        rapports: {
          aujourdhui: 0,
          manquants: 0,
          finauxDeposes: 0,
          finauxValides: 0,
          enAttente: 0,
          list: []
        },
        alertes: [],
        presences: {
          Lundi: { presents: 0, absents: 0 },
          Mardi: { presents: 0, absents: 0 },
          Mercredi: { presents: 0, absents: 0 },
          Jeudi: { presents: 0, absents: 0 },
          Vendredi: { presents: 0, absents: 0 },
          Samedi: { presents: 0, absents: 0 },
          Dimanche: { presents: 0, absents: 0 }
        },
        presencesMensuelles: {
          Jan: { presents: 0, absents: 0 },
          Fév: { presents: 0, absents: 0 },
          Mar: { presents: 0, absents: 0 },
          Avr: { presents: 0, absents: 0 },
          Mai: { presents: 0, absents: 0 },
          Jun: { presents: 0, absents: 0 },
          Jul: { presents: 0, absents: 0 },
          Aoû: { presents: 0, absents: 0 },
          Sep: { presents: 0, absents: 0 },
          Oct: { presents: 0, absents: 0 },
          Nov: { presents: 0, absents: 0 },
          Déc: { presents: 0, absents: 0 }
        },
        pointages: [],
        taches: {
          'À Faire': [],
          'En Cours': [],
          'Terminé': []
        }
      };
      localStorage.setItem('orchid_shared_data', JSON.stringify(initialData));
    }
  }

  getData() {
    return JSON.parse(localStorage.getItem('orchid_shared_data') || '{}');
  }

  updateData(section, data) {
    const currentData = this.getData();
    currentData[section] = { ...currentData[section], ...data };
    localStorage.setItem('orchid_shared_data', JSON.stringify(currentData));
    
    // Émettre un événement pour notifier les autres pages
    window.dispatchEvent(new CustomEvent('dataUpdated', { 
      detail: { section, data: currentData[section] } 
    }));
  }

  addAlerte(alerte) {
    const currentData = this.getData();
    alerte.id = Date.now();
    alerte.read = false;
    currentData.alertes.unshift(alerte);
    
    // Limiter à 10 alertes maximum
    if (currentData.alertes.length > 10) {
      currentData.alertes = currentData.alertes.slice(0, 10);
    }
    
    this.updateData('alertes', currentData.alertes);
  }

  markAlerteAsRead(alerteId) {
    const currentData = this.getData();
    const alerte = currentData.alertes.find(a => a.id === alerteId);
    if (alerte) {
      alerte.read = true;
      this.updateData('alertes', currentData.alertes);
    }
  }

  getUnreadAlertesCount() {
    const currentData = this.getData();
    return currentData.alertes.filter(a => !a.read).length;
  }

  addPointage(pointage) {
    const currentData = this.getData();
    pointage.id = Date.now();
    pointage.timestamp = new Date().toISOString();
    currentData.pointages.unshift(pointage);
    
    // Limiter à 50 pointages maximum
    if (currentData.pointages.length > 50) {
      currentData.pointages = currentData.pointages.slice(0, 50);
    }
    
    this.updateData('pointages', currentData.pointages);
    
    // Mettre à jour les présences
    this.updatePresences();
  }

  updatePresences() {
    const currentData = this.getData();
    const today = new Date().toLocaleDateString('fr-FR', { weekday: 'long' });
    
    // Simuler une mise à jour des présences
    if (currentData.presences[today]) {
      currentData.presences[today].presents += Math.floor(Math.random() * 3);
      this.updateData('presences', currentData.presences);
    }
  }

  addAlerte(alerte) {
    const currentData = this.getData();
    alerte.id = Date.now();
    alerte.read = false;
    
    currentData.alertes.unshift(alerte);
    
    // Limiter à 20 alertes maximum
    if (currentData.alertes.length > 20) {
      currentData.alertes = currentData.alertes.slice(0, 20);
    }
    
    this.updateData('alertes', currentData.alertes);
  }

  markAlerteAsRead(alerteId) {
    const currentData = this.getData();
    const alerte = currentData.alertes.find(a => a.id === alerteId);
    if (alerte) {
      alerte.read = true;
      this.updateData('alertes', currentData.alertes);
    }
  }

  getUnreadAlertesCount() {
    const currentData = this.getData();
    return currentData.alertes.filter(a => !a.read).length;
  }

  setupEventListeners() {
    // Écouter les mises à jour de données
    window.addEventListener('dataUpdated', (event) => {
      console.log('Données mises à jour:', event.detail);
    });
    
    // Écouter les modifications de localStorage pour synchroniser automatiquement
    window.addEventListener('storage', (event) => {
      console.log('[SYNC] Modification détectée dans localStorage:', event.key);
      
      // Synchroniser les données correspondantes
      if (event.key === 'stagiaires') {
        this.syncStagiairesData();
      } else if (event.key === 'rapports') {
        this.syncRapportsData();
      } else if (event.key === 'orchidData') {
        this.syncProjetsData();
      }
    });
  }
  
  // Fonction pour synchroniser toutes les données automatiquement
  syncAllData() {
    console.log('[SYNC] Synchronisation de toutes les données...');
    this.syncStagiairesData();
    this.syncRapportsData();
    this.syncProjetsData();
  }

  // Synchroniser les données de projets entre orchidData et orchid_shared_data
  syncProjetsData() {
    try {
      // Lire depuis orchidData (utilisé par projets.html et taches.html)
      const orchidData = JSON.parse(localStorage.getItem('orchidData') || '{"projets":{"list":[]}}');
      const projetsList = orchidData.projets?.list || [];
      
      // Calculer les statistiques
      const projetsEnCours = projetsList.filter(p => p.etat === 'encours').length;
      const projetsTermines = projetsList.filter(p => p.etat === 'done' || p.etat === 'termine').length;
      const projetsEnRetard = projetsList.filter(p => p.etat === 'retard').length;
      
      // Mettre à jour orchid_shared_data
      this.updateData('projets', {
        total: projetsList.length,
        enCours: projetsEnCours,
        termines: projetsTermines,
        enRetard: projetsEnRetard,
        list: projetsList
      });
      
      console.log('[SYNC] Projets synchronisés:', projetsList.length, 'projets');
    } catch (e) {
      console.error('[SYNC] Erreur synchronisation projets:', e);
    }
  }

  // Synchroniser les données de stagiaires depuis localStorage vers orchid_shared_data
  syncStagiairesData() {
    try {
      const stagiaires = JSON.parse(localStorage.getItem('stagiaires') || '[]');
      
      const actifs = stagiaires.filter(s => s.statut === 'Accepté' || s.statut === 'actif' || !s.statut).length;
      const bloques = stagiaires.filter(s => s.statut === 'Refusé' || s.statut === 'bloque').length;
      const enAttente = stagiaires.filter(s => s.statut === 'En attente' || s.statut === 'en_attente' || s.statut === 'pending').length;
      
      this.updateData('stagiaires', {
        total: stagiaires.length,
        actifs: actifs,
        enAttente: enAttente,
        bloques: bloques,
        list: stagiaires
      });
      
      console.log('[SYNC] Stagiaires synchronisés:', stagiaires.length, 'stagiaires');
    } catch (e) {
      console.error('[SYNC] Erreur synchronisation stagiaires:', e);
    }
  }

  // Synchroniser les données de rapports depuis localStorage vers orchid_shared_data
  syncRapportsData() {
    try {
      const rapportsData = JSON.parse(localStorage.getItem('rapports') || '{"list":[],"finaux":[]}');
      const journaliers = rapportsData.list || [];
      const finaux = rapportsData.finaux || [];
      
      const today = new Date().toLocaleDateString('fr-FR');
      const rapportsAujourdhui = journaliers.filter(r => r.date === today).length;
      const finauxEnAttente = finaux.filter(r => r.statut === 'attente').length;
      
      this.updateData('rapports', {
        aujourdhui: rapportsAujourdhui,
        manquants: 0,
        finauxDeposes: finaux.length,
        finauxValides: finaux.filter(r => r.statut === 'valide').length,
        enAttente: finauxEnAttente,
        list: journaliers
      });
      
      console.log('[SYNC] Rapports synchronisés');
    } catch (e) {
      console.error('[SYNC] Erreur synchronisation rapports:', e);
    }
  }
}

// Instance globale des données partagées
window.sharedData = new SharedData();

// Vérification de l'authentification
function checkAuth() {
  const token = localStorage.getItem('access_token');
  const user = localStorage.getItem('user');
  
  if (!token || !user) {
    window.location.href = 'authentification.html';
    return null;
  }
  
  return JSON.parse(user);
}

// Afficher les informations utilisateur
function displayUserInfo(user) {
  // Mettre à jour l'avatar basé sur le rôle
  const avatarElement = document.getElementById('userAvatar');
  if (avatarElement) {
    const roleIcons = {
      'admin': 'Admin',
      'rh': 'RH',
      'manager': 'Mgr',
      'stagiaire': 'Stag'
    };
    avatarElement.textContent = roleIcons[user.role] || 'User';
  }
  
  // Mettre à jour le nom d'utilisateur
  const userElement = document.getElementById('userName');
  if (userElement) {
    userElement.textContent = `${user.first_name} ${user.last_name}`;
  }
  
  // Mettre à jour l'email
  const emailElement = document.getElementById('userEmail');
  if (emailElement) {
    emailElement.textContent = user.email;
  }
  
  // Mettre à jour le rôle
  const roleElement = document.getElementById('userRole');
  if (roleElement) {
    const roleNames = {
      'admin': 'Administrateur',
      'rh': 'RH',
      'manager': 'Manager',
      'stagiaire': 'Stagiaire'
    };
    roleElement.textContent = roleNames[user.role] || user.role;
  }
}

// Fonction de navigation - compatible avec Django (port 8000) et Live Server (port 5500)
function navigateTo(page) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = 'authentification.html';
    return;
  }
  
  // Si on est sur le port 8000 (Django), utiliser l'URL sans extension
  if (window.location.origin.includes(':8000')) {
    // Remplacer .html par /
    const djangoUrl = page.replace('.html', '/');
    window.location.href = '/' + djangoUrl;
  } else {
    // Sinon, comportement normal
    window.location.href = page;
  }
}

// Fonction de déconnexion
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = 'authentification.html';
}

// ===== GESTION TOKENS JWT =====

function getToken() {
  return localStorage.getItem('access_token');
}

async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) {
    logout();
    return null;
  }

  try {
    const BACKEND_URL = window.BACKEND_URL || 'http://127.0.0.1:8000';
    const response = await fetch(`${BACKEND_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    });

    const data = await response.json();

    if (data.access) {
      localStorage.setItem('access_token', data.access);
      console.log('[TOKEN] Token rafraîchi avec succès');
      return data.access;
    } else {
      console.error('[TOKEN] Refresh échoué:', data);
      logout();
      return null;
    }
  } catch(e) {
    console.error('[TOKEN] Erreur refresh:', e);
    logout();
    return null;
  }
}

// ✅ Nouvelle version qui gère le 401 automatiquement
async function fetchWithAuth(url, options = {}) {
  const BACKEND_URL = window.BACKEND_URL || 'http://127.0.0.1:8000';
  const fullUrl = url.startsWith('http') ? url : BACKEND_URL + url;

  // ✅ Ne pas forcer Content-Type si le body est FormData
  const isFormData = options.body instanceof FormData;

  options.headers = {
    'Authorization': `Bearer ${getToken()}`,
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers || {})
  };

  // Supprimer Content-Type si undefined (cas legacy)
  if (options.headers['Content-Type'] === undefined) {
    delete options.headers['Content-Type'];
  }

  let response = await fetch(fullUrl, options);

  // Si 401 → rafraîchir le token et réessayer une fois
  if (response.status === 401) {
    console.log('[AUTH] Token expiré, tentative de refresh...');
    const newToken = await refreshToken();

    if (newToken) {
      options.headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(fullUrl, options);
    } else {
      return null; // logout() déjà appelé dans refreshToken()
    }
  }

  return response;
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  };
}

// Mettre à jour les badges de navigation avec les vraies données
function updateNavBadges() {
  // Synchroniser les données d'abord
  if (window.sharedData) {
    window.sharedData.syncStagiairesData();
    window.sharedData.syncRapportsData();
  }
  
  // Mettre à jour le badge des stagiaires
  const badgeStagiaires = document.getElementById('badgeStagiaires');
  if (badgeStagiaires) {
    let stagiairesCount = 0;
    try {
      const stored = JSON.parse(localStorage.getItem('stagiaires') || '[]');
      stagiairesCount = stored.length;
    } catch (e) {
      console.error('[COMMON] Erreur lors du comptage des stagiaires:', e);
    }
    badgeStagiaires.textContent = stagiairesCount;
    badgeStagiaires.style.display = stagiairesCount > 0 ? 'inline-block' : 'none';
  }
  
  // Mettre à jour le badge des rapports
  const badgeRapports = document.getElementById('badgeRapports');
  if (badgeRapports) {
    let rapportsCount = 0;
    try {
      const rapportsData = JSON.parse(localStorage.getItem('rapports') || '{"list":[],"finaux":[]}');
      const finaux = rapportsData.finaux || [];
      const journaliers = rapportsData.list || [];
      // Compter les rapports finaux en attente
      const finauxEnAttente = finaux.filter(r => r.statut === 'attente').length;
      // Compter les rapports journaliers d'aujourd'hui
      const today = new Date().toLocaleDateString('fr-FR');
      const rapportsAujourdhui = journaliers.filter(r => r.date === today).length;
      rapportsCount = finauxEnAttente + rapportsAujourdhui;
    } catch (e) {
      console.error('[COMMON] Erreur lors du comptage des rapports:', e);
    }
    badgeRapports.textContent = rapportsCount;
    badgeRapports.style.display = rapportsCount > 0 ? 'inline-block' : 'none';
  }
  
  // Mettre à jour le badge des alertes via AlertManager
  const badgeAlertes = document.getElementById('badgeAlertes');
  if (badgeAlertes) {
    let alertesCount = 0;
    try {
      if (window.alertManager && typeof window.alertManager.getUnreadAlertesCount === 'function') {
        alertesCount = window.alertManager.getUnreadAlertesCount();
      }
    } catch (e) {
      console.error('[COMMON] Erreur lors du comptage des alertes:', e);
    }
    badgeAlertes.textContent = alertesCount;
    badgeAlertes.style.display = alertesCount > 0 ? 'inline-block' : 'none';
  }
}

// ==================== SYSTÈME D'ALERTES ET ABSENCES ====================

// Classe pour gérer les absences et les alertes
class AlertManager {
  constructor() {
    this.initStorage();
  }

  initStorage() {
    // Initialiser le stockage des absences si inexistant
    if (!localStorage.getItem('absences')) {
      localStorage.setItem('absences', JSON.stringify([]));
    }
    // Initialiser le stockage des alertes système si inexistant
    if (!localStorage.getItem('system_alerts')) {
      localStorage.setItem('system_alerts', JSON.stringify([]));
    }
    // Initialiser le stockage des nouveaux stagiaires
    if (!localStorage.getItem('new_stagiaires')) {
      localStorage.setItem('new_stagiaires', JSON.stringify([]));
    }
  }

  // Récupérer toutes les absences
  getAbsences() {
    return JSON.parse(localStorage.getItem('absences') || '[]');
  }

  // Sauvegarder les absences
  saveAbsences(absences) {
    localStorage.setItem('absences', JSON.stringify(absences));
  }

  // Ajouter une absence pour un stagiaire
  addAbsence(stagiaireId, nom, date, type = 'non_justifiee', justification = null) {
    const absences = this.getAbsences();
    const existingIndex = absences.findIndex(a => a.stagiaireId === stagiaireId && a.date === date);
    
    if (existingIndex === -1) {
      absences.push({
        id: Date.now(),
        stagiaireId,
        nom,
        date,
        type,
        justification,
        createdAt: new Date().toISOString()
      });
      this.saveAbsences(absences);
      this.checkAlertesAbsences(stagiaireId, nom);
    }
  }

  // Justifier une absence avec fichier PDF
  justifyAbsence(absenceId, fichierJustification) {
    const absences = this.getAbsences();
    const absence = absences.find(a => a.id === absenceId);
    if (absence) {
      absence.type = 'justifiee';
      absence.justification = {
        fichier: fichierJustification,
        date: new Date().toISOString()
      };
      this.saveAbsences(absences);
      return true;
    }
    return false;
  }

  // Récupérer les absences non justifiées d'un stagiaire
  getAbsencesNonJustifiees(stagiaireId) {
    const absences = this.getAbsences();
    return absences.filter(a => a.stagiaireId === stagiaireId && a.type === 'non_justifiee');
  }

  // Vérifier si un stagiaire doit recevoir une alerte (3 absences)
  checkAlertesAbsences(stagiaireId, nom) {
    const absencesNonJustifiees = this.getAbsencesNonJustifiees(stagiaireId);
    
    if (absencesNonJustifiees.length >= 3) {
      this.addSystemAlert({
        type: 'critique',
        category: 'absences',
        stagiaireId,
        nom,
        message: `${nom} a ${absencesNonJustifiees.length} absences non justifiées`,
        details: `Le stagiaire a atteint ${absencesNonJustifiees.length} absences sans justification. Compte susceptible d'être bloqué.`,
        date: new Date().toISOString(),
        read: false
      });
    } else if (absencesNonJustifiees.length === 2) {
      this.addSystemAlert({
        type: 'avertissement',
        category: 'absences',
        stagiaireId,
        nom,
        message: `${nom} a 2 absences non justifiées`,
        details: `Attention: 1 absence supplémentaire entraînera un blocage du compte.`,
        date: new Date().toISOString(),
        read: false
      });
    }
  }

  // Récupérer les alertes système
  getSystemAlerts() {
    return JSON.parse(localStorage.getItem('system_alerts') || '[]');
  }

  // Sauvegarder les alertes système
  saveSystemAlerts(alerts) {
    localStorage.setItem('system_alerts', JSON.stringify(alerts));
  }

  // Ajouter une alerte système
  addSystemAlert(alert) {
    const alerts = this.getSystemAlerts();

    // Vérifier si une alerte similaire existe déjà (déduplication)
    const isDuplicate = alerts.some(a =>
      (alert.alertKey && a.alertKey === alert.alertKey) ||
      (
        a.category === alert.category &&
        a.nom === alert.nom &&
        a.dateAbsence === alert.dateAbsence &&  // ← clé principale
        !a.justifiee
      )
    );

    if (isDuplicate) {
      console.log('[ALERTMANAGER] Alerte en double détectée, ignorée:', alert.message);
      return null;
    }

    alert.id = Date.now();
    alerts.unshift(alert);
    this.saveSystemAlerts(alerts);
    this.updateAlertesBadge();
    window.dispatchEvent(new CustomEvent('dataUpdated', { detail: { section: 'alertes' } }));
    return alert;
  }

  // Marquer une alerte comme lue
  markAlertAsRead(alertId) {
    const alerts = this.getSystemAlerts();
    const alert = alerts.find(a => String(a.id) === String(alertId));
    if (alert) {
      alert.read = true;
      this.saveSystemAlerts(alerts);
      this.updateAlertesBadge();
      window.dispatchEvent(new CustomEvent('dataUpdated', { detail: { section: 'alertes' } }));
    }
  }

  // Supprimer une alerte
  deleteAlert(alertId) {
    const alerts = this.getSystemAlerts().filter(a => String(a.id) !== String(alertId));
    this.saveSystemAlerts(alerts);
    this.updateAlertesBadge();
    window.dispatchEvent(new CustomEvent('dataUpdated', { detail: { section: 'alertes' } }));
    console.log('[ALERTMANAGER] Alerte supprimée:', alertId);
  }

  // Mettre à jour le badge des alertes
  updateAlertesBadge() {
    const alerts = this.getSystemAlerts();
    const unreadCount = alerts.filter(a => !a.read).length;
    const badgeAlertes = document.getElementById('badgeAlertes');
    if (badgeAlertes) {
      badgeAlertes.textContent = unreadCount;
      badgeAlertes.style.display = unreadCount > 0 ? 'inline-block' : 'none';
    }
  }

  // Vérifier les stagiaires sans rapport aujourd'hui
  checkStagiairesWithoutReports() {
    const today = new Date().toLocaleDateString('fr-FR');
    const stagiaires = JSON.parse(localStorage.getItem('stagiaires') || '[]');
    const rapportsData = JSON.parse(localStorage.getItem('rapports') || '{"list":[],"finaux":[]}');
    const rapportsAujourdhui = rapportsData.list || [];
    
    // Vérifier si une alerte pour les rapports existe déjà aujourd'hui
    const existingReportAlert = this.getSystemAlerts().find(a => 
      a.category === 'rapports' && 
      a.date && new Date(a.date).toLocaleDateString('fr-FR') === today
    );
    
    if (existingReportAlert) {
      console.log('[ALERTMANAGER] Alerte rapports existe déjà pour aujourd\'hui, ignorée');
      return [];
    }
    
    const stagiairesSansRapport = stagiaires.filter(s => {
      const rapportExiste = rapportsAujourdhui.some(r => 
        r.nom === `${s.prenom} ${s.nom}` || r.nom === s.nom || r.stagiaire === s.nom
      );
      return !rapportExiste;
    });

    if (stagiairesSansRapport.length > 0) {
      this.addSystemAlert({
        type: 'critique',
        category: 'rapports',
        message: `${stagiairesSansRapport.length} stagiaire(s) sans rapport`,
        details: `Les stagiaires suivants n'ont pas déposé leur rapport du ${today}: ${stagiairesSansRapport.map(s => `${s.prenom} ${s.nom}`).join(', ')}`,
        stagiaires: stagiairesSansRapport,
        date: new Date().toISOString(),
        read: false
      });
    }

    return stagiairesSansRapport;
  }

  // Vérifier les nouveaux stagiaires
  checkNewStagiaires() {
    const newStagiaires = JSON.parse(localStorage.getItem('new_stagiaires') || '[]');
    
    if (newStagiaires.length === 0) {
      return;
    }
    
    console.log('[ALERTMANAGER] Traitement des nouveaux stagiaires:', newStagiaires.length);
    
    // Générer une seule alerte pour tous les nouveaux stagiaires
    const stagiairesNoms = newStagiaires.map(s => `${s.prenom} ${s.nom}`).join(', ');
    const stagiairesDetails = newStagiaires.map(s => {
      const department = s.departement || s.formation || 'Non spécifié';
      return `- ${s.prenom} ${s.nom} (Département: ${department})`;
    }).join('\n');
    
    const message = newStagiaires.length === 1 
      ? `Nouveau stagiaire: ${stagiairesNoms}`
      : `${newStagiaires.length} nouveaux stagiaires ajoutés`;
    
    const details = newStagiaires.length === 1
      ? `Le stagiaire ${stagiairesNoms} a été ajouté à la plateforme.`
      : `Les stagiaires suivants ont été ajoutés à la plateforme:\n${stagiairesDetails}`;
    
    this.addSystemAlert({
      type: 'info',
      category: 'nouveau',
      message: message,
      details: details,
      stagiaires: newStagiaires,
      nom: stagiairesNoms,
      date: new Date().toISOString(),
      read: false
    });
    
    console.log('[ALERTMANAGER] Alerte générée pour', newStagiaires.length, 'stagiaire(s)');
    
    // Vider la liste après traitement
    localStorage.setItem('new_stagiaires', JSON.stringify([]));
    
    console.log('[ALERTMANAGER] new_stagiaires vidé après traitement');
  }

  // Générer toutes les alertes quotidiennes
  generateDailyAlerts() {
    this.checkStagiairesWithoutReports();
    // checkNewStagiaires est appelé immédiatement lors de l'ajout, pas besoin de l'appeler ici
    this.checkDailyAbsences();
  }

  // Vérifier les absences du jour
  checkDailyAbsences() {
    const today = new Date().toLocaleDateString('fr-FR');
    const absences = this.getAbsences().filter(a => a.date === today && a.type === 'non_justifiee');
    
    absences.forEach(absence => {
      // Vérifier si une alerte existe déjà pour cette absence
      const existingAlert = this.getSystemAlerts().find(a => 
        a.category === 'absence_jour' && a.stagiaireId === absence.stagiaireId && a.date === today
      );
      
      if (!existingAlert) {
        this.addSystemAlert({
          type: 'avertissement',
          category: 'absence_jour',
          stagiaireId: absence.stagiaireId,
          nom: absence.nom,
          date: today,
          message: `Absence non justifiée: ${absence.nom}`,
          details: `${absence.nom} est absent aujourd'hui (${today}) sans justification. Voulez-vous déposer une justification ?`,
          requiresJustification: true,
          read: false
        });
      }
    });
  }
}

// ===== FONCTIONS D'ALERTES AUTOMATIQUES =====

// Vérifier absences et retards depuis l'API - CORRIGÉ pour éviter faux positifs
async function checkAbsencesRetards() {
  try {
    const BACKEND_URL = window.BACKEND_URL || 'http://127.0.0.1:8000';

    // ✅ Vérifier d'abord si le backend est accessible
    try {
      const ping = await fetch(`${BACKEND_URL}/api/auth/stagiaires/`, { signal: AbortSignal.timeout(2000) });
      if (!ping.ok) return; // backend répond mais erreur → on sort
    } catch (e) {
      console.log('[ABSENCE CHECK] Backend inaccessible, vérification ignorée.');
      return; // ← ici on sort proprement sans bloquer
    }

    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    const HEURE_LIMITE = 9 * 60 + 30; // 09h30

    // Ne vérifier qu'après 09h30
    if (currentMinutes < HEURE_LIMITE) return;

    // 1. Récupérer tous les stagiaires
    const stagResponse = await fetch(`${BACKEND_URL}/api/auth/stagiaires/`);
    const stagData = await stagResponse.json();
    if (!stagData.success) return;

    // 2. Récupérer les pointages du jour
    const today = new Date().toISOString().split('T')[0];
    const ptgResponse = await fetch(`${BACKEND_URL}/api/presences/pointages/`);
    const ptgData = await ptgResponse.json();
    if (!ptgData.success) return;

    // 3. Filtrer les pointages d'aujourd'hui
    const todayPointages = ptgData.pointages.filter(p => {
      return p.date && p.date.split('T')[0] === today;
    });

    // 4. Créer un Set des noms présents aujourd'hui
    const presentsToday = new Set();
    todayPointages.forEach(p => {
      const key = `${p.nom.toLowerCase()}_${p.prenom.toLowerCase()}`;
      presentsToday.add(key);
      // Aussi par email si disponible
      if (p.email) presentsToday.add(p.email.toLowerCase());
    });

    // ✅ AJOUT — Lire aussi depuis localStorage (pointageLogs sauvé par pointage_qr.html)
    const pointageLogsLocal = JSON.parse(localStorage.getItem('pointageLogs') || '[]');
    const nomsPointesLocal = new Set(
      pointageLogsLocal.map(l =>
        `${(l.nom || '').toLowerCase()}_${(l.prenom || '').toLowerCase()}`
      )
    );

    // 5. Identifier les absents
    const existingAlerts = alertManager.getSystemAlerts();

    stagData.stagiaires.forEach(s => {
      const key = `${s.last_name.toLowerCase()}_${s.first_name.toLowerCase()}`;
      const keyEmail = s.email.toLowerCase();

      // ✅ Présent si backend OU localStorage
      const isPresent = presentsToday.has(key) || presentsToday.has(keyEmail) || nomsPointesLocal.has(key);

      if (!isPresent) {
        const fullName = `${s.first_name} ${s.last_name}`;

        // Vérifier si une alerte d'absence existe déjà pour aujourd'hui
        const alreadyAlerted = existingAlerts.some(a =>
          a.category === 'absence' &&
          a.stagiaireId === s.id &&
          a.date && new Date(a.date).toDateString() === new Date().toDateString()
        );

        if (!alreadyAlerted) {
          alertManager.addSystemAlert({
            type: 'critique',
            category: 'absence',
            nom: fullName,
            stagiaireId: s.id,
            message: `Absence détectée: ${fullName}`,
            details: `Aucun pointage enregistré aujourd'hui après 09h30`,
            date: new Date().toISOString(),
            read: false,
            requiresJustification: true
          });
        }
      }
    });
  } catch(e) {
    console.log('[ABSENCE CHECK] Erreur ignorée:', e.message);
    // Ne pas laisser l'erreur remonter
  }
}

// ✅ Purger les alertes "absence" category si le stagiaire a pointé aujourd'hui
function purgeAbsenceAlertsIfPointed() {
  const logs = JSON.parse(localStorage.getItem('pointageLogs') || '[]');
  if (logs.length === 0) return;

  const pointedKeys = new Set(
    logs.map(l => `${(l.nom||'').toLowerCase()}_${(l.prenom||'').toLowerCase()}`)
  );

  const alerts = alertManager.getSystemAlerts();
  let changed = false;

  alerts.forEach(a => {
    if (a.category !== 'absence' || !a.requiresJustification) return;

    const nameParts = (a.nom || '').toLowerCase().split(' ');
    // Essayer les deux ordres (Prénom Nom ou Nom Prénom)
    const key1 = `${nameParts.slice(1).join(' ')}_${nameParts[0]}`;
    const key2 = `${nameParts[0]}_${nameParts.slice(1).join(' ')}`;

    if (pointedKeys.has(key1) || pointedKeys.has(key2)) {
      console.log(`[PURGE] Alerte absence supprimée car ${a.nom} a pointé`);
      alertManager.deleteAlert(a.id);
      changed = true;
    }
  });

  if (changed) alertManager.updateAlertesBadge();
}

// Alerte nouveau stagiaire — appelez-la depuis saveStagiaire() après création
function alertNouveauStagiaire(prenom, nom, ecole) {
  alertManager.addSystemAlert({
    type: 'info',
    category: 'nouveau',
    message: `Nouveau stagiaire ajouté : ${prenom} ${nom}`,
    details: `École : ${ecole}`,
    nom: `${prenom} ${nom}`,
    date: new Date().toISOString(),
    read: false
  });
}

// Alerte dépôt de rapport — appelez-la depuis submitReport()
function alertRapportDepose(prenom, nom, typeRapport) {
  alertManager.addSystemAlert({
    type: 'info',
    category: 'rapport',
    message: `Rapport ${typeRapport} déposé par ${prenom} ${nom}`,
    details: `Déposé le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR', {hour:'2-digit',minute:'2-digit'})}`,
    nom: `${prenom} ${nom}`,
    date: new Date().toISOString(),
    read: false
  });
}

// Alerte rapport manquant — vérifier chaque soir après 17h00
async function checkRapportsManquants() {
  // Ne vérifier qu'après 17h00
  const now = new Date();
  if (now.getHours() < 17) return;

  const today = new Date().toLocaleDateString('fr-FR');
  const rapports = JSON.parse(localStorage.getItem('rapports') || '{"list":[]}');
  const stagiaires = JSON.parse(localStorage.getItem('stagiaires') || '[]');
  const rapportsAujourdhui = (rapports.list || []).filter(r => r.date === today);
  const deposants = new Set(rapportsAujourdhui.map(r => r.stagiaire));

  stagiaires.forEach(s => {
    const fullName = `${s.prenom} ${s.nom}`;
    if (!deposants.has(fullName)) {
      const existingAlerts = alertManager.getSystemAlerts();
      const alreadyExists = existingAlerts.some(a =>
        a.category === 'rapport_manquant' && a.nom === fullName &&
        a.date.startsWith(new Date().toISOString().split('T')[0])
      );
      if (!alreadyExists) {
        alertManager.addSystemAlert({
          type: 'avertissement',
          category: 'rapport_manquant',
          message: `Rapport journalier manquant : ${fullName}`,
          details: `Aucun rapport déposé pour le ${today}`,
          nom: fullName,
          date: new Date().toISOString(),
          read: false
        });
      }
    }
  });
}

// Alerte fin de stage — vérifier chaque jour
function checkFinStages() {
  const stagiaires = JSON.parse(localStorage.getItem('stagiaires') || '[]');
  const today = new Date();

  stagiaires.forEach(s => {
    if (!s.fin || s.fin === '-') return;

    // Convertir date FR (dd/mm/yyyy) en Date
    const parts = s.fin.split('/');
    if (parts.length !== 3) return;
    const finDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
    const diffDays = Math.ceil((finDate - today) / (1000*60*60*24));
    const fullName = `${s.prenom} ${s.nom}`;
    const existingAlerts = alertManager.getSystemAlerts();

    // Alerte 7 jours avant la fin
    if (diffDays === 7) {
      const alreadyExists = existingAlerts.some(a =>
        a.category === 'fin_stage_proche' && a.nom === fullName
      );
      if (!alreadyExists) {
        alertManager.addSystemAlert({
          type: 'avertissement',
          category: 'fin_stage_proche',
          message: `Fin de stage dans 7 jours : ${fullName}`,
          details: `Date de fin : ${s.fin}`,
          nom: fullName,
          date: new Date().toISOString(),
          read: false
        });
      }
    }

    // Alerte le jour de la fin
    if (diffDays === 0) {
      const alreadyExists = existingAlerts.some(a =>
        a.category === 'fin_stage_aujourd_hui' && a.nom === fullName &&
        a.date.startsWith(new Date().toISOString().split('T')[0])
      );
      if (!alreadyExists) {
        alertManager.addSystemAlert({
          type: 'critique',
          category: 'fin_stage_aujourd_hui',
          message: `Fin de stage aujourd'hui : ${fullName}`,
          details: `Le stage de ${fullName} se termine aujourd'hui`,
          nom: fullName,
          date: new Date().toISOString(),
          read: false
        });
      }
    }
  });
}

// Alerte retard dans projet
function checkRetardsProjets() {
  const data = JSON.parse(localStorage.getItem('orchidData') || '{"projets":{"list":[]}}');
  const projets = data.projets?.list || [];

  projets.forEach(p => {
    if (p.etat !== 'retard') return;
    const existingAlerts = alertManager.getSystemAlerts();
    const alreadyExists = existingAlerts.some(a =>
      a.category === 'projet_retard' && a.message.includes(p.nom) && !a.read
    );
    if (!alreadyExists) {
      alertManager.addSystemAlert({
        type: 'avertissement',
        category: 'projet_retard',
        message: `Projet en retard : ${p.nom}`,
        details: `Responsable : ${p.resp} — Date limite : ${p.fin}`,
        nom: p.resp || 'N/A',
        date: new Date().toISOString(),
        read: false
      });
    }
  });
}

// Lancer toutes les vérifications au chargement et périodiquement
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    purgeAbsenceAlertsIfPointed(); // ✅ Purger alertes absence si pointage existe
    checkAbsencesRetards();   // absences + retards + 3 absences
    checkFinStages();          // fin de stage
    checkRetardsProjets();     // projets en retard
    checkRapportsManquants();  // rapports manquants (si après 17h)
  }, 3000);

  // Re-vérifier toutes les 10 minutes
  setInterval(() => {
    checkAbsencesRetards();
    checkFinStages();
    checkRetardsProjets();
    checkRapportsManquants(); // ← ajouter cette ligne
  }, 10 * 60 * 1000);
});

// Instance globale de l'alert manager
const alertManager = new AlertManager();
window.alertManager = alertManager; // Rendre accessible globalement

// Fonction pour démarrer la vérification quotidienne des alertes
function startDailyAlertCheck() {
  // Vérifier immédiatement
  alertManager.generateDailyAlerts();
  
  // Vérifier toutes les heures
  setInterval(() => {
    alertManager.generateDailyAlerts();
  }, 60 * 60 * 1000); // Toutes les heures
}

// Initialisation commune
document.addEventListener('DOMContentLoaded', function() {
  const user = checkAuth();
  if (user) {
    displayUserInfo(user);
  }
  
  // Activer le menu item correspondant à la page actuelle
  const currentPage = window.location.pathname.split('/').pop();
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(currentPage)) {
      item.classList.add('active');
    }
  });
  
  // NE PAS appeler startDailyAlertCheck pour éviter les doublons
  // Les alertes sont générées en temps réel lors des actions
  // startDailyAlertCheck();
  
  // Nettoyer les alertes en double au chargement (une seule fois)
  const alerts = JSON.parse(localStorage.getItem('system_alerts') || '[]');
  const uniqueAlerts = [];
  const seen = new Set();
  
  alerts.forEach(alert => {
    const key = `${alert.category}-${alert.message}-${alert.nom}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueAlerts.push(alert);
    }
  });
  
  if (uniqueAlerts.length !== alerts.length) {
    console.log('[COMMON] Nettoyage des alertes en double:', alerts.length, '->', uniqueAlerts.length);
    localStorage.setItem('system_alerts', JSON.stringify(uniqueAlerts));
  }
  
  // Mettre à jour les badges de navigation
  updateNavBadges();
  
  // Mettre à jour le badge des alertes
  if (typeof alertManager !== 'undefined') {
    alertManager.updateAlertesBadge();
  }
  
  // Démarrer la vérification quotidienne des alertes
  if (typeof startDailyAlertCheck !== 'undefined') {
    startDailyAlertCheck();
  }
});

// Fonctions d'authentification pour les requêtes API
function getToken() {
  return localStorage.getItem('access_token');
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  };
}

// ===== API HELPER FOR RAILWAY =====
async function fetchWithAuth(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const BACKEND = window.BACKEND_URL || 'https://orchid-island-production.up.railway.app';
  
  const response = await fetch(`${BACKEND}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...(options.headers || {})
    }
  });
  
  if (response.status === 401) {
    localStorage.clear();
    window.location.href = 'authentification.html';
    return null;
  }
  return response;
}
