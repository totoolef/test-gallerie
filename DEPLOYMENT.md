# 🚀 Guide de Déploiement Cloud

Ce guide explique comment déployer l'application pour qu'elle soit accessible partout sur votre téléphone.

## 📋 Options de Déploiement

### Option 1 : Railway (Recommandé - Simple et gratuit)

Railway est excellent pour déployer des applications Python avec des dépendances ML.

#### Étapes :

1. **Créer un compte Railway** : https://railway.app

2. **Installer Railway CLI** :
   ```bash
   npm i -g @railway/cli
   railway login
   ```

3. **Créer les fichiers de configuration** :

   **`railway.json`** :
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "python api_server.py",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

   **`Procfile`** :
   ```
   web: python api_server.py
   ```

   **`runtime.txt`** :
   ```
   python-3.11
   ```

4. **Déployer** :
   ```bash
   railway init
   railway up
   ```

5. **Configurer les variables d'environnement** dans Railway :
   - `FLASK_PORT=5000`
   - `FLASK_ENV=production`

6. **Déployer le frontend** sur Vercel :
   ```bash
   npm install -g vercel
   vercel
   ```

### Option 2 : Render (Gratuit avec limitations)

1. **Créer un compte** : https://render.com

2. **Créer un nouveau Web Service** :
   - Connecter votre repo GitHub
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `python api_server.py`

3. **Configurer les variables d'environnement**

4. **Déployer le frontend** sur Vercel ou Netlify

### Option 3 : Vercel + Railway (Recommandé pour production)

- **Backend (API)** : Railway
- **Frontend (React)** : Vercel

## 🔧 Configuration pour le Cloud

### Modifications nécessaires

1. **Base de données** : Utiliser PostgreSQL au lieu de fichiers locaux
2. **Stockage** : Utiliser S3 ou Cloudinary pour les médias
3. **Variables d'environnement** : Configurer les URLs et clés API

## 📝 Fichiers à créer

Voir les fichiers dans le projet :
- `railway.json`
- `Procfile`
- `runtime.txt`
- `.env.example`

