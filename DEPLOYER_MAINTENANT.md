# 🚀 Déployer Maintenant - Instructions Finales

## ✅ Ce qui a été fait automatiquement

1. ✅ Fichiers de configuration mis à jour (`Procfile` et `railway.json`)
2. ✅ Configuration pour utiliser `api_server_cloud.py`

## 📋 Ce que vous devez faire maintenant

### Étape 1 : Créer/Lier un Service dans Railway

**Option A : Via l'Interface Web (Recommandé)**

1. Allez sur https://railway.app
2. Cliquez sur votre projet **medIA**
3. Cliquez sur **"New"** → **"GitHub Repo"**
4. Sélectionnez votre repo GitHub
5. Railway créera automatiquement un service et commencera à déployer

**Option B : Via la CLI**

```bash
railway service
```

Puis suivez les instructions pour créer ou lier un service.

### Étape 2 : Vérifier que PostgreSQL est ajouté

1. Dans votre projet Railway, vérifiez qu'il y a un service **PostgreSQL**
2. Si ce n'est pas le cas, cliquez sur **"New"** → **"Database"** → **"PostgreSQL"**

### Étape 3 : Vérifier les Variables d'Environnement

Dans votre service (pas PostgreSQL), vérifiez que ces variables existent :

- ✅ `PORT=5000`
- ✅ `FLASK_ENV=production`
- ✅ `STORAGE_TYPE=local`
- ✅ `CORS_ORIGINS=http://localhost:3000,*`
- ✅ `DATABASE_URL` (créé automatiquement par PostgreSQL)

### Étape 4 : Déployer

**Via l'Interface Web :**
- Railway déploiera automatiquement quand vous liez le repo GitHub

**Via la CLI :**
```bash
# Lier le service d'abord
railway service

# Pousser le code
git push

# Ou déployer directement
railway up
```

### Étape 5 : Obtenir l'URL de l'API

**Via l'Interface Web :**
1. Dans votre service, allez dans **"Settings"**
2. Cliquez sur **"Generate Domain"**
3. Copiez l'URL (ex: `https://votre-service.railway.app`)

**Via la CLI :**
```bash
railway domain
```

### Étape 6 : Tester l'API

```bash
# Remplacer par votre URL Railway
curl https://votre-service.railway.app/api/health
```

Vous devriez recevoir : `{"status":"ok",...}`

## 🐛 Si ça ne fonctionne pas

### Vérifier les logs

**Via l'Interface Web :**
- Cliquez sur votre service → onglet **"Deployments"** → cliquez sur le dernier déploiement → **"View Logs"**

**Via la CLI :**
```bash
railway logs
```

### Erreurs courantes

1. **"No module named 'database'"**
   - Vérifiez que `database.py` est bien dans le repo
   - Vérifiez que `requirements.txt` contient toutes les dépendances

2. **"DATABASE_URL not found"**
   - Vérifiez que PostgreSQL est bien ajouté
   - Vérifiez que la variable `DATABASE_URL` existe dans les variables d'environnement

3. **"Port already in use"**
   - Vérifiez que `PORT=5000` est bien configuré
   - Railway utilise automatiquement la variable `PORT`

## 📝 Prochaines étapes

Une fois que l'API est déployée et fonctionne :

1. **Notez l'URL de l'API** (ex: `https://votre-service.railway.app`)
2. **Passez à l'étape 3** du README_CLOUD.md pour déployer le frontend sur Vercel
3. **Mettez à jour `CORS_ORIGINS`** dans Railway avec l'URL Vercel


