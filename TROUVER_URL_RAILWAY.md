# 🔍 Comment Trouver l'URL de votre API Railway

## Méthode 1 : Via l'Interface Web

### Option A : Dans l'Onglet "Settings"

1. **Dans Railway**, allez dans votre projet "medIA"
2. **Cliquez sur votre service "test-gallerie"**
3. **Cliquez sur l'onglet "Settings"** (en haut, à côté de "Variables", "Deployments", etc.)
4. **Cherchez la section "Networking"** ou **"Domains"**
5. Si vous voyez un bouton **"Generate Domain"** ou **"Add Domain"**, cliquez dessus
6. Railway générera automatiquement un domaine comme : `https://test-gallerie-production-xxxx.up.railway.app`

### Option B : Dans l'Onglet "Deployments"

1. **Dans votre service "test-gallerie"**
2. **Cliquez sur l'onglet "Deployments"**
3. **Cliquez sur le dernier déploiement** (celui qui est actif)
4. **Cherchez une section "Domains"** ou **"URL"** dans les détails du déploiement
5. L'URL devrait être affichée là

### Option C : Dans la Vue d'Ensemble

1. **Dans votre projet Railway**, regardez la **vue d'ensemble** (onglet "Architecture")
2. **Sur la carte de votre service "test-gallerie"**, il devrait y avoir une **URL** affichée
3. Si ce n'est pas le cas, cliquez sur la carte pour voir plus de détails

## Méthode 2 : Via la CLI (Plus Simple)

### Générer un Domaine

```bash
# Lier le service d'abord (si pas déjà fait)
railway service

# Générer un domaine
railway domain
```

Railway vous donnera une URL comme :
```
Service Domain created:
🚀 https://test-gallerie-production-xxxx.up.railway.app
```

### Voir le Domaine Existant

```bash
# Voir le statut du service
railway status

# Ou voir les informations du service
railway service
```

## Méthode 3 : Dans les Logs

Parfois, l'URL est affichée dans les logs :

1. **Dans Railway**, allez dans votre service "test-gallerie"
2. **Onglet "Logs"** ou **"Deployments"** → dernier déploiement → **"View Logs"**
3. **Cherchez une ligne** qui contient `https://` ou `railway.app`

## 🐛 Si Vous Ne Trouvez Toujours Pas

### Vérifier que le Service est Déployé

1. **Dans Railway**, vérifiez que votre service "test-gallerie" a un déploiement actif
2. **Onglet "Deployments"** : Le dernier déploiement doit être "Active" (vert)
3. Si le déploiement est en cours ou a échoué, attendez qu'il se termine

### Générer le Domaine Manuellement

Si le domaine n'existe pas, vous pouvez le générer via la CLI :

```bash
# Lier le service
railway service

# Générer un domaine
railway domain
```

## 📝 Note

- Railway génère automatiquement un domaine pour chaque service
- Le domaine est de la forme : `https://nom-service-production-xxxx.up.railway.app`
- Si vous ne voyez pas de domaine, c'est qu'il n'a pas encore été généré


