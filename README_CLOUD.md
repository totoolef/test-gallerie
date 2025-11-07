# ☁️ Guide de Déploiement Cloud

Ce guide explique comment déployer l'application pour qu'elle soit accessible partout sur votre téléphone, avec stockage dynamique et base de données.

## 🎯 Objectifs

- ✅ Accessible partout (pas seulement réseau local)
- ✅ Stockage dynamique (pas de dossiers locaux)
- ✅ Base de données pour les métadonnées
- ✅ Support Photo Picker API (iOS 16.4+)
- ✅ Stockage cloud (S3/Cloudinary) optionnel

## 📋 Prérequis

1. **Compte Railway** (gratuit) : https://railway.app
2. **Compte Vercel** (gratuit) : https://vercel.com
3. **Optionnel** : Compte AWS S3 ou Cloudinary pour le stockage

## 🚀 Déploiement

### Étape 1 : Préparer le projet

1. **Créer un repo GitHub** et pousser votre code

2. **Installer Railway CLI** :
   ```bash
   npm i -g @railway/cli
   railway login
   ```

3. **Créer les fichiers de configuration** (déjà créés) :
   - `railway.json`
   - `Procfile`
   - `.env.example`

### Étape 2 : Déployer le Backend (Railway)

1. **Créer un nouveau projet Railway** :
   ```bash
   railway init
   ```

2. **Ajouter PostgreSQL** :
   - Dans Railway, allez dans votre projet
   - Cliquez sur "New" → "Database" → "PostgreSQL"
   - Railway créera automatiquement `DATABASE_URL`

3. **Configurer les variables d'environnement** dans Railway :
   ```
   PORT=5000
   FLASK_ENV=production
   DATABASE_URL=<automatiquement créé par Railway>
   STORAGE_TYPE=local
   CORS_ORIGINS=https://votre-app.vercel.app,http://localhost:3000
   ```

4. **Déployer** :
   ```bash
   railway up
   ```

5. **Obtenir l'URL de l'API** :
   - Railway vous donnera une URL comme : `https://votre-app.railway.app`
   - Notez cette URL pour le frontend

### Étape 3 : Déployer le Frontend (Vercel)

1. **Installer Vercel CLI** :
   ```bash
   npm i -g vercel
   vercel login
   ```

2. **Configurer l'URL de l'API** :
   - Créez un fichier `.env.production` :
   ```
   VITE_API_URL=https://votre-app.railway.app/api
   ```

3. **Déployer** :
   ```bash
   vercel
   ```

4. **Configurer les variables d'environnement** dans Vercel :
   - Allez dans les paramètres de votre projet Vercel
   - Ajoutez `VITE_API_URL` avec l'URL de votre API Railway

### Étape 4 : Utiliser l'application

1. **Ouvrir l'URL Vercel** sur votre iPhone
2. **Installer l'application** (PWA)
3. **Importer vos photos** depuis l'app Photos

## 🔧 Configuration Avancée

### Stockage Cloud (Optionnel)

#### Option 1 : AWS S3

1. **Créer un bucket S3** sur AWS
2. **Créer des clés d'accès** (IAM)
3. **Configurer dans Railway** :
   ```
   STORAGE_TYPE=s3
   AWS_ACCESS_KEY_ID=votre_key
   AWS_SECRET_ACCESS_KEY=votre_secret
   S3_BUCKET=votre_bucket
   S3_REGION=us-east-1
   ```

#### Option 2 : Cloudinary

1. **Créer un compte** : https://cloudinary.com
2. **Configurer dans Railway** :
   ```
   STORAGE_TYPE=cloudinary
   CLOUDINARY_CLOUD_NAME=votre_cloud_name
   CLOUDINARY_API_KEY=votre_api_key
   CLOUDINARY_API_SECRET=votre_api_secret
   ```

### Base de données

Par défaut, Railway crée une base PostgreSQL. Pour utiliser SQLite en local :

```bash
# Pas besoin de DATABASE_URL, SQLite sera utilisé automatiquement
python api_server_cloud.py
```

## 📱 Utilisation sur iPhone

1. **Ouvrir l'application** dans Safari
2. **Installer** : Partager → Sur l'écran d'accueil
3. **Importer des photos** :
   - Cliquez sur le bouton bleu (icône image)
   - Sur iOS 16.4+, cela ouvrira Photo Picker
   - Sélectionnez vos photos
   - Elles seront automatiquement uploadées et indexées

## 🔄 Migration depuis la version locale

Pour migrer vos données existantes :

1. **Exporter les métadonnées** :
   ```python
   import json
   with open('metadata.json', 'r') as f:
       metadata = json.load(f)
   ```

2. **Importer dans la base de données** :
   ```python
   from database import get_db
   db = get_db()
   for item in metadata:
       db.add_media(
           file_path=item['file_path'],
           file_name=os.path.basename(item['file_path']),
           media_type=item.get('media_type', 'image'),
           caption=item.get('caption', '')
       )
   ```

## 🐛 Dépannage

### L'API ne démarre pas

- Vérifiez les variables d'environnement dans Railway
- Vérifiez les logs : `railway logs`

### Les photos ne s'uploadent pas

- Vérifiez les permissions de stockage
- Vérifiez les logs de l'API
- Vérifiez que CORS est bien configuré

### Photo Picker ne fonctionne pas

- Vérifiez que vous êtes sur iOS 16.4+
- L'application doit être en HTTPS
- L'application doit être installée (PWA)

## 📝 Notes

- **Gratuit** : Railway et Vercel ont des plans gratuits généreux
- **Limites** : 
  - Railway : 500h/mois gratuit
  - Vercel : 100GB/mois de bande passante
- **Stockage** : Utilisez S3 ou Cloudinary pour plus d'espace

## 🎯 Prochaines étapes

- [ ] Ajouter l'authentification utilisateur
- [ ] Implémenter la recherche vectorielle complète
- [ ] Ajouter la synchronisation cloud
- [ ] Optimiser l'indexation en arrière-plan

