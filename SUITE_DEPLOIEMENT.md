# 🚀 Suite du Déploiement - Frontend sur Vercel

## ✅ Étape 2 Terminée - Backend sur Railway

Vous avez maintenant :
- ✅ Service "test-gallerie" déployé sur Railway
- ✅ PostgreSQL configuré et connecté
- ✅ Variables d'environnement configurées
- ✅ URL de l'API Railway (ex: `https://test-gallerie-production-xxxx.up.railway.app`)

## 📋 Étape 3 : Déployer le Frontend sur Vercel

### 1. Se Connecter à Vercel

```bash
vercel login
```

Choisissez "Continue with GitHub" et suivez les instructions.

### 2. Déployer le Frontend

```bash
vercel
```

Répondez aux questions :
- **Set up and deploy?** → `Y` (Oui)
- **Which scope?** → Votre compte
- **Link to existing project?** → `N` (Non)
- **What's your project's name?** → `mon-ia-media` (ou autre)
- **In which directory is your code located?** → `./` (Entrée)
- **Want to override the settings?** → `N` (Non)

### 3. Configurer l'URL de l'API

**Important** : Après le déploiement, vous devez configurer la variable d'environnement `VITE_API_URL`.

**Via l'Interface Web :**
1. Allez sur https://vercel.com
2. Sélectionnez votre projet
3. Allez dans **Settings** → **Environment Variables**
4. Ajoutez :
   - **Name** : `VITE_API_URL`
   - **Value** : `https://votre-url-railway.app/api` (remplacez par votre URL Railway)
   - **Environment** : Cochez Production, Preview, Development
5. Cliquez sur **Save**

**Via la CLI :**
```bash
vercel env add VITE_API_URL production
# Entrez votre URL Railway : https://votre-url-railway.app/api
```

### 4. Redéployer avec les Variables

```bash
vercel --prod
```

### 5. Obtenir l'URL Vercel

Après le déploiement, Vercel vous donnera une URL comme :
`https://mon-ia-media.vercel.app`

### 6. Mettre à Jour CORS dans Railway

1. **Dans Railway**, allez dans votre service "test-gallerie"
2. **Onglet "Variables"**
3. **Modifiez `CORS_ORIGINS`** :
   - Ancienne valeur : `http://localhost:3000,*`
   - Nouvelle valeur : `https://mon-ia-media.vercel.app,http://localhost:3000,*`
   - (Remplacez par votre URL Vercel)

### 7. Tester l'Application

1. **Ouvrez l'URL Vercel** sur votre iPhone
2. **Installez l'application** (PWA) : Safari → Partager → Sur l'écran d'accueil
3. **Testez l'upload de photos** depuis l'app Photos

## 🎯 Résumé des URLs

- **Backend (Railway)** : `https://test-gallerie-production-xxxx.up.railway.app`
- **Frontend (Vercel)** : `https://mon-ia-media.vercel.app`
- **API Health Check** : `https://test-gallerie-production-xxxx.up.railway.app/api/health`

## ✅ Checklist Finale

- [ ] Backend déployé sur Railway
- [ ] API répond sur `/api/health`
- [ ] Frontend déployé sur Vercel
- [ ] Variable `VITE_API_URL` configurée dans Vercel
- [ ] Variable `CORS_ORIGINS` mise à jour dans Railway
- [ ] Application accessible sur iPhone
- [ ] Upload de photos fonctionne


