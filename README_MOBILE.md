# 📱 Utilisation sur Mobile

Ce guide explique comment utiliser l'application sur votre téléphone et accéder à votre galerie.

## 🚀 Installation sur Mobile

### Option 1 : Application Web Progressive (PWA)

1. **Ouvrir l'application dans le navigateur mobile** :
   - Assurez-vous que le serveur API est démarré : `python api_server.py`
   - Assurez-vous que l'application React est démarrée : `npm run dev`
   - Accédez à l'URL depuis votre téléphone (voir section "Accès depuis le téléphone")

2. **Installer l'application** :
   - **Sur iOS (Safari)** : Cliquez sur le bouton "Partager" → "Sur l'écran d'accueil"
   - **Sur Android (Chrome)** : Un popup apparaîtra automatiquement, ou allez dans le menu → "Ajouter à l'écran d'accueil"

3. **L'application apparaîtra comme une app native** sur votre écran d'accueil

### Option 2 : Accès direct via navigateur

Vous pouvez simplement ouvrir l'application dans le navigateur mobile sans l'installer.

## 📡 Accès depuis le Téléphone

### Sur le même réseau Wi-Fi

1. **Trouver l'adresse IP de votre ordinateur** :
   - **macOS/Linux** : `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - **Windows** : `ipconfig` (cherchez "Adresse IPv4")

2. **Démarrer les serveurs** :
   ```bash
   # Terminal 1 : Serveur API
   python api_server.py
   
   # Terminal 2 : Application React
   npm run dev
   ```

3. **Accéder depuis le téléphone** :
   - Ouvrez le navigateur sur votre téléphone
   - Accédez à : `http://VOTRE_IP:3000` (remplacez VOTRE_IP par l'adresse IP trouvée)
   - Exemple : `http://192.168.1.100:3000`

### Configuration du serveur pour l'accès réseau

Par défaut, Vite écoute sur `localhost`. Pour permettre l'accès depuis le réseau :

1. **Modifier `vite.config.js`** :
   ```javascript
   server: {
     host: '0.0.0.0',  // Permet l'accès depuis le réseau
     port: 3000,
     // ...
   }
   ```

2. **Le serveur API Flask** écoute déjà sur `0.0.0.0` par défaut

## 📸 Upload depuis la Galerie Photos de l'iPhone

### Utilisation

1. **Ouvrir l'application** sur votre iPhone
2. **Aller sur la page d'accueil** (onglet Home)
3. **Cliquer sur le bouton bleu flottant** en bas à droite (icône upload)
4. **Sur iOS, cela ouvrira automatiquement l'app Photos** de votre iPhone
5. **Sélectionner des photos/vidéos** depuis votre galerie Photos
6. **Les fichiers seront automatiquement** :
   - Uploadés vers le serveur
   - Sauvegardés dans le dossier `data/` sur votre Mac
   - Indexés automatiquement avec CLIP
   - Disponibles pour la recherche
   - Affichés dans l'application

### Important

- **Les images affichées** sont celles qui sont dans le dossier `data/` et qui ont été indexées
- **Quand vous uploadez depuis votre iPhone**, les nouvelles images seront ajoutées au dossier `data/` sur votre Mac
- **L'indexation peut prendre quelques minutes** selon le nombre de fichiers
- **Les fichiers uploadés depuis l'iPhone** apparaîtront dans l'application après l'indexation

### Formats supportés

- **Images** : JPG, JPEG, PNG, BMP, GIF, WEBP, TIFF, HEIC, HEIF
- **Vidéos** : MP4, AVI, MOV, MKV, FLV, WMV, WEBM, M4V

### Fonctionnalités

- ✅ Upload multiple (sélectionner plusieurs fichiers à la fois)
- ✅ Indexation automatique après upload
- ✅ Rechargement automatique de la galerie
- ✅ Messages de confirmation/erreur
- ✅ Support des formats iPhone (HEIC/HEIF)

## 🔧 Dépannage

### L'application ne se charge pas depuis le téléphone

1. **Vérifier que les deux serveurs sont démarrés** :
   - API Flask : `http://localhost:5001/api/health`
   - React : `http://localhost:3000`

2. **Vérifier le pare-feu** :
   - Assurez-vous que les ports 3000 et 5001 sont ouverts
   - Sur macOS : Réglages Système → Pare-feu

3. **Vérifier que vous êtes sur le même réseau Wi-Fi**

### L'upload ne fonctionne pas

1. **Vérifier que le serveur API est démarré** :
   ```bash
   python api_server.py
   ```

2. **Vérifier les permissions** :
   - Le dossier `data/` doit être accessible en écriture
   - Vérifier les logs du serveur API pour les erreurs

3. **Vérifier la taille des fichiers** :
   - Les fichiers très volumineux peuvent prendre du temps
   - Vérifier la connexion réseau

### L'indexation prend du temps

- L'indexation automatique peut prendre quelques minutes selon le nombre de fichiers
- Les fichiers sont quand même uploadés même si l'indexation échoue
- Vous pouvez relancer l'indexation depuis la page "Analyse"

## 📝 Notes

- L'application fonctionne mieux sur le même réseau Wi-Fi
- Pour un usage en production, envisagez d'utiliser un service cloud (Heroku, Vercel, etc.)
- Les fichiers uploadés sont stockés localement sur le serveur dans le dossier `data/`
- L'indexation utilise CLIP et peut être gourmande en ressources

## 🎯 Prochaines étapes

- [ ] Ajouter la synchronisation cloud
- [ ] Ajouter la compression automatique des images
- [ ] Ajouter la gestion de l'espace disque
- [ ] Ajouter l'authentification utilisateur
- [ ] Optimiser l'indexation pour les gros volumes

