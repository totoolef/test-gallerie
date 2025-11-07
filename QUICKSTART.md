# 🚀 Guide de démarrage rapide

## Installation

### 1. Dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Dépendances Node.js

```bash
npm install
```

## Utilisation

### Option 1 : Application React standalone (Recommandé)

1. **Démarrer le serveur API Python** (dans un terminal) :
```bash
python api_server.py
```
**Note** : L'API utilise le port 5001 par défaut (5000 est souvent utilisé par AirPlay Receiver sur macOS). Pour utiliser un autre port : `FLASK_PORT=8000 python api_server.py`

2. **Démarrer l'application React** (dans un autre terminal) :
```bash
npm run dev
```

3. **Ouvrir dans le navigateur** :
L'application sera automatiquement ouverte sur `http://localhost:3000`

### Option 2 : Application Streamlit intégrée

1. **Construire l'interface React** :
```bash
npm run build
```

2. **Lancer l'application Streamlit** :
```bash
streamlit run app_ios.py
```

L'application Streamlit démarrera automatiquement le serveur API et chargera l'interface React.

## 📱 Utilisation de l'interface

### Page Accueil
- Affiche automatiquement les 9 premiers médias
- Utilisez la barre de recherche pour lancer une recherche

### Page Recherche
- Entrez votre requête dans la barre de recherche
- Les résultats s'affichent en grille 3 colonnes
- Cliquez sur un média pour voir les détails

### Page Analyse
- Cliquez sur "Lancer l'analyse" pour indexer vos médias
- L'analyse peut prendre quelques minutes selon le nombre de médias

### Page Paramètres
- Basculez le mode sombre/clair
- Gérez les notifications
- Consultez les informations sur l'application

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
VITE_API_URL=http://localhost:5000/api
VITE_PORT=3000
```

### Personnalisation

Vous pouvez personnaliser les couleurs et styles dans `tailwind.config.js`.

## 🐛 Dépannage

### Le serveur API ne démarre pas
- **Port déjà utilisé** : L'API utilise le port 5001 par défaut (5000 est souvent utilisé par AirPlay Receiver sur macOS)
- Pour utiliser un autre port : `FLASK_PORT=8000 python api_server.py`
- Vérifiez que les fichiers `index.faiss` et `metadata.json` existent
- Sur macOS, vous pouvez désactiver AirPlay Receiver dans Réglages Système > Général > AirDrop et Handoff

### L'interface React ne se charge pas
- Vérifiez que `npm install` a été exécuté
- Vérifiez que `npm run build` a été exécuté (pour Streamlit)

### Les miniatures ne s'affichent pas
- Vérifiez que les fichiers médias existent
- Vérifiez que les permissions sont correctes

## 📝 Notes

- L'application nécessite un index FAISS existant (`index.faiss` et `metadata.json`)
- Pour créer un index, utilisez `app_simple.py` ou la fonctionnalité d'analyse dans l'interface

