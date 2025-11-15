# 🚀 Guide de Déploiement Final - Étape par Étape

## ✅ Corrections Apportées

1. ✅ **Correction du problème PostgreSQL** : Remplacement de `VECTOR(768)` par `BYTEA` dans `database.py` (l'extension pgvector n'est pas disponible sur Railway par défaut)
2. ✅ **Amélioration de la fonction health()** : Gestion d'erreurs améliorée

## 📋 Étape 1 : Vérifier que le code est à jour

Assurez-vous que tous les changements sont commités et poussés sur GitHub :

```bash
# Vérifier l'état
git status

# Ajouter les fichiers modifiés
git add database.py api_server_cloud.py

# Commit
git commit -m "Fix: Correction du problème PostgreSQL (BYTEA au lieu de VECTOR)"

# Pousser sur GitHub
git push origin main
```

## 📋 Étape 2 : Vérifier la Configuration Railway

### 2.1 Ouvrir Railway

1. Allez sur https://railway.app
2. Connectez-vous à votre compte
3. Ouvrez le projet **"medIA"**

### 2.2 Vérifier le Service "test-gallerie"

1. Cliquez sur le service **"test-gallerie"**
2. Vérifiez que le repo GitHub est bien lié :
   - Onglet **"Settings"** → Section **"Source"**
   - Le repo GitHub devrait être visible

### 2.3 Vérifier les Variables d'Environnement

Dans l'onglet **"Variables"** du service "test-gallerie", vérifiez que ces variables existent :

