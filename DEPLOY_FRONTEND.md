# 🚀 Guide de Déploiement Frontend sur Vercel

## Étape 1 : Vérifier que le backend est déployé

Avant de déployer le frontend, assurez-vous que votre backend est déployé sur Railway et que vous avez l'URL de l'API.

Pour obtenir l'URL de votre API Railway :
```bash
railway domain
# ou
railway service
```

L'URL devrait ressembler à : `https://votre-app.railway.app`

## Étape 2 : Configurer l'URL de l'API

1. **Créer un fichier `.env.production`** (localement, ne sera pas commité) :
   ```bash
   echo "VITE_API_URL=https://votre-app.railway.app/api" > .env.production
   ```

2. **Ou configurer dans Vercel** (recommandé) :
   - Après le déploiement, allez dans les paramètres de votre projet Vercel
   - Ajoutez la variable d'environnement : `VITE_API_URL` = `https://votre-app.railway.app/api`

## Étape 3 : Se connecter à Vercel

```bash
vercel login
```

Choisissez "Continue with GitHub" et suivez les instructions.

## Étape 4 : Déployer

```bash
vercel
```

Vercel vous posera quelques questions :
- **Set up and deploy?** → Oui (Y)
- **Which scope?** → Votre compte
- **Link to existing project?** → Non (N)
- **What's your project's name?** → mon-ia-media (ou le nom que vous voulez)
- **In which directory is your code located?** → ./ (appuyez sur Entrée)
- **Want to override the settings?** → Non (N)

## Étape 5 : Configurer les variables d'environnement dans Vercel

1. Allez sur https://vercel.com
2. Sélectionnez votre projet
3. Allez dans **Settings** → **Environment Variables**
4. Ajoutez :
   - **Name** : `VITE_API_URL`
   - **Value** : `https://votre-app.railway.app/api`
   - **Environment** : Production, Preview, Development (cochez tout)
5. Cliquez sur **Save**

## Étape 6 : Redéployer

Après avoir ajouté les variables d'environnement, redéployez :

```bash
vercel --prod
```

## Étape 7 : Tester

1. Ouvrez l'URL Vercel sur votre iPhone
2. Installez l'application (PWA)
3. Testez l'upload de photos

## 🐛 Dépannage

### L'API ne répond pas

- Vérifiez que l'URL de l'API est correcte dans Vercel
- Vérifiez que CORS est configuré dans Railway
- Vérifiez les logs : `vercel logs`

### Les variables d'environnement ne fonctionnent pas

- Les variables Vite doivent commencer par `VITE_`
- Redéployez après avoir ajouté les variables
- Vérifiez que les variables sont dans tous les environnements (Production, Preview, Development)


