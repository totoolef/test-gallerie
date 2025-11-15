# ✅ CHECKLIST COMPLÈTE - AVANT DÉPLOIEMENT

## 🚨 PROBLÈME ACTUEL
- ❌ **Image trop grande : 9.0 GB** (limite Railway : 4.0 GB)
- ✅ **Corrections appliquées** : Optimisation du build, nettoyage des caches

---

## 📋 VÉRIFICATIONS À FAIRE AVANT DE REDÉPLOYER

### 1. ✅ CODE ET CONFIGURATION

#### 1.1 Fichiers modifiés à commiter
- [ ] `database.py` (correction BYTEA au lieu de VECTOR)
- [ ] `api_server_cloud.py` (amélioration health())
- [ ] `nixpacks.toml` (optimisation nettoyage)
- [ ] `.railwayignore` (exclusion fichiers inutiles)
- [ ] `GUIDE_DEPLOIEMENT_FINAL.md` (nouveau)
- [ ] `CHECKLIST_AVANT_DEPLOIEMENT.md` (ce fichier)

**Commande à exécuter :**
```bash
git status
git add database.py api_server_cloud.py nixpacks.toml .railwayignore GUIDE_DEPLOIEMENT_FINAL.md CHECKLIST_AVANT_DEPLOIEMENT.md
git commit -m "Fix: Optimisation taille image + correction PostgreSQL"
git push origin main
```

#### 1.2 Fichiers à VÉRIFIER qu'ils ne sont PAS dans le repo
- [ ] `venv/` et `venv311/` (doivent être dans .gitignore)
- [ ] `index.faiss` (doit être dans .gitignore)
- [ ] `metadata.json` (doit être dans .gitignore)
- [ ] `node_modules/` (doit être dans .gitignore)
- [ ] `__pycache__/` (doit être dans .gitignore)

**Vérification :**
```bash
# Vérifier que ces fichiers ne sont pas trackés
git ls-files | grep -E "(venv|index.faiss|metadata.json|node_modules|__pycache__)"
# Ne devrait rien retourner
```

#### 1.3 Fichiers de configuration Railway
- [ ] `nixpacks.toml` existe et est correct
- [ ] `railway.json` existe et est correct
- [ ] `Procfile` existe et est correct
- [ ] `runtime.txt` existe et contient `python-3.11`
- [ ] `.railwayignore` existe et exclut tout le frontend
- [ ] `.nixpacksignore` existe

---

### 2. ✅ RAILWAY - CONFIGURATION

#### 2.1 Service "test-gallerie"
- [ ] Service existe dans Railway
- [ ] Repo GitHub est bien lié
- [ ] Branch configurée : `main` (ou `master`)

#### 2.2 Variables d'environnement
Dans Railway → Service "test-gallerie" → Onglet "Variables", vérifier :

**OBLIGATOIRES :**
- [ ] `PORT=5000` (ou laisser Railway le gérer automatiquement)
- [ ] `FLASK_ENV=production`
- [ ] `STORAGE_TYPE=local`
- [ ] `CORS_ORIGINS=http://localhost:3000,*`
- [ ] `DATABASE_URL` (créée automatiquement par PostgreSQL)

**Comment vérifier :**
1. Railway → Projet "medIA" → Service "test-gallerie"
2. Onglet "Variables"
3. Vérifier chaque variable ci-dessus

#### 2.3 PostgreSQL
- [ ] Service PostgreSQL existe dans le projet
- [ ] PostgreSQL est connecté au service "test-gallerie"
- [ ] Variable `DATABASE_URL` est automatiquement disponible

**Comment vérifier :**
1. Railway → Projet "medIA"
2. Vérifier qu'il y a un service "Postgres" ou "PostgreSQL"
3. Vérifier que la variable `DATABASE_URL` apparaît dans "test-gallerie" → Variables

---

### 3. ✅ OPTIMISATIONS APPLIQUÉES

#### 3.1 Nettoyage dans nixpacks.toml
- [ ] `pip cache purge` pour nettoyer les caches
- [ ] Suppression des `__pycache__` et `.pyc`
- [ ] Nettoyage des fichiers temporaires

#### 3.2 Exclusion de fichiers
- [ ] `.railwayignore` exclut : venv, node_modules, index.faiss, metadata.json
- [ ] `.railwayignore` exclut : fichiers de test, app_ios.py, app_simple.py
- [ ] `.railwayignore` exclut : tous les fichiers frontend (src/, public/, etc.)

---

### 4. ✅ GITHUB - ÉTAT DU REPO

