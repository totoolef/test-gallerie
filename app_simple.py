"""
Interface Streamlit simplifiée pour le moteur de recherche multimédia CLIP/FAISS.
Une seule page avec bouton pour récupérer les photos depuis l'app Photos du Mac.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

import streamlit as st
import json
import faiss
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import sys
import io
import tempfile
import shutil

# Import des modules core APRÈS torch
from core.indexer import extract_and_index_multiple_dirs, get_media_files
from core.searcher import load_index_and_metadata, search
from core.clip_utils import get_embedder, CLIPEmbedder
from core.captioner import get_captioner, BLIPCaptioner
from core.reranker import get_reranker, CrossEncoderReranker
from photos_utils import get_photos_from_photos_app, get_photos_from_library

# Import des utilitaires UI
from ui_utils import (
    make_thumbnail, get_video_preview,
    open_in_finder, human_readable_score, format_file_size
)

# Configuration de la page
st.set_page_config(
    page_title="Recherche Photos CLIP",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialiser session_state
if 'index_loaded' not in st.session_state:
    st.session_state.index_loaded = False
if 'index' not in st.session_state:
    st.session_state.index = None
if 'metadata' not in st.session_state:
    st.session_state.metadata = []
if 'last_results' not in st.session_state:
    st.session_state.last_results = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'photos_loaded' not in st.session_state:
    st.session_state.photos_loaded = False
if 'photos_temp_dir' not in st.session_state:
    st.session_state.photos_temp_dir = None


# Cache des modèles avec st.cache_resource
@st.cache_resource
def load_clip_embedder(model_name: str = "openai/clip-vit-large-patch14"):
    """Charge le modèle CLIP et le met en cache."""
    return get_embedder(model_name=model_name)


@st.cache_resource
def load_blip_captioner():
    """Charge le modèle BLIP et le met en cache."""
    return get_captioner()


@st.cache_resource
def load_reranker():
    """Charge le modèle Cross-Encoder et le met en cache."""
    return get_reranker()


def get_index_info(index_path: str = "index.faiss", metadata_path: str = "metadata.json") -> Optional[Dict]:
    """Récupère les informations sur l'index."""
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        return None
    
    try:
        index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Obtenir la date de modification
        index_mtime = os.path.getmtime(index_path)
        index_date = datetime.fromtimestamp(index_mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "ntotal": index.ntotal,
            "dimension": index.d if hasattr(index, 'd') else None,
            "date": index_date,
            "metadata_count": len(metadata)
        }
    except Exception as e:
        return None


def load_index(index_path: str = "index.faiss", metadata_path: str = "metadata.json"):
    """Charge l'index et les métadonnées dans session_state."""
    try:
        index, metadata = load_index_and_metadata(index_path, metadata_path)
        st.session_state.index = index
        st.session_state.metadata = metadata
        st.session_state.index_loaded = True
        return True
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de l'index: {e}")
        return False


# Sidebar - Options globales
with st.sidebar:
    st.title("⚙️ Options")
    
    # Section Index
    st.header("📊 Index")
    index_info = get_index_info()
    if index_info:
        st.success(f"✅ Index chargé")
        st.caption(f"**{index_info['ntotal']}** embeddings")
        st.caption(f"Dimension: **{index_info['dimension']}**")
        st.caption(f"Date: **{index_info['date']}**")
        
        if st.button("🔄 Recharger l'index"):
            if load_index():
                st.success("✅ Index rechargé")
                st.rerun()
    else:
        st.warning("⚠️ Aucun index trouvé")
        st.caption("Cliquez sur 'Analyser Photos' pour créer un index")
    
    st.divider()
    
    # Options d'indexation
    st.header("📝 Indexation")
    use_quality_selection = st.checkbox("Sélection intelligente des frames vidéo", value=True)
    max_frames_per_video = st.slider("Nb de frames vidéo max / vidéo", 5, 30, 10)
    use_multi_scale = st.checkbox("Multi-échelle images (5 crops)", value=True)
    generate_captions = st.checkbox("Générer des captions (BLIP)", value=True)
    batch_size = st.slider("Batch size images", 8, 64, 32)
    
    st.divider()
    
    # Options de recherche
    st.header("🔍 Recherche")
    top_k = st.slider("Top-K", 5, 50, 12)
    
    # Seuil dynamique ou fixe
    use_dynamic_threshold = st.checkbox("Seuil dynamique", value=False, help="Calcule un seuil adaptatif basé sur la distribution des scores")
    if use_dynamic_threshold:
        st.caption("💡 Seuil calculé automatiquement")
        fixed_threshold = 0.3  # Valeur par défaut si dynamique activé
    else:
        fixed_threshold = st.slider("Score threshold fixe", 0.0, 1.0, 0.3, step=0.05, help="Score minimum pour afficher les résultats")
    
    # Query expansion et traduction
    use_query_expansion = st.checkbox("Query expansion bilingue", value=True, help="Génère des variantes FR/EN de la requête")
    auto_translate = st.checkbox("Traduction FR→EN automatique", value=False, help="Traduit la requête en anglais pour expansion")
    
    # Rerank options
    always_rerank = st.checkbox("Toujours rerank", value=False, help="Appliquer toujours le rerank Cross-Encoder")
    use_rerank_if_below = st.checkbox("Rerank si score faible", value=False, help="Appliquer rerank si le meilleur score cosinus est en dessous d'un seuil")
    rerank_if_below = st.slider("Rerank si score <", 0.0, 1.0, 0.4, step=0.05, help="Seuil pour déclencher le rerank", disabled=not use_rerank_if_below) if use_rerank_if_below else None


