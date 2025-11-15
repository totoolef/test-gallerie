# ✅ Vérifier que le Déploiement Fonctionne

## 📋 Checklist - Vérifications à Faire

### ✅ 1. Variables d'Environnement Configurées

Dans Railway, dans votre service "test-gallerie" → onglet "Variables", vous devriez avoir :

- ✅ `PORT=5000`
- ✅ `FLASK_ENV=production`
- ✅ `STORAGE_TYPE=local`
- ✅ `CORS_ORIGINS=http://localhost:3000,*`
- ✅ `DATABASE_URL` (ajoutée depuis PostgreSQL)

### ✅ 2. Service Déployé

1. **Dans Railway**, allez dans votre service "test-gallerie"
2. **Onglet "Deployments"** : Vous devriez voir un déploiement récent
3. **Statut** : Le déploiement devrait être "Active" (vert) ou en cours

### ✅ 3. Obtenir l'URL de l'API

1. **Dans votre service "test-gallerie"**, allez dans **"Settings"**
2. **Section "Domains"** :
   - Si un domaine existe déjà, copiez-le
   - Sinon, cliquez sur **"Generate Domain"**
3. **Copiez l'URL** (ex: `https://test-gallerie-production-xxxx.up.railway.app`)

### ✅ 4. Tester l'API

Une fois que vous avez l'URL, testez-la :

```bash
# Remplacez par votre URL Railway
curl https://votre-url-railway.app/api/health
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

### ✅ 5. Vérifier les Logs

**Via l'Interface Web :**
1. Dans votre service "test-gallerie"
2. Onglet **"Logs"** ou **"Deployments"** → cliquez sur le dernier déploiement → **"View Logs"**
3. Vous devriez voir :
   ```
   🚀 Démarrage de l'API Flask (version cloud)...
   📡 API disponible sur http://0.0.0.0:5000
   💾 Stockage: local
   🗄️  Base de données: PostgreSQL
   ```

**Via la CLI :**
```bash
railway logs --service test-gallerie
```

## 🐛 Problèmes Courants

### L'API ne répond pas

1. **Vérifiez que le service est déployé** : Onglet "Deployments" → le dernier déploiement doit être "Active"
2. **Vérifiez les logs** pour voir les erreurs
3. **Vérifiez que le domaine est généré** : Settings → Domains

### Erreur de connexion à la base de données

1. **Vérifiez que `DATABASE_URL` est bien configurée** dans les variables
2. **Vérifiez que PostgreSQL est démarré** (service Postgres doit être vert)
3. **Vérifiez les logs** pour voir l'erreur exacte

### Le service ne démarre pas

1. **Vérifiez les logs** pour voir l'erreur
2. **Vérifiez que `api_server_cloud.py` existe** dans le repo
3. **Vérifiez que toutes les dépendances sont dans `requirements.txt`**

## 📝 Prochaines Étapes

Une fois que l'API fonctionne :

1. **Notez l'URL de l'API** (ex: `https://test-gallerie-production-xxxx.up.railway.app`)
2. **Passez à l'étape 3** du README_CLOUD.md pour déployer le frontend sur Vercel
3. **Mettez à jour `CORS_ORIGINS`** dans Railway avec l'URL Vercel après le déploiement


