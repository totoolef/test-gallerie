# 🔧 Guide : Configurer les Variables d'Environnement dans Railway

## Méthode 1 : Via l'Interface Web (Recommandé - Plus Simple)

### Étape 1 : Ouvrir votre projet Railway

1. Allez sur https://railway.app
2. Connectez-vous avec votre compte
3. Cliquez sur votre projet **medIA**

### Étape 2 : Accéder aux Variables d'Environnement

1. Dans votre projet, vous verrez votre service (ou "New Service" si pas encore créé)
2. Cliquez sur votre service (ou créez-en un nouveau si nécessaire)
3. Cliquez sur l'onglet **"Variables"** en haut
4. Ou cliquez sur **"Settings"** puis **"Variables"**

### Étape 3 : Ajouter les Variables

Cliquez sur **"New Variable"** et ajoutez une par une :

#### Variable 1 : PORT
- **Name** : `PORT`
- **Value** : `5000`
- Cliquez sur **"Add"**

#### Variable 2 : FLASK_ENV
- **Name** : `FLASK_ENV`
- **Value** : `production`
- Cliquez sur **"Add"**

#### Variable 3 : DATABASE_URL
- **Name** : `DATABASE_URL`
- **Value** : Railway l'a créé automatiquement si vous avez ajouté PostgreSQL
  - Si vous avez ajouté PostgreSQL, Railway a déjà créé cette variable
  - Sinon, vous devez d'abord ajouter PostgreSQL (voir ci-dessous)
- Si elle existe déjà, ne la modifiez pas !

#### Variable 4 : STORAGE_TYPE
- **Name** : `STORAGE_TYPE`
- **Value** : `local`
- Cliquez sur **"Add"**

#### Variable 5 : CORS_ORIGINS
- **Name** : `CORS_ORIGINS`
- **Value** : `https://votre-app.vercel.app,http://localhost:3000`
  - Remplacez `votre-app.vercel.app` par votre URL Vercel (vous l'obtiendrez après le déploiement du frontend)
  - Pour l'instant, mettez : `http://localhost:3000,*`
- Cliquez sur **"Add"**

### Étape 4 : Ajouter PostgreSQL (si pas encore fait)

1. Dans votre projet Railway, cliquez sur **"New"**
2. Sélectionnez **"Database"**
3. Choisissez **"PostgreSQL"**
4. Railway créera automatiquement la variable `DATABASE_URL`

## Méthode 2 : Via la CLI Railway

### Étape 1 : Lier le projet

```bash
railway link --project medIA
```

### Étape 2 : Ajouter les variables

```bash
# PORT
railway variables set PORT=5000

# FLASK_ENV
railway variables set FLASK_ENV=production

# STORAGE_TYPE
railway variables set STORAGE_TYPE=local

# CORS_ORIGINS (pour l'instant, mettez localhost)
railway variables set CORS_ORIGINS="http://localhost:3000,*"
```

### Étape 3 : Vérifier les variables

```bash
railway variables
```

## 📝 Variables à Configurer

| Variable | Valeur | Description |
|----------|--------|-------------|
| `PORT` | `5000` | Port sur lequel l'API écoute |
| `FLASK_ENV` | `production` | Environnement Flask |
| `DATABASE_URL` | Auto | Créé automatiquement par Railway si PostgreSQL est ajouté |
| `STORAGE_TYPE` | `local` | Type de stockage (local, s3, cloudinary) |
| `CORS_ORIGINS` | `http://localhost:3000,*` | Origines autorisées pour CORS |

## ⚠️ Important

- **DATABASE_URL** : Si vous n'avez pas encore ajouté PostgreSQL, faites-le d'abord
- **CORS_ORIGINS** : Vous pourrez mettre à jour cette variable après avoir déployé le frontend sur Vercel
- Toutes les variables sont sensibles à la casse (majuscules/minuscules)

## ✅ Vérification

Pour vérifier que tout est bien configuré :

```bash
railway variables
```

Vous devriez voir toutes vos variables listées.


