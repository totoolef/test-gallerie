# 🔍 Moteur de Recherche Multimédia Local

Un système d'analyse de contenus multimédias (photos + vidéos) capable de répondre à une requête utilisateur formulée en langage naturel, fonctionnant entièrement en local.

## 🎯 Fonctionnalités

- **Indexation automatique** : Parcourt des dossiers contenant des images et vidéos
- **Extraction d'embeddings** : Utilise le modèle CLIP (`openai/clip-vit-large-patch14`) pour extraire des descripteurs vectoriels sémantiques
- **Indexation FAISS** : Stocke les embeddings dans un index FAISS pour une recherche rapide
- **Recherche sémantique** : Recherche dans le corpus via des requêtes texte en langage naturel
- **Support multimédia** : Gère les images (JPG, PNG, etc.) et vidéos (MP4, AVI, MOV, etc.)
- **Extraction de frames vidéo** : Extrait automatiquement des frames à intervalles réguliers des vidéos
- **Génération de légendes** : Utilise BLIP pour générer des descriptions automatiques des images
- **Re-ranking** : Améliore les résultats avec un modèle Cross-Encoder
- **Intégration Photos macOS** : Récupère automatiquement les photos depuis l'app Photos du Mac

## 📦 Installation

1. **Créer un environnement virtuel** (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### Interface Streamlit

L'interface graphique principale est disponible via `app_simple.py` :

```bash
streamlit run app_simple.py
```

L'interface offre :
- **Récupération depuis Photos.app** : Récupère automatiquement les photos depuis l'app Photos du Mac
- **Indexation interactive** : Lance l'analyse avec barre de progression et logs en temps réel
- **Recherche visuelle** : Recherche avec affichage des résultats en grille (vignettes, previews vidéo)
- **Options configurables** : Tous les paramètres d'indexation et de recherche dans la sidebar
- **Ouverture dans Finder** : Ouvre directement les fichiers trouvés dans le Finder (macOS)
- **Historique des recherches** : Conserve l'historique des recherches récentes

**Note macOS** : Pour accéder aux photos depuis l'app Photos, vous devez :
1. Autoriser l'accès complet au disque dans **Réglages Système > Confidentialité et sécurité > Accès complet au disque**
2. Autoriser l'accès à Photos dans **Réglages Système > Confidentialité et sécurité > Photos**
3. Autoriser Terminal ou votre application Python

### Évaluation (Optionnel)

Un script d'évaluation est disponible pour tester la performance du moteur :

```bash
python evaluate_search.py --test-queries test_queries.json
```

## 📁 Structure du Projet

```
mon-ia/
├── app_simple.py           # Interface Streamlit principale
├── photos_utils.py          # Utilitaires pour accéder à l'app Photos (macOS)
├── ui_utils.py              # Utilitaires UI (thumbnails, sélecteur dossier)
├── evaluate_search.py       # Script d'évaluation (optionnel)
├── core/
│   ├── __init__.py
│   ├── clip_utils.py        # Module utilitaire CLIP (encodage images/texte)
│   ├── indexer.py           # Extraction embeddings et indexation FAISS
│   ├── searcher.py          # Recherche dans l'index
│   ├── captioner.py         # Génération de légendes BLIP
│   ├── reranker.py          # Re-ranking Cross-Encoder
│   ├── eval.py              # Utilitaires d'évaluation
│   └── filters.py           # Filtres de recherche
├── requirements.txt         # Dépendances Python
├── README.md                # Documentation
├── data/                    # Dossier contenant vos médias (optionnel)
├── index.faiss              # Index FAISS (généré)
└── metadata.json            # Métadonnées (généré)
```

## 🔧 Architecture

### Modules Core

1. **`core/clip_utils.py`** : 
   - Classe `CLIPEmbedder` pour gérer l'encodage CLIP
   - Fonctions pour encoder des images et du texte
   - Support automatique CPU/GPU

2. **`core/indexer.py`** :
   - Parcourt récursivement les dossiers de médias
   - Traite les images avec PIL
   - Extrait des frames des vidéos avec OpenCV
   - Crée l'index FAISS et les métadonnées JSON
   - Support multi-échelle pour les images (5 crops)

3. **`core/searcher.py`** :
   - Charge l'index FAISS et les métadonnées
   - Encode la requête texte avec CLIP
   - Recherche les embeddings les plus proches
   - Support query expansion (FR/EN)
   - Seuil dynamique adaptatif

4. **`core/captioner.py`** :
   - Génère des légendes automatiques avec BLIP
   - Améliore la recherche en utilisant les légendes

5. **`core/reranker.py`** :
   - Re-ranking avec Cross-Encoder
   - Améliore la précision des résultats

### Formats Supportés

**Images** : `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.webp`, `.tiff`, `.tif`, `.heic`, `.heif`

**Vidéos** : `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`, `.m4v`, `.3gp`

## 🔄 Réindexation

Si vous ajoutez de nouveaux médias, utilisez l'interface Streamlit pour réindexer. L'ancien index sera remplacé.

## 📝 Notes

- **Performance** : Le traitement peut être lent sur CPU. Pour de gros volumes, considérez l'utilisation d'un GPU.
- **Stockage** : L'index FAISS et les métadonnées peuvent prendre de l'espace pour de grandes collections.
- **Première exécution** : Les modèles CLIP et BLIP seront téléchargés automatiquement lors de la première utilisation.

## 🐛 Gestion des Erreurs

Le système gère automatiquement :
- Fichiers média corrompus ou non valides
- Formats non supportés
- Erreurs d'ouverture de vidéos
- Fichiers manquants

Les erreurs sont affichées avec un préfixe ⚠️ et le traitement continue avec les autres fichiers.

## 📄 Licence

Projet personnel - Libre d'utilisation.
