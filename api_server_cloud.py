"""
API Flask pour servir les données à l'interface React iOS-like.
Version cloud avec base de données et stockage dynamique.
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

# Import des nouveaux modules
from database import get_db
from storage import get_storage

app = Flask(__name__)

# Configuration CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins)

# Variables globales pour le cache
_index = None
_metadata = []
_embedder = None
_reranker = None
_index_loaded = False

# Instances de base de données et stockage
db = get_db()
storage = get_storage()


def load_index_if_needed():
    """Charge l'index et les métadonnées si nécessaire."""
    global _index, _metadata, _index_loaded
    
    if not _index_loaded:
        try:
            # Essayer de charger depuis les fichiers (compatibilité)
            if os.path.exists("index.faiss") and os.path.exists("metadata.json"):
                _index, _metadata = load_index_and_metadata("index.faiss", "metadata.json")
                _index_loaded = True
                print(f"✅ Index chargé depuis fichiers: {_index.ntotal} embedding(s)")
            else:
                # Charger depuis la base de données
                _metadata = db.list_media(limit=10000)
                if _metadata:
                    # Reconstruire l'index FAISS depuis la base de données
                    # Pour l'instant, on utilise les métadonnées seulement
                    _index_loaded = True
                    print(f"✅ Métadonnées chargées depuis la base de données: {len(_metadata)} média(s)")
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
        
        limit = int(request.args.get('limit', 9))
        
        # Récupérer depuis la base de données
        media_list = db.list_media(limit=limit, offset=0)
        
        # Formater pour l'API
        formatted_media = []
        for media in media_list:
            formatted_media.append({
                "file_path": media.get("file_path", ""),
                "file_name": media.get("file_name", ""),
                "media_type": media.get("media_type", "image"),
                "caption": media.get("caption", ""),
                "created_at": media.get("created_at", "")
            })
        
        return jsonify({
            "media": formatted_media,
            "count": len(formatted_media)
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur get_initial_media: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search_media():
    """Recherche des médias par requête texte."""
    try:
        load_index_if_needed()
        
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
        
        # Pour l'instant, recherche simple par caption
        # TODO: Implémenter la recherche vectorielle avec FAISS
        all_media = db.list_media(limit=1000)
        
        # Filtrer par caption (recherche simple)
        results = []
        query_lower = query.lower()
        for media in all_media:
            caption = media.get("caption", "").lower()
            if query_lower in caption:
                results.append({
                    "path": media.get("file_path", ""),
                    "file_path": media.get("file_path", ""),
                    "score": 0.8,  # Score simple
                    "caption": media.get("caption", ""),
                    "media_type": media.get("media_type", "image")
                })
        
        # Limiter les résultats
        results = results[:top_k]
        
        return jsonify({
            "results": results,
            "count": len(results)
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur search_media: {e}")
        import traceback
        traceback.print_exc()
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
                
                # Déterminer le type MIME
                mime_type = file.content_type or f"image/{ext[1:]}" if ext in ['.jpg', '.jpeg', '.png'] else f"video/{ext[1:]}"
                
                # Déterminer le type média
                media_type = "video" if ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'] else "image"
                
                # Sauvegarder le fichier dans le stockage
                # Lire le contenu du fichier
                file.seek(0)  # S'assurer qu'on est au début
                file_path = storage.save_file(file, filename, mime_type)
                file.seek(0)  # Remettre au début pour la taille
                
                # Ajouter à la base de données
                media_id = db.add_media(
                    file_path=file_path,
                    file_name=filename,
                    media_type=media_type,
                    file_size=len(file.read()),
                    mime_type=mime_type,
                    caption=""  # Sera généré plus tard
                )
                
                uploaded_files.append({
                    "id": media_id,
                    "file_path": file_path,
                    "file_name": filename,
                    "media_type": media_type
                })
                
                print(f"✅ Fichier uploadé: {file_path} (ID: {media_id})")
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
                print(f"❌ Erreur lors de l'upload de {file.filename}: {e}")
                import traceback
                traceback.print_exc()
        
        if not uploaded_files:
            return jsonify({
                "error": "Aucun fichier n'a pu être uploadé",
                "details": errors
            }), 400
        
        # Indexer automatiquement les nouveaux fichiers (en arrière-plan)
        # TODO: Implémenter l'indexation en arrière-plan
        try:
            print(f"🔄 Indexation de {len(uploaded_files)} nouveau(x) fichier(s)...")
            # Pour l'instant, on ne fait que sauvegarder
            # L'indexation complète sera faite plus tard
            print(f"✅ Fichiers sauvegardés (indexation à venir)")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'indexation: {e}")
        
        # Recharger les métadonnées
        global _metadata, _index_loaded
        _index_loaded = False
        load_index_if_needed()
        
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


@app.route('/api/thumbnail', methods=['GET'])
def get_thumbnail():
    """Récupère une miniature pour un média."""
    try:
        file_path = request.args.get('path', '')
        media_type = request.args.get('type', 'image')
        
        if not file_path:
            return jsonify({"error": "Chemin non fourni"}), 400
        
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
        
        if not file_path:
            return jsonify({"error": "Chemin non fourni"}), 400
        
        # Obtenir l'URL du fichier depuis le stockage
        file_url = storage.get_file_url(file_path)
        
        # Si c'est une URL (S3/Cloudinary), rediriger
        if file_url.startswith('http'):
            from flask import redirect
            return redirect(file_url)
        
        # Sinon, servir le fichier localement
        if not os.path.exists(file_path):
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


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de santé."""
    load_index_if_needed()
    
    media_count = len(_metadata) if _index_loaded else db.list_media(limit=1)
    
    return jsonify({
        "status": "ok",
        "index_loaded": _index_loaded,
        "media_count": len(media_count) if isinstance(media_count, list) else media_count,
        "storage_type": storage.storage_type
    }), 200


if __name__ == '__main__':
    import sys
    
    # Utiliser le port depuis l'environnement (pour Railway/Render)
    port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5001)))
    
    print("🚀 Démarrage de l'API Flask (version cloud)...")
    print(f"📡 API disponible sur http://0.0.0.0:{port}")
    print(f"💾 Stockage: {storage.storage_type}")
    print(f"🗄️  Base de données: {'PostgreSQL' if db.use_postgres else 'SQLite'}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Erreur: Le port {port} est déjà utilisé")
            sys.exit(1)
        else:
            raise