# Main content
st.title("📸 Recherche Photos CLIP")
st.caption("Recherchez vos photos et vidéos depuis l'app Photos du Mac par description textuelle")

# Section 1: Récupération et analyse des photos
st.header("📸 Récupération et analyse des photos")

# Info sur les permissions
st.info("""
💡 **Note macOS** : Pour accéder aux photos depuis l'app Photos, vous devez :
1. Autoriser l'accès complet au disque dans **Réglages Système > Confidentialité et sécurité > Accès complet au disque**
2. Autoriser l'accès à Photos dans **Réglages Système > Confidentialité et sécurité > Photos**
3. Autoriser Terminal ou votre application Python
""")

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("📸 Récupérer et analyser les photos depuis Photos.app", type="primary", use_container_width=True):
        with st.spinner("📸 Récupération des photos depuis l'app Photos... Cela peut prendre quelques minutes..."):
            try:
                # Récupérer les photos depuis Photos.app
                photos_files, num_images, num_videos = get_photos_from_photos_app()
                
                if not photos_files:
                    st.error("❌ Aucune photo trouvée dans l'app Photos. Vérifiez les permissions d'accès.")
                else:
                    st.success(f"✅ {len(photos_files)} fichier(s) trouvé(s) ({num_images} image(s), {num_videos} vidéo(s))")
                    
                    # Créer un dossier temporaire pour les photos
                    temp_dir = tempfile.mkdtemp(prefix="photos_index_")
                    st.session_state.photos_temp_dir = temp_dir
                    
                    # Copier les fichiers vers le dossier temporaire (ou créer des liens symboliques)
                    # Pour économiser l'espace, on peut créer des liens symboliques
                    indexed_files = []
                    for photo_path in photos_files:
                        if os.path.exists(photo_path):
                            # Créer un lien symbolique vers le fichier original
                            filename = os.path.basename(photo_path)
                            link_path = os.path.join(temp_dir, filename)
                            try:
                                # Éviter les doublons en ajoutant un hash si nécessaire
                                if os.path.exists(link_path):
                                    # Utiliser un nom unique
                                    base, ext = os.path.splitext(filename)
                                    link_path = os.path.join(temp_dir, f"{base}_{hash(photo_path) % 10000}{ext}")
                                
                                os.symlink(photo_path, link_path)
                                indexed_files.append(link_path)
                            except Exception as e:
                                # Si symlink échoue, essayer de copier (mais plus lent)
                                try:
                                    shutil.copy2(photo_path, link_path)
                                    indexed_files.append(link_path)
                                except Exception:
                                    pass
                    
                    if indexed_files:
                        st.info(f"📁 {len(indexed_files)} fichier(s) préparé(s) pour l'indexation")
                        
                        # Lancer l'indexation automatiquement
                        st.info("🚀 Lancement de l'indexation automatique...")
                        
                        # Zone de logs avec suivi détaillé
                        log_container = st.container()
                        with log_container:
                            st.subheader("📊 Progression de l'indexation")
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            stats_text = st.empty()
                            log_expander = st.expander("📝 Logs détaillés", expanded=True)
                            
                            # Capturer les logs
                            log_buffer = io.StringIO()
                            
                            try:
                                # Étape 1: Charger les modèles
                                status_text.text("🔄 **Étape 1/3** : Chargement des modèles...")
                                progress_bar.progress(10)
                                embedder = load_clip_embedder()
                                captioner = load_blip_captioner() if generate_captions else None
                                status_text.text("✅ Modèles chargés")
                                
                                # Étape 2: Lancer l'indexation
                                status_text.text(f"🚀 **Étape 2/3** : Indexation en cours... ({len(indexed_files)} fichier(s))")
                                progress_bar.progress(50)
                                
                                # Afficher les logs en temps réel
                                console_logs_empty = st.empty()
                                
                                # Rediriger stdout vers Streamlit
                                old_stdout = sys.stdout
                                
                                # Créer un logger Streamlit simple
                                class StreamlitLogger:
                                    def __init__(self, container):
                                        self.container = container
                                        self.logs = []
                                    
                                    def write(self, message):
                                        if message.strip():
                                            self.logs.append(message.rstrip())
                                            if len(self.logs) > 100:
                                                self.logs = self.logs[-100:]
                                            try:
                                                self.container.code('\n'.join(self.logs), language='text')
                                            except:
                                                pass
                                    
                                    def flush(self):
                                        pass
                                
                                streamlit_logger = StreamlitLogger(console_logs_empty)
                                sys.stdout = streamlit_logger
                                
                                try:
                                    # Lancer l'indexation
                                    extract_and_index_multiple_dirs(
                                        data_dirs=[temp_dir],  # Utiliser le dossier temporaire
                                        output_index="index.faiss",
                                        output_metadata="metadata.json",
                                        frame_interval=2.0,
                                        max_frames_per_video=max_frames_per_video,
                                        use_quality_selection=use_quality_selection,
                                        use_multi_scale=use_multi_scale,
                                        generate_captions=generate_captions,
                                        batch_size=batch_size,
                                        embedder=embedder,
                                        captioner=captioner
                                    )
                                finally:
                                    # Restaurer stdout
                                    sys.stdout = old_stdout
                                
                                # Mettre à jour la progression
                                progress_bar.progress(100)
                                status_text.text("✅ **Indexation terminée!**")
                                
                                # Afficher le résultat
                                if os.path.exists("index.faiss"):
                                    index = faiss.read_index("index.faiss")
                                    with open("metadata.json", 'r', encoding='utf-8') as f:
                                        metadata = json.load(f)
                                    stats_text.success(f"✅ **Index créé**: {index.ntotal} embedding(s) indexé(s) ({len(metadata)} métadonnées)")
                                
                                # Recharger l'index
                                if load_index():
                                    st.session_state.photos_loaded = True
                                    st.success("✅ Photos analysées et index chargé avec succès!")
                                    st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ **Erreur lors de l'indexation**: {e}")
                                import traceback
                                with log_expander:
                                    st.text_area("Détails de l'erreur", traceback.format_exc(), height=200)
                    else:
                        st.warning("⚠️ Aucun fichier valide trouvé pour l'indexation")
                        
            except Exception as e:
                st.error(f"❌ Erreur lors de la récupération des photos: {e}")
                import traceback
                st.text_area("Détails de l'erreur", traceback.format_exc(), height=200)