#### 4.1 Vérifier que le code est à jour
```bash
# Vérifier l'état
git status

# Vérifier les derniers commits
git log --oneline -5
```

#### 4.2 Vérifier que les fichiers lourds ne sont pas trackés
```bash
# Vérifier la taille des fichiers trackés
git ls-files | xargs ls -lh | sort -k5 -hr | head -20
```

**Fichiers à surveiller :**
- Aucun fichier > 10 MB ne devrait être tracké
- `index.faiss` ne devrait PAS être tracké
- `metadata.json` ne devrait PAS être tracké
- `venv/` ne devrait PAS être tracké

---

### 5. ✅ TESTS LOCAUX (Optionnel mais recommandé)

#### 5.1 Tester que l'API démarre localement
```bash
# Activer l'environnement virtuel
source venv/bin/activate  # ou venv311/bin/activate

# Tester avec les variables d'environnement
export PORT=5000
export FLASK_ENV=production
export STORAGE_TYPE=local
export DATABASE_URL="postgresql://..."  # Si vous avez PostgreSQL local

# Démarrer l'API
python api_server_cloud.py
```

**Vérifier :**
- [ ] L'API démarre sans erreur
- [ ] `/api/health` retourne `{"status": "ok"}`

---

### 6. ✅ PRÊT POUR DÉPLOIEMENT

Une fois toutes les cases cochées :

1. **Commit et push final :**
   ```bash
   git add .
   git commit -m "Fix: Optimisation taille image Railway"
   git push origin main
   ```

2. **Dans Railway :**
   - Le déploiement devrait se déclencher automatiquement
   - OU cliquez sur "Redeploy" dans l'onglet "Deployments"

3. **Surveiller les logs :**
   - Build Logs : Vérifier que l'installation se passe bien
   - Deploy Logs : Vérifier que l'API démarre
   - **IMPORTANT** : Vérifier la taille de l'image dans les logs

4. **Si l'image est toujours > 4 GB :**
   - Voir section "Solutions alternatives" ci-dessous

---

## 🚨 SI L'IMAGE EST ENCORE TROP GRANDE (> 4 GB)

### Solution 1 : Utiliser torch CPU-only (plus léger)
Modifier `requirements.txt` :
```txt
# Remplacer torch>=2.0.0 par :
--index-url https://download.pytorch.org/whl/cpu
torch>=2.0.0
```

### Solution 2 : Supprimer des dépendances non essentielles
Vérifier si ces dépendances sont vraiment nécessaires :
- `streamlit` (utilisé seulement pour app_ios.py, pas pour api_server_cloud.py)
- `matplotlib` (peut-être pas nécessaire pour l'API)

### Solution 3 : Utiliser une image Docker personnalisée
Créer un `Dockerfile` optimisé au lieu d'utiliser Nixpacks.

### Solution 4 : Upgrader le plan Railway
Railway propose des plans payants avec des limites plus élevées.

---

## 📊 RÉSULTATS ATTENDUS

### Build réussi
- ✅ "Successfully Built!" dans les Build Logs
- ✅ Taille de l'image < 4.0 GB
- ✅ Temps de build : 10-15 minutes

### Déploiement réussi
- ✅ "🚀 Démarrage de l'API Flask (version cloud)..." dans Deploy Logs
- ✅ "📡 API disponible sur http://0.0.0.0:5000"
- ✅ "💾 Stockage: local"
- ✅ "🗄️  Base de données: PostgreSQL"
- ✅ Statut "Active" (vert) dans Railway

### Test API
- ✅ `curl https://votre-service.railway.app/api/health` retourne `{"status": "ok"}`

---

## 📝 NOTES IMPORTANTES

1. **Taille de l'image** : Les dépendances ML (torch, transformers) sont très lourdes. Même avec optimisations, l'image peut être proche de 4 GB.

2. **Premier déploiement** : Peut prendre 15-20 minutes à cause du téléchargement des dépendances.

3. **Déploiements suivants** : Plus rapides grâce au cache Railway.

4. **Surveillance** : Surveillez les logs en temps réel pendant le premier déploiement.

---

## ✅ CHECKLIST FINALE

Avant de cliquer sur "Deploy" ou de faire `git push` :

- [ ] Tous les fichiers sont commités et poussés
- [ ] Variables d'environnement vérifiées dans Railway
- [ ] PostgreSQL connecté
- [ ] `.railwayignore` à jour
- [ ] `nixpacks.toml` optimisé
- [ ] Fichiers lourds exclus du repo
- [ ] Prêt mentalement à attendre 15-20 minutes pour le build

**Une fois tout vérifié, vous pouvez déployer ! 🚀**

