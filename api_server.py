"""
API Flask pour servir les données à l'interface React iOS-like.
"""

import os
# Fix pour OpenMP sur macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
torch.set_num_threads(1)

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import base64
from PIL import Image
import io
import shutil
from datetime import datetime

# Import des modules core
from core.searcher import load_index_and_metadata, search
from core.clip_utils import get_embedder, CLIPEmbedder
from core.reranker import get_reranker, CrossEncoderReranker
from core.indexer import extract_and_index
from ui_utils import make_thumbnail, get_video_preview

app = Flask(__name__)
CORS(app)

# Variables globales pour le cache
_index = None
_metadata = []
_embedder = None
_reranker = None
_index_loaded = False


def load_index_if_needed():
    """Charge l'index et les métadonnées si nécessaire."""
    global _index, _metadata, _index_loaded
    
    if not _index_loaded:
        try:
            if os.path.exists("index.faiss") and os.path.exists("metadata.json"):
                _index, _metadata = load_index_and_metadata("index.faiss", "metadata.json")
                _index_loaded = True
                print(f"✅ Index chargé: {_index.ntotal} embedding(s)")
            else:
                print("⚠️  Aucun index trouvé")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'index: {e}")
            _index_loaded = False


def get_embedder_if_needed():
    """Charge l'embedder si nécessaire."""
    global _embedder
    
    if _embedder is None:
        try:
            _embedder = get_embedder(model_name="openai/clip-vit-large-patch14")
            print("✅ Embedder chargé")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'embedder: {e}")
    
    return _embedder


def get_reranker_if_needed():
    """Charge le reranker si nécessaire."""
    global _reranker
    
    if _reranker is None:
        try:
            _reranker = get_reranker()
            print("✅ Reranker chargé")
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement du reranker: {e}")
    
    return _reranker


