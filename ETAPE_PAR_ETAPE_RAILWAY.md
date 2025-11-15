# 🚂 Guide Étape par Étape : Déployer sur Railway

## Étape 1 : Créer un Service dans Railway

### Option A : Via l'Interface Web (Recommandé)

1. **Allez sur https://railway.app**
2. **Connectez-vous** avec votre compte
3. **Cliquez sur votre projet "medIA"**
4. **Cliquez sur "New"** (en haut à droite)
5. **Sélectionnez "GitHub Repo"** ou **"Empty Service"**
   - Si vous choisissez GitHub Repo : sélectionnez votre repo
   - Si vous choisissez Empty Service : vous devrez pousser le code manuellement

### Option B : Via la CLI

```bash
# Créer un nouveau service depuis le repo GitHub
railway service

# Ou créer un service vide
railway service --new
```

## Étape 2 : Ajouter PostgreSQL

1. **Dans votre projet Railway**, cliquez sur **"New"**
2. **Sélectionnez "Database"**
3. **Choisissez "PostgreSQL"**
4. Railway créera automatiquement :
   - Une base de données PostgreSQL
   - La variable d'environnement `DATABASE_URL`

## Étape 3 : Configurer les Variables d'Environnement

### Via l'Interface Web (Plus Simple)

1. **Dans votre projet**, cliquez sur votre **service** (celui que vous venez de créer)
2. Cliquez sur l'onglet **"Variables"** (ou **"Settings"** → **"Variables"**)
3. **Ajoutez les variables suivantes** une par une :

#### Variable 1 : PORT
- Cliquez sur **"New Variable"**
- **Name** : `PORT`
- **Value** : `5000`
- Cliquez sur **"Add"**

#### Variable 2 : FLASK_ENV
- Cliquez sur **"New Variable"**
- **Name** : `FLASK_ENV`
- **Value** : `production`
- Cliquez sur **"Add"**

#### Variable 3 : STORAGE_TYPE
- Cliquez sur **"New Variable"**
- **Name** : `STORAGE_TYPE`
- **Value** : `local`
- Cliquez sur **"Add"**

#### Variable 4 : CORS_ORIGINS
- Cliquez sur **"New Variable"**
- **Name** : `CORS_ORIGINS`
- **Value** : `http://localhost:3000,*`
- Cliquez sur **"Add"**

#### Variable 5 : DATABASE_URL
- **Cette variable est créée automatiquement** quand vous ajoutez PostgreSQL
- **Ne la modifiez pas !**
- Si vous ne la voyez pas, c'est que PostgreSQL n'a pas été ajouté (retournez à l'Étape 2)

### Via la CLI

```bash
# Lier le service (si pas déjà fait)
railway service

# Ajouter les variables
railway variables set PORT=5000
railway variables set FLASK_ENV=production
railway variables set STORAGE_TYPE=local
railway variables set CORS_ORIGINS="http://localhost:3000,*"

# Vérifier les variables
railway variables
```

## Étape 4 : Configurer le Fichier de Démarrage

Railway doit savoir quel fichier exécuter. Vérifiez que vous avez :

1. **`Procfile`** (déjà créé) :
   ```
   web: python api_server_cloud.py
   ```

2. **`railway.json`** (déjà créé) :
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "python api_server_cloud.py",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

## Étape 5 : Déployer

### Via l'Interface Web

1. **Dans votre service**, Railway détectera automatiquement votre code
2. Il commencera à **build** et **deploy** automatiquement
3. Vous verrez les logs en temps réel

### Via la CLI

```bash
# Déployer
railway up

# Voir les logs
railway logs
```

## Étape 6 : Obtenir l'URL de l'API

### Via l'Interface Web

1. **Dans votre service**, cliquez sur **"Settings"**
2. Cliquez sur **"Generate Domain"** (si pas déjà fait)
3. Vous verrez l'URL : `https://votre-service.railway.app`

### Via la CLI

```bash
# Générer un domaine
railway domain

# Voir l'URL
railway status
```

## ✅ Vérification

Pour vérifier que tout fonctionne :

1. **Vérifiez les logs** :
   ```bash
   railway logs
   ```
   Vous devriez voir : `🚀 Démarrage de l'API Flask (version cloud)...`

2. **Testez l'API** :
   ```bash
   curl https://votre-service.railway.app/api/health
   ```
   Vous devriez recevoir : `{"status":"ok",...}`

## 🐛 Problèmes Courants

### Le service ne démarre pas

- Vérifiez les logs : `railway logs`
- Vérifiez que `api_server_cloud.py` existe
- Vérifiez que toutes les variables d'environnement sont configurées

### DATABASE_URL n'existe pas

- Vous devez d'abord ajouter PostgreSQL (Étape 2)
- Railway créera automatiquement cette variable

### L'API ne répond pas

- Vérifiez que le domaine est généré : `railway domain`
- Vérifiez les logs pour les erreurs
- Vérifiez que CORS_ORIGINS est bien configuré