**Variables OBLIGATOIRES :**
- ✅ `PORT=5000` (Railway définit automatiquement cette variable, mais vous pouvez la définir manuellement)
- ✅ `FLASK_ENV=production`
- ✅ `STORAGE_TYPE=local`
- ✅ `CORS_ORIGINS=http://localhost:3000,*` (vous pourrez mettre à jour avec l'URL Vercel plus tard)
- ✅ `DATABASE_URL` (créée automatiquement par PostgreSQL, vérifiez qu'elle existe)

**Comment ajouter/modifier une variable :**
1. Onglet **"Variables"**
2. Cliquez sur **"New Variable"**
3. Entrez le nom et la valeur
4. Cliquez sur **"Add"**

### 2.4 Vérifier que PostgreSQL est connecté

1. Dans votre projet Railway, vérifiez qu'il y a un service **PostgreSQL**
2. Si ce n'est pas le cas :
   - Cliquez sur **"New"** → **"Database"** → **"PostgreSQL"**
   - Railway créera automatiquement la variable `DATABASE_URL` dans votre service

3. **Important** : Vérifiez que le service PostgreSQL est bien connecté au service "test-gallerie" :
   - Le service PostgreSQL devrait apparaître dans l'architecture
   - La variable `DATABASE_URL` devrait être automatiquement disponible dans "test-gallerie"

## 📋 Étape 3 : Redéployer le Service

### Option A : Via l'Interface Web (Recommandé)

1. Dans le service "test-gallerie", allez dans l'onglet **"Deployments"**
2. Cliquez sur **"Redeploy"** ou **"Deploy"** (bouton en haut à droite)
3. Railway va :
   - Récupérer le dernier code depuis GitHub
   - Builder l'image
   - Déployer le service

### Option B : Via Git Push

Si le repo est bien lié, un simple push déclenchera un nouveau déploiement :

```bash
git push origin main
```

## 📋 Étape 4 : Vérifier les Logs de Déploiement

1. Dans l'onglet **"Deployments"**, cliquez sur le dernier déploiement
2. Vérifiez l'onglet **"Build Logs"** :
   - ✅ Le build devrait se terminer avec "Successfully Built!"
   
3. Vérifiez l'onglet **"Deploy Logs"** :
   - ✅ Vous devriez voir : "🚀 Démarrage de l'API Flask (version cloud)..."
   - ✅ Vous devriez voir : "📡 API disponible sur http://0.0.0.0:5000"
   - ✅ Vous devriez voir : "💾 Stockage: local"
   - ✅ Vous devriez voir : "🗄️  Base de données: PostgreSQL"

**Si vous voyez des erreurs :**
- Notez le message d'erreur exact
- Vérifiez les sections de dépannage ci-dessous

## 📋 Étape 5 : Obtenir l'URL de l'API

1. Dans le service "test-gallerie", allez dans l'onglet **"Settings"**
2. Section **"Networking"** ou **"Domains"**
3. Si aucun domaine n'existe :
   - Cliquez sur **"Generate Domain"**
   - Railway générera une URL comme : `https://test-gallerie-production-xxxx.up.railway.app`
4. **Copiez cette URL** - vous en aurez besoin pour le frontend

## 📋 Étape 6 : Tester l'API

### Test 1 : Endpoint de santé

```bash
# Remplacez par votre URL Railway
curl https://votre-service.railway.app/api/health
```

**Réponse attendue :**
```json
{
  "status": "ok",
  "index_loaded": false,
  "media_count": 0,
  "storage_type": "local"
}
```

### Test 2 : Vérifier que l'API répond

Ouvrez dans votre navigateur :
```
https://votre-service.railway.app/api/health
```

Vous devriez voir la réponse JSON ci-dessus.

## 📋 Étape 7 : Déployer le Frontend sur Vercel

Une fois que l'API fonctionne :

1. **Aller sur Vercel** : https://vercel.com
2. **Importer le projet** depuis GitHub
3. **Configurer les variables d'environnement** :
   - `VITE_API_URL=https://votre-service.railway.app/api`
4. **Déployer**

5. **Mettre à jour CORS dans Railway** :
   - Retournez dans Railway → Service "test-gallerie" → Variables
   - Modifiez `CORS_ORIGINS` pour inclure l'URL Vercel :
     ```
     http://localhost:3000,https://votre-app.vercel.app
     ```

## 🐛 Dépannage

### Problème 1 : Le build échoue

**Erreur : "No module named 'database'"**
- ✅ Vérifiez que `database.py` est bien dans le repo GitHub
- ✅ Vérifiez que le fichier n'est pas dans `.railwayignore`

**Erreur : "pip install failed"**
- ✅ Vérifiez que `requirements.txt` existe et contient toutes les dépendances
- ✅ Vérifiez les logs pour voir quelle dépendance pose problème

### Problème 2 : Le déploiement échoue au démarrage

**Erreur : "DATABASE_URL not found"**
- ✅ Vérifiez que PostgreSQL est bien ajouté au projet
- ✅ Vérifiez que la variable `DATABASE_URL` existe dans les variables d'environnement
- ✅ Si elle n'existe pas, ajoutez-la manuellement depuis le service PostgreSQL

**Erreur : "Port already in use"**
- ✅ Railway gère automatiquement le port via la variable `PORT`
- ✅ Vérifiez que `PORT=5000` est défini (ou laissez Railway le gérer automatiquement)

**Erreur : "Table 'embeddings' already exists" ou erreur SQL**
- ✅ C'est normal si la table existe déjà
- ✅ Si l'erreur persiste, vérifiez les logs pour le message exact

### Problème 3 : L'API ne répond pas

**L'URL ne fonctionne pas :**
- ✅ Vérifiez que le domaine est bien généré dans Railway
- ✅ Vérifiez que le service est "Active" (vert) dans l'onglet Deployments
- ✅ Vérifiez les logs pour voir si le serveur démarre correctement

**Erreur 502 Bad Gateway :**
- ✅ Le service ne démarre probablement pas
- ✅ Vérifiez les logs de déploiement pour voir l'erreur exacte

**Erreur CORS :**
- ✅ Vérifiez que `CORS_ORIGINS` contient l'URL de votre frontend
- ✅ Vérifiez que l'URL est correcte (sans slash final)

### Problème 4 : Erreurs de base de données

**Erreur : "relation 'media' does not exist"**
- ✅ La base de données devrait être initialisée automatiquement au premier démarrage
- ✅ Vérifiez les logs pour voir si l'initialisation a réussi
- ✅ Si nécessaire, redéployez le service

**Erreur : "permission denied" ou erreur de connexion**
- ✅ Vérifiez que `DATABASE_URL` est correcte
- ✅ Vérifiez que PostgreSQL est bien connecté au service

## 📝 Checklist Finale

Avant de considérer le déploiement comme terminé :

- [ ] Code poussé sur GitHub
- [ ] Service Railway créé et lié au repo
- [ ] PostgreSQL ajouté et connecté
- [ ] Variables d'environnement configurées
- [ ] Build réussi (pas d'erreurs dans Build Logs)
- [ ] Déploiement réussi (pas d'erreurs dans Deploy Logs)
- [ ] URL générée et accessible
- [ ] `/api/health` retourne `{"status": "ok"}`
- [ ] Frontend déployé sur Vercel (optionnel)
- [ ] CORS configuré avec l'URL Vercel (si frontend déployé)

## 🎉 C'est Terminé !

Si toutes les étapes sont complétées et que l'API répond correctement, votre backend est déployé et fonctionnel !

**Prochaines étapes :**
1. Tester l'upload de médias via l'API
2. Déployer le frontend sur Vercel
3. Tester l'application complète

## 📞 Besoin d'aide ?

Si vous rencontrez toujours des problèmes :
1. Copiez le message d'erreur exact des logs Railway
2. Vérifiez que toutes les variables d'environnement sont correctes
3. Vérifiez que le code est bien poussé sur GitHub