@app.route('/api/media/initial', methods=['GET'])
def get_initial_media():
    """Récupère les N premiers médias pour la page d'accueil."""
    try:
        load_index_if_needed()
        
        if not _index_loaded or not _metadata:
            return jsonify({"media": []}), 200
        
        limit = int(request.args.get('limit', 9))
        
        # Prendre les N premiers médias uniques (grouper par fichier)
        unique_media = {}
        for meta in _metadata:
            file_path = meta.get("file_path", "")
            if file_path and file_path not in unique_media:
                unique_media[file_path] = meta
                if len(unique_media) >= limit:
                    break
        
        media_list = list(unique_media.values())
        
        return jsonify({
            "media": media_list,
            "count": len(media_list)
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur get_initial_media: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search_media():
    """Recherche des médias par requête texte."""
    try:
        load_index_if_needed()
        
        if not _index_loaded or not _metadata:
            return jsonify({"results": []}), 200
        
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"results": []}), 200
        
        # Options de recherche
        top_k = data.get('top_k', 12)
        use_query_expansion = data.get('use_query_expansion', True)
        auto_translate = data.get('auto_translate', False)
        use_dynamic_threshold = data.get('use_dynamic_threshold', False)
        fixed_threshold = data.get('fixed_threshold', 0.3)
        always_rerank = data.get('always_rerank', False)
        rerank_if_below = data.get('rerank_if_below', None)
        
        # Charger les modèles si nécessaire
        embedder = get_embedder_if_needed()
        reranker = get_reranker_if_needed() if (always_rerank or rerank_if_below) else None
        
        # Effectuer la recherche
        results = search(
            query_text=query,
            index=_index,
            metadata=_metadata,
            embedder=embedder,
            top_k=top_k,
            use_query_expansion=use_query_expansion,
            auto_translate=auto_translate,
            use_dynamic_threshold=use_dynamic_threshold,
            fixed_threshold=fixed_threshold,
            always_rerank=always_rerank,
            rerank_if_below=rerank_if_below,
            reranker=reranker,
            use_captions=True
        )
        
        # Grouper les résultats par fichier (éviter les doublons)
        unique_results = {}
        for result in results:
            file_path = result.get("path", "")
            score = result.get("score", 0.0)
            
            if file_path not in unique_results or score > unique_results[file_path].get("score", 0.0):
                unique_results[file_path] = result
        
        # Convertir en liste et trier par score
        results_list = sorted(unique_results.values(), key=lambda x: x.get("score", 0.0), reverse=True)
        
        return jsonify({
            "results": results_list,
            "count": len(results_list)
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur search_media: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/thumbnail', methods=['GET'])
def get_thumbnail():
    """Récupère une miniature pour un média."""
    try:
        file_path = request.args.get('path', '')
        media_type = request.args.get('type', 'image')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Fichier introuvable"}), 404
        
        # Générer la miniature
        if media_type == 'video':
            thumbnail = get_video_preview(file_path)
        else:
            thumbnail = make_thumbnail(file_path)
        
        if thumbnail is None:
            return jsonify({"error": "Impossible de générer la miniature"}), 500
        
        # Convertir en base64
        buffer = io.BytesIO()
        thumbnail.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # Retourner l'image
        return send_file(buffer, mimetype='image/jpeg')
        
    except Exception as e:
        print(f"❌ Erreur get_thumbnail: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/media/file', methods=['GET'])
def get_media_file():
    """Sert un fichier média (image ou vidéo) directement."""
    try:
        file_path = request.args.get('path', '')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Fichier introuvable"}), 404
        
        # Déterminer le type MIME
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
        }
        
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # Servir le fichier avec les en-têtes appropriés
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False,
            conditional=True
        )
        
    except Exception as e:
        print(f"❌ Erreur get_media_file: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyse', methods=['POST'])
def analyse_media():
    """Lance l'analyse/indexation des médias."""
    try:
        # Cette fonction devrait appeler la logique d'indexation
        # Pour l'instant, on retourne un succès
        # Dans une vraie implémentation, vous devriez lancer l'indexation en arrière-plan
        
        return jsonify({
            "status": "success",
            "message": "Analyse lancée avec succès"
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur analyse_media: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_media():
    """Upload des fichiers média depuis la galerie du téléphone."""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "Aucun fichier fourni"}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        
        # Créer le dossier data/ s'il n'existe pas
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Formats supportés
        ALLOWED_EXTENSIONS = {
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif',
            '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v',
            '.heic', '.heif'  # Formats iPhone
        }
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Vérifier l'extension
                filename = secure_filename(file.filename)
                ext = Path(filename).suffix.lower()
                
                if ext not in ALLOWED_EXTENSIONS:
                    errors.append(f"{filename}: Format non supporté")
                    continue
                
                # Générer un nom unique pour éviter les collisions
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                safe_name = f"{timestamp}_{filename}"
                file_path = data_dir / safe_name
                
                # Sauvegarder le fichier
                file.save(str(file_path))
                uploaded_files.append(str(file_path))
                
                print(f"✅ Fichier uploadé: {file_path}")
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
                print(f"❌ Erreur lors de l'upload de {file.filename}: {e}")
        
        if not uploaded_files:
            return jsonify({
                "error": "Aucun fichier n'a pu être uploadé",
                "details": errors
            }), 400
        
        # Indexer automatiquement les nouveaux fichiers
        try:
            print(f"🔄 Indexation de {len(uploaded_files)} nouveau(x) fichier(s)...")
            # Recharger l'index pour inclure les nouveaux fichiers
            extract_and_index(
                data_dir="data/",
                output_index="index.faiss",
                output_metadata="metadata.json",
                generate_captions=True
            )
            
            # Recharger l'index et les métadonnées
            global _index, _metadata, _index_loaded
            _index_loaded = False
            load_index_if_needed()
            
            print(f"✅ Indexation terminée")
            
        except Exception as e:
            print(f"⚠️  Erreur lors de l'indexation: {e}")
            # On retourne quand même les fichiers uploadés même si l'indexation a échoué
        
        return jsonify({
            "status": "success",
            "uploaded": len(uploaded_files),
            "files": uploaded_files,
            "errors": errors if errors else None
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur upload_media: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de santé."""
    load_index_if_needed()
    
    return jsonify({
        "status": "ok",
        "index_loaded": _index_loaded,
        "media_count": len(_metadata) if _index_loaded else 0
    }), 200


if __name__ == '__main__':
    import sys
    
    # Utiliser le port 5001 par défaut (5000 est souvent utilisé par AirPlay sur macOS)
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    print("🚀 Démarrage de l'API Flask...")
    print(f"📡 API disponible sur http://localhost:{port}")
    print(f"💡 Pour utiliser un autre port, définissez la variable d'environnement FLASK_PORT")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Erreur: Le port {port} est déjà utilisé")
            print(f"💡 Solutions:")
            print(f"   1. Utilisez un autre port: FLASK_PORT=8000 python api_server.py")
            print(f"   2. Trouvez et arrêtez le processus utilisant le port {port}")
            print(f"   3. Sur macOS, désactivez AirPlay Receiver dans Réglages Système")
            sys.exit(1)
        else:
            raise

