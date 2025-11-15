# 🔍 Diagnostic de l'Erreur de Build

## ❌ Erreur Actuelle
**"Failed to build an image. Please check the build logs for more details."**

Le build échoue pendant la phase "Build > Build image" après ~10 minutes.

---

## 🔎 Causes Possibles

### 1. **Commandes de nettoyage trop agressives** ✅ CORRIGÉ
- Les commandes `find` sur `/nix` et `/nix/store` peuvent échouer
- **Solution** : Simplifié `nixpacks.toml` pour ne garder que le nettoyage pip

### 2. **Fichier requirements-cloud.txt introuvable**
- Vérifier que le fichier est bien dans le repo GitHub
- **Vérification** : ✅ Le fichier est bien tracké par Git

### 3. **Erreur d'installation d'une dépendance**
- Une dépendance dans `requirements-cloud.txt` pourrait échouer
- **Solution** : Vérifier les logs de build dans Railway

### 4. **Problème de permissions**
- Les commandes de nettoyage pourraient manquer de permissions
- **Solution** : Simplification des commandes (fait)

---

## ✅ Corrections Appliquées

1. **Simplification de `nixpacks.toml`** :
   - Supprimé les commandes `find` complexes
   - Gardé uniquement `pip cache purge` qui est sûr

---

## 📋 Prochaines Étapes

### 1. Vérifier les Build Logs dans Railway

**Comment faire :**
1. Railway → Service "test-gallerie"
2. Onglet "Deployments"
3. Cliquer sur le dernier déploiement (celui qui a échoué)
4. Onglet "Build Logs"
5. **Chercher l'erreur exacte** (généralement à la fin des logs)

**Erreurs courantes à chercher :**
- `FileNotFoundError: requirements-cloud.txt`
- `ERROR: Could not find a version that satisfies the requirement`
- `Permission denied`
- `Command failed with exit code 1`

### 2. Si l'erreur persiste

**Option A : Revenir à requirements.txt temporairement**
Modifier `nixpacks.toml` :
```toml
[phases.install]
cmds = [
    "pip install --break-system-packages --no-cache-dir -r requirements.txt",
    "pip cache purge || true"
]
```

**Option B : Vérifier que requirements-cloud.txt est bien poussé**
```bash
git status
git add requirements-cloud.txt
git commit -m "Add requirements-cloud.txt"
git push origin main
```

---

## 🐛 Erreurs Spécifiques et Solutions

### Erreur : "FileNotFoundError: requirements-cloud.txt"
**Solution** : Le fichier n'est pas dans le repo
```bash
git add requirements-cloud.txt
git commit -m "Add requirements-cloud.txt"
git push origin main
```

### Erreur : "ERROR: Could not find a version that satisfies..."
**Solution** : Problème avec une dépendance spécifique
- Vérifier la version dans `requirements-cloud.txt`
- Essayer de mettre une version exacte au lieu de `>=`

### Erreur : "Command failed" sur une commande de nettoyage
**Solution** : Déjà corrigé en simplifiant `nixpacks.toml`

### Erreur : Timeout ou mémoire insuffisante
**Solution** : Les dépendances ML sont très lourdes
- Attendre plus longtemps (15-20 minutes)
- Ou utiliser torch CPU-only (voir RESUME_OPTIMISATIONS.md)

---

## 📝 Checklist de Diagnostic

- [ ] Vérifier les Build Logs dans Railway (onglet "Build Logs")
- [ ] Noter l'erreur exacte (dernières lignes des logs)
- [ ] Vérifier que `requirements-cloud.txt` est dans le repo
- [ ] Vérifier que `nixpacks.toml` est correct
- [ ] Si erreur sur une dépendance, vérifier sa version

---

## 🚀 Après Correction

Une fois l'erreur identifiée et corrigée :

1. **Commit les corrections** :
   ```bash
   git add nixpacks.toml
   git commit -m "Fix: Simplification nixpacks.toml"
   git push origin main
   ```

2. **Surveiller le nouveau déploiement** dans Railway

3. **Vérifier les Build Logs** pour confirmer que ça fonctionne

---

## 💡 Conseil

**Le plus important** : Regardez les **Build Logs** dans Railway pour voir l'erreur exacte. C'est là que vous trouverez la vraie cause du problème !

