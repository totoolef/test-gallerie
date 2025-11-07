# Mon IA Média - Interface iOS-like

Interface professionnelle inspirée de l'iPhone et du design Apple pour explorer vos médias (images/vidéos) de manière intuitive.

## 🎯 Caractéristiques

- **Design Apple-like** : Interface sobre, épurée, fluide avec transitions douces
- **Mobile-first** : Optimisé pour iPhone (320-430px), adaptable tablette et desktop
- **Navigation intuitive** : Menu inférieur avec 4 icônes (Accueil, Recherche, Analyse, Paramètres)
- **Galerie responsive** : Grille 3 colonnes avec espacements fins entre médias
- **Recherche intelligente** : Recherche par texte avec CLIP et reranking
- **Chargement automatique** : Affichage des 9 premiers médias au démarrage

## 📦 Installation

### 1. Dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Dépendances Node.js

```bash
npm install
```

## 🚀 Utilisation

### Option 1 : Application React standalone

1. **Démarrer le serveur API Python** :
```bash
python api_server.py
```
**Note** : L'API utilise le port 5001 par défaut (5000 est souvent utilisé par AirPlay Receiver sur macOS). Pour utiliser un autre port, définissez la variable d'environnement `FLASK_PORT`.

2. **Dans un autre terminal, démarrer l'application React** :
```bash
npm run dev
```

3. **Ouvrir dans le navigateur** :
L'application sera disponible sur `http://localhost:3000`

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

## 📁 Structure du projet

```
mon-ia/
├── src/
│   ├── components/        # Composants UI réutilisables
│   │   ├── Header.jsx
│   │   ├── SearchBar.jsx
│   │   ├── MediaGrid.jsx
│   │   ├── BottomNav.jsx
│   │   └── AppLayout.jsx
│   ├── pages/            # Pages de l'application
│   │   ├── Home.jsx
│   │   ├── Search.jsx
│   │   ├── Analyse.jsx
│   │   └── Settings.jsx
│   ├── services/         # Services API
│   │   └── mediaService.js
│   ├── App.jsx           # Application principale
│   ├── main.jsx          # Point d'entrée
│   └── index.css         # Styles globaux
├── api_server.py         # API Flask pour servir les données
├── app_ios.py           # Wrapper Streamlit
├── package.json         # Dépendances Node.js
├── vite.config.js       # Configuration Vite
├── tailwind.config.js   # Configuration Tailwind
└── index.html           # Template HTML
```

## 🎨 Composants UI

### Header
Barre supérieure fixe avec titre centré, fond translucide et ombre douce.

### SearchBar
Barre de recherche arrondie style iOS Spotlight avec icône loupe.

### MediaGrid
Grille responsive 3 colonnes avec espacements fins, lazy loading et animations.

### BottomNav
Barre de navigation inférieure fixe avec 4 icônes animées (Accueil, Recherche, Analyse, Paramètres).

## 🔧 Configuration

### API Endpoints

- `GET /api/media/initial?limit=9` : Récupère les N premiers médias
- `POST /api/search` : Recherche des médias par requête texte
- `GET /api/thumbnail?path=...&type=...` : Récupère une miniature
- `POST /api/analyse` : Lance l'analyse/indexation des médias
- `GET /api/health` : Vérifie l'état de l'API

**Note** : L'API utilise le port 5001 par défaut (5000 est souvent utilisé par AirPlay Receiver sur macOS). Pour utiliser un autre port, définissez la variable d'environnement `FLASK_PORT`.

### Personnalisation

Vous pouvez personnaliser les couleurs, typographies et espacements dans `tailwind.config.js`.

## 📱 Responsive Design

L'interface est optimisée pour :
- **Mobile** : 320-430px (iPhone)
- **Tablette** : 768px+
- **Desktop** : 1024px+

## 🎯 Fonctionnalités

### Page Accueil
- Affichage automatique des 9 premiers médias
- Barre de recherche pour lancer une recherche
- Grille responsive avec lazy loading

### Page Recherche
- Recherche par texte avec CLIP
- Affichage des résultats en grille
- Support du reranking Cross-Encoder

### Page Analyse
- Lancement de l'indexation des médias
- Suivi de la progression
- Génération de captions avec BLIP

### Page Paramètres
- Basculement mode clair/sombre
- Gestion des notifications
- Informations sur l'application

## 🐛 Dépannage

### Le serveur API ne démarre pas
Vérifiez que le port 5000 n'est pas déjà utilisé :
```bash
lsof -i :5000
```

### L'interface React ne se charge pas
Vérifiez que l'application a été construite :
```bash
npm run build
```

### Les miniatures ne s'affichent pas
Vérifiez que les fichiers médias existent et que les permissions sont correctes.

## 📝 Notes

- L'interface utilise Framer Motion pour les animations fluides
- Les icônes proviennent de Lucide React
- Le design suit les guidelines Apple Human Interface Guidelines
- L'application est compatible avec les safe areas iOS

## 🔄 Mise à jour

Pour mettre à jour l'interface React après des modifications :
```bash
npm run build
```

Pour redémarrer le serveur API :
```bash
python api_server.py
```

## 📄 Licence

Ce projet est sous licence MIT.