with col2:
    if st.session_state.photos_loaded:
        st.success("✅ Photos chargées")
    if st.session_state.photos_temp_dir and os.path.exists(st.session_state.photos_temp_dir):
        st.caption(f"📁 Dossier temp: {st.session_state.photos_temp_dir}")

st.divider()

# Section 2: Recherche
st.header("🔍 Recherche par texte")

# Vérifier que l'index est chargé
if not st.session_state.index_loaded:
    if os.path.exists("index.faiss") and os.path.exists("metadata.json"):
        if st.button("📂 Charger l'index existant"):
            if load_index():
                st.success("✅ Index chargé")
                st.rerun()
    else:
        st.warning("⚠️ Aucun index trouvé. Veuillez d'abord cliquer sur 'Récupérer et analyser les photos'.")
else:
    # Historique des recherches
    if st.session_state.search_history:
        with st.expander("📜 Historique des recherches"):
            for i, hist_item in enumerate(reversed(st.session_state.search_history[-10:]), 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"{i}. {hist_item['query']}")
                    st.caption(f"   {len(hist_item.get('results', []))} résultat(s) - {hist_item.get('timestamp', '')}")
                with col2:
                    if st.button("🔄 Rejouer", key=f"replay_{i}"):
                        st.session_state.replay_query = hist_item['query']
                        st.rerun()
    
    # Champ de recherche
    query = st.text_input("🔍 Requête de recherche", placeholder="Ex: moi en wheeling, auditorium, chien qui court...", 
                          value=st.session_state.get('replay_query', ''))
    
    if 'replay_query' in st.session_state:
        del st.session_state.replay_query
    
    # Afficher les variantes si query expansion activé
    if use_query_expansion and query:
        from core.searcher import expand_query
        variants = expand_query(query, enable_fr=True, enable_en=auto_translate, auto_translate=auto_translate)
        with st.expander("📝 Variantes de requête utilisées"):
            for variant in variants:
                st.text(f"• {variant}")
    
    # Bouton de recherche
    if st.button("🔍 Rechercher", type="primary", use_container_width=True):
        if not query:
            st.warning("⚠️ Veuillez entrer une requête")
        else:
            with st.spinner("🔍 Recherche en cours..."):
                try:
                    # Charger les modèles si nécessaire
                    embedder = load_clip_embedder()
                    reranker = load_reranker() if (always_rerank or (use_rerank_if_below and rerank_if_below is not None)) else None
                    
                    # Déterminer le seuil
                    threshold_value = fixed_threshold if not use_dynamic_threshold else 0.0
                    
                    # Effectuer la recherche
                    from core.searcher import search
                    results = search(
                        query_text=query,
                        index=st.session_state.index,
                        metadata=st.session_state.metadata,
                        embedder=embedder,
                        top_k=top_k,
                        use_query_expansion=use_query_expansion,
                        auto_translate=auto_translate,
                        use_dynamic_threshold=use_dynamic_threshold,
                        fixed_threshold=threshold_value,
                        always_rerank=always_rerank,
                        rerank_if_below=rerank_if_below if (use_rerank_if_below and rerank_if_below is not None and not always_rerank) else None,
                        reranker=reranker,
                        use_captions=True
                    )
                    
                    # Sauvegarder les résultats et l'historique
                    st.session_state.last_results = results
                    st.session_state.search_history.append({
                        "query": query,
                        "results": results,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "options": {
                            "top_k": top_k,
                            "use_query_expansion": use_query_expansion,
                            "auto_translate": auto_translate,
                            "use_dynamic_threshold": use_dynamic_threshold,
                            "always_rerank": always_rerank,
                            "rerank_if_below": rerank_if_below
                        }
                    })
                    
                    if not results:
                        st.warning("⚠️ Aucun résultat pertinent trouvé")
                    else:
                        st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
                
                except Exception as e:
                    st.error(f"❌ Erreur lors de la recherche: {e}")
                    import traceback
                    st.text_area("Détails de l'erreur", traceback.format_exc(), height=200)
    
    # Afficher les résultats
    if st.session_state.last_results:
        st.divider()
        st.subheader(f"📊 Résultats ({len(st.session_state.last_results)} résultats)")
        
        # Grouper les résultats par fichier
        unique_results = {}
        for result in st.session_state.last_results:
            file_path = result.get("path", "")
            score = result.get("score", 0.0)
            meta = result.get("meta", {})
            
            if file_path not in unique_results or score > unique_results[file_path].get("score", 0.0):
                unique_results[file_path] = result
        
        # Trier par score décroissant
        sorted_results = sorted(unique_results.values(), key=lambda x: x.get("score", 0.0), reverse=True)
        
        # Afficher en grille responsive
        cols_per_row = 3
        for i in range(0, len(sorted_results), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(sorted_results):
                    result = sorted_results[i + j]
                    file_path = result.get("path", "")
                    score = result.get("score", 0.0)
                    cosine_score = result.get("cosine_score", score)
                    meta = result.get("meta", {})
                    
                    with col:
                        st.markdown(f"**{os.path.basename(file_path)}**")
                        
                        # Afficher la miniature ou preview
                        if meta.get('media_type') == 'image':
                            thumbnail = make_thumbnail(file_path)
                            if thumbnail:
                                st.image(thumbnail, use_container_width=True)
                        else:  # video
                            preview = get_video_preview(file_path)
                            if preview:
                                st.image(preview, use_container_width=True)
                        
                        # Score
                        if abs(score - cosine_score) > 0.001:
                            st.caption(f"Score Cross-Encoder: **{score:.3f}** | FAISS: {cosine_score:.3f}")
                        else:
                            st.caption(f"Score: **{score:.3f}** ({human_readable_score(score)})")
                        
                        # Caption si disponible
                        caption = meta.get('caption', '')
                        if caption and caption.strip() and caption.strip().lower() != "unknown":
                            st.caption(f"📝 {caption}")
                        
                        # Chemin
                        st.caption(f"📍 {file_path}")
                        
                        # Bouton pour ouvrir dans Finder
                        if st.button("📂 Ouvrir dans Finder", key=f"open_{i+j}", use_container_width=True):
                            if open_in_finder(file_path):
                                st.success("✅ Fichier ouvert dans Finder")
                        
                        st.divider()

