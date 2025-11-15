# 🔧 Corriger la Connexion à la Base de Données

## ❌ Problème Identifié

Dans Railway, votre service "test-gallerie" n'a pas accès à la variable `DATABASE_URL` de PostgreSQL.

Le message **"Trying to connect a database? Add Variable"** indique que l'application ne peut pas se connecter à la base de données.

## ✅ Solution : Ajouter la Variable DATABASE_URL

### Méthode 1 : Via l'Interface Web (Recommandé)

1. **Dans votre service "test-gallerie"**, allez dans l'onglet **"Variables"**
2. **Cliquez sur "Add Variable"** (ou sur le message "Trying to connect a database? Add Variable")
3. Railway vous proposera automatiquement d'ajouter la variable `DATABASE_URL` depuis PostgreSQL
4. **Sélectionnez le service "Postgres"** dans la liste
5. **Choisissez la variable `DATABASE_URL`** (ou `PGDATABASE`, `PGHOST`, etc.)
6. **Cliquez sur "Add"**

### Méthode 2 : Via "Shared Variable"

1. **Dans l'onglet "Variables"** de "test-gallerie"
2. **Cliquez sur "Shared Variable"** (en haut à droite)
3. **Sélectionnez le service "Postgres"**
4. **Cochez `DATABASE_URL`** (ou toutes les variables PostgreSQL)
5. **Cliquez sur "Add"**

### Méthode 3 : Via la CLI

```bash
# Lier le service d'abord
railway service

# Ajouter la variable DATABASE_URL depuis PostgreSQL
railway variables set DATABASE_URL=$DATABASE_URL --from postgres
```

## 📋 Variables PostgreSQL à Ajouter

Railway crée automatiquement ces variables pour PostgreSQL :
- `DATABASE_URL` (la plus importante - contient toute la connexion)
- `PGDATABASE` (nom de la base)
- `PGHOST` (hôte)
- `PGPORT` (port)
- `PGUSER` (utilisateur)
- `PGPASSWORD` (mot de passe)

**Pour votre application, vous avez surtout besoin de `DATABASE_URL`.**

## ✅ Vérification

Après avoir ajouté la variable :

1. **Vérifiez dans l'onglet "Variables"** que `DATABASE_URL` apparaît maintenant
2. **Vérifiez les logs** pour voir si l'application se connecte :
   ```bash
   railway logs
   ```
3. **Testez l'API** :
   ```bash
   curl https://votre-service.railway.app/api/health
   ```

## 🐛 Si ça ne fonctionne toujours pas

1. **Vérifiez que PostgreSQL est bien démarré** (dans le panneau de gauche, le service Postgres doit être vert)
2. **Vérifiez les logs de PostgreSQL** pour voir s'il y a des erreurs
3. **Vérifiez que l'application utilise bien `api_server_cloud.py`** qui utilise la base de données


