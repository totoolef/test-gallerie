"""
Module d'indexation pour extraire les embeddings des médias et créer l'index FAISS.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

import json
import glob
from pathlib import Path
from typing import List, Tuple
import numpy as np
import faiss
from PIL import Image
import heapq

# Import cv2 EN DERNIER pour éviter les conflits
import cv2

from .clip_utils import CLIPEmbedder
from .captioner import BLIPCaptioner, get_captioner

# Formats supportés
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}


def get_media_files(data_dir: str) -> Tuple[List[str], List[str]]:
    """
    Récupère tous les fichiers média du dossier data/.
    
    Args:
        data_dir: Chemin vers le dossier contenant les médias
        
    Returns:
        Tuple (liste_images, liste_vidéos)
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Le dossier {data_dir} n'existe pas")
    
    images = []
    videos = []
    
    for ext in IMAGE_EXTENSIONS:
        images.extend(glob.glob(str(data_path / '**' / f'*{ext}'), recursive=True))
        images.extend(glob.glob(str(data_path / '**' / f'*{ext.upper()}'), recursive=True))
    
    for ext in VIDEO_EXTENSIONS:
        videos.extend(glob.glob(str(data_path / '**' / f'*{ext}'), recursive=True))
        videos.extend(glob.glob(str(data_path / '**' / f'*{ext.upper()}'), recursive=True))
    
    return images, videos


def detect_scene_changes(video_path: str, stride: int = 1, diff_threshold: float = 0.3) -> List[int]:
    """
    Détecte les changements de scène dans une vidéo.
    
    Args:
        video_path: Chemin vers la vidéo
        stride: Pas entre les frames à analyser (défaut: 1 pour toutes les frames)
        diff_threshold: Seuil de différence moyenne absolue pour détecter un changement (défaut: 0.3)
        
    Returns:
        Liste d'indices de frames où un changement de scène est détecté
    """
    scene_changes = []
    prev_frame = None
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"⚠️  Impossible d'ouvrir la vidéo: {video_path}")
            return []
        
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Ne traiter que les frames selon le stride
            if frame_idx % stride == 0:
                # Convertir en grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # Calculer la différence absolue
                    diff = cv2.absdiff(gray, prev_frame)
                    mean_diff = np.mean(diff) / 255.0  # Normaliser entre 0 et 1
                    
                    # Si la différence dépasse le seuil, c'est un changement de scène
                    if mean_diff > diff_threshold:
                        scene_changes.append(frame_idx)
                
                prev_frame = gray
            
            frame_idx += 1
        
        cap.release()
        
        return scene_changes
        
    except Exception as e:
        print(f"⚠️  Erreur lors de la détection de changements de scène: {e}")
        return []


def select_quality_frames(video_path: str, n_frames: int = 10, use_scene_diversity: bool = True) -> List[Image.Image]:
    """
    Sélectionne les N meilleures frames d'une vidéo basées sur la qualité (Laplacian variance)
    et la diversité de scènes (changements de scène détectés).
    
    Utilise un heap pour ne garder que les N meilleures frames en mémoire,
    évitant ainsi les problèmes de mémoire avec les longues vidéos.
    
    Args:
        video_path: Chemin vers la vidéo
        n_frames: Nombre de frames à sélectionner (les meilleures)
        use_scene_diversity: Si True, favorise la diversité de scènes (défaut: True)
        
    Returns:
        Liste d'images PIL (les meilleures frames, diversifiées par scène)
    """
    # Utiliser un heap min pour garder seulement les N meilleures frames
    heap = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"⚠️  Impossible d'ouvrir la vidéo: {video_path}")
            return []
        
        # Obtenir les infos de la vidéo pour afficher la progression
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if total_frames > 0 and fps > 0:
            duration = total_frames / fps
            print(f"    📊 Analyse de la qualité des frames ({total_frames} frames, {duration:.1f}s)...")
        else:
            print(f"    📊 Analyse de la qualité des frames...")
        
        # Détecter les changements de scène si demandé
        scene_changes = []
        if use_scene_diversity:
            print(f"    🎬 Détection des changements de scène...")
            scene_changes = detect_scene_changes(video_path, stride=max(1, total_frames // 100), diff_threshold=0.3)
            print(f"    ✅ {len(scene_changes)} changement(s) de scène détecté(s)")
        
        frame_count = 0
        scene_change_indices = set(scene_changes) if scene_changes else set()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                # Convertir en niveaux de gris pour calculer la variance Laplacienne
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # La variance Laplacienne mesure la netteté (plus élevé = plus net)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                # Bonus pour les frames de changement de scène (diversité)
                quality_score = laplacian_var
                if use_scene_diversity and frame_count in scene_change_indices:
                    quality_score *= 1.5  # Bonus de 50% pour les changements de scène
                
                # Convertir en RGB pour PIL
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Utiliser un heap min pour garder seulement les N meilleures frames
                if len(heap) < n_frames:
                    # On a encore de la place, ajouter directement
                    heapq.heappush(heap, (-quality_score, frame_count, pil_image))
                else:
                    # Vérifier si cette frame est meilleure que la pire du heap
                    min_neg_score, _, _ = heap[0]
                    if quality_score > -min_neg_score:
                        # Remplacer la pire frame par cette meilleure
                        heapq.heapreplace(heap, (-quality_score, frame_count, pil_image))
                
                frame_count += 1
                
                # Afficher la progression tous les 100 frames pour les longues vidéos
                if frame_count % 100 == 0:
                    print(f"      Traité {frame_count} frames...", end='\r')
                
            except Exception as e:
                print(f"⚠️  Erreur lors de l'analyse d'une frame: {e}")
                continue
        
        cap.release()
        
        # Extraire les frames du heap et les trier par score décroissant
        frames_with_scores = sorted(heap, key=lambda x: -x[0], reverse=True)
        selected_frames = [f[2] for f in frames_with_scores]
        
        print(f"    ✅ Sélectionné {len(selected_frames)} frame(s) sur {frame_count} analysée(s)")
        return selected_frames
        
    except Exception as e:
        print(f"⚠️  Erreur lors du traitement de la vidéo {video_path}: {e}")
        return []


def extract_frames_from_video(video_path: str, frame_interval: float = 2.0, use_quality_selection: bool = True) -> List[Image.Image]:
    """
    Extrait des frames d'une vidéo.
    Utilise la sélection intelligente par qualité si use_quality_selection=True,
    sinon utilise un échantillonnage régulier.
    
    Args:
        video_path: Chemin vers la vidéo
        frame_interval: Intervalle en secondes entre chaque frame (si use_quality_selection=False)
        use_quality_selection: Si True, utilise la sélection par qualité (recommandé)
        
    Returns:
        Liste d'images PIL
    """
    if use_quality_selection:
        # Utiliser la sélection intelligente par qualité
        # Estimer le nombre de frames à sélectionner basé sur la durée de la vidéo
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count_total / fps if fps > 0 else 0
        cap.release()
        
        # Sélectionner environ 1 frame toutes les 2 secondes
        n_frames = max(5, min(int(duration / frame_interval), 20))  # Entre 5 et 20 frames
        return select_quality_frames(video_path, n_frames=n_frames)
    else:
        # Méthode classique : échantillonnage régulier
        frames = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"⚠️  Impossible d'ouvrir la vidéo: {video_path}")
                return frames
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # FPS par défaut
            
            frame_step = int(fps * frame_interval)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_step == 0:
                    try:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(frame_rgb)
                        frames.append(pil_image)
                    except Exception as e:
                        print(f"⚠️  Erreur lors de l'extraction d'une frame: {e}")
                        continue
                
                frame_count += 1
            
            cap.release()
            
        except Exception as e:
            print(f"⚠️  Erreur lors du traitement de la vidéo {video_path}: {e}")
        
        return frames


def encode_image_adaptive(image: Image.Image, embedder: CLIPEmbedder, n_crops: int = 5) -> np.ndarray:
    """
    Encode une image avec multi-échelle adaptative (pondéré par variance locale).
    Génère un crop central + crops autour des zones à plus forte variance.
    
    Args:
        image: Image PIL à encoder
        embedder: Instance de CLIPEmbedder
        n_crops: Nombre de crops à générer (défaut: 5)
        
    Returns:
        Embedding numpy (moyenne pondérée des embeddings des crops)
    """
    w, h = image.size
    
    # Convertir en grayscale pour calculer la variance
    # cv2 et numpy sont déjà importés au début du fichier
    
    # Convertir PIL en numpy pour OpenCV
    img_array = np.array(image.convert('RGB'))
    img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Calculer la carte de variance (fenêtre glissante)
    # Utiliser un kernel pour calculer la variance locale
    kernel_size = min(32, w // 8, h // 8)
    kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
    
    # Moyenne locale
    mean_local = cv2.filter2D(img_gray.astype(np.float32), -1, kernel)
    
    # Variance locale
    sqr_mean = cv2.filter2D((img_gray.astype(np.float32) ** 2), -1, kernel)
    variance_map = sqr_mean - (mean_local ** 2)
    
    # Générer les crops
    crops = []
    crop_weights = []
    
    # 1. Crop central (50% de l'image) - poids fixe
    center_crop = image.crop((w//4, h//4, 3*w//4, 3*h//4))
    crops.append(center_crop)
    crop_weights.append(1.0)  # Poids de base pour le centre
    
    # 2. Trouver les zones de haute variance pour les autres crops
    # Diviser l'image en grille et prendre les zones avec variance élevée
    grid_size = 3
    cell_w = w // grid_size
    cell_h = h // grid_size
    
    variance_cells = []
    for i in range(grid_size):
        for j in range(grid_size):
            x1 = i * cell_w
            y1 = j * cell_h
            x2 = min((i + 1) * cell_w, w)
            y2 = min((j + 1) * cell_h, h)
            
            # Variance moyenne de cette cellule
            cell_variance = np.mean(variance_map[y1:y2, x1:x2])
            variance_cells.append((cell_variance, (x1, y1, x2, y2)))
    
    # Trier par variance décroissante et prendre les meilleures
    variance_cells.sort(key=lambda x: x[0], reverse=True)
    
    # Prendre les n_crops - 1 meilleures zones (en plus du centre)
    for i in range(min(n_crops - 1, len(variance_cells))):
        _, (x1, y1, x2, y2) = variance_cells[i]
        crop = image.crop((x1, y1, x2, y2))
        crops.append(crop)
        # Poids proportionnel à la variance
        weight = variance_cells[i][0] / (np.max(variance_map) + 1e-6)
        crop_weights.append(max(0.1, weight))  # Minimum 0.1 pour éviter les poids nuls
    
    # Encoder chaque crop en batch si possible
    embeddings = []
    valid_weights = []
    
    try:
        # Encoder en batch si possible
        embeddings_batch = embedder.encode_images_batch(crops)
        for i, embedding in enumerate(embeddings_batch):
            if embedding is not None and embedding.size > 0:
                embeddings.append(embedding)
                valid_weights.append(crop_weights[i] if i < len(crop_weights) else 1.0)
    except Exception:
        # Fallback: encoder un par un
        for i, crop in enumerate(crops):
            try:
                embedding = embedder.encode_image(crop)
                if embedding is not None and embedding.size > 0:
                    embeddings.append(embedding)
                    valid_weights.append(crop_weights[i] if i < len(crop_weights) else 1.0)
            except Exception:
                continue
    
    if not embeddings:
        # Fallback : encoder l'image complète
        return embedder.encode_image(image)
    
    # Moyenne pondérée des embeddings
    embeddings_array = np.array(embeddings)
    weights_array = np.array(valid_weights)
    
    # Normaliser les poids
    weights_array = weights_array / (np.sum(weights_array) + 1e-6)
    
    # Moyenne pondérée
    weighted_embedding = np.average(embeddings_array, axis=0, weights=weights_array)
    
    # Re-normaliser (important pour cosine similarity)
    norm = np.linalg.norm(weighted_embedding)
    if norm > 0:
        weighted_embedding = weighted_embedding / norm
    
    return weighted_embedding.astype('float32')


def encode_image_multi_scale(image: Image.Image, embedder: CLIPEmbedder) -> np.ndarray:
    """
    Alias pour encode_image_adaptive (rétrocompatibilité).
    """
    return encode_image_adaptive(image, embedder, n_crops=5)


def process_image(image_path: str, embedder: CLIPEmbedder, use_multi_scale: bool = True) -> np.ndarray:
    """
    Traite une image et retourne son embedding.
    Utilise l'augmentation multi-échelle si use_multi_scale=True (recommandé).
    
    Args:
        image_path: Chemin vers l'image
        embedder: Instance de CLIPEmbedder
        use_multi_scale: Si True, utilise l'augmentation multi-échelle
        
    Returns:
        Embedding numpy (ou None en cas d'erreur)
    """
    try:
        if not os.path.exists(image_path):
            print(f"⚠️  Fichier introuvable: {image_path}")
            return None
        
        # Ouvrir l'image
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Vérifier que l'image est valide
        if image.size[0] == 0 or image.size[1] == 0:
            print(f"⚠️  Image invalide (taille 0): {image_path}")
            image.close()
            return None
        
        # Encoder l'image (avec ou sans augmentation multi-échelle adaptative)
        if use_multi_scale:
            embedding = encode_image_adaptive(image, embedder, n_crops=5)
        else:
            embedding = embedder.encode_image(image)
        
        image.close()
        
        # Nettoyage : s'assurer que c'est bien float32 et valide
        if embedding is not None:
            embedding = embedding.astype('float32')
            # Vérifier qu'il n'y a pas de NaN ou Inf
            if not np.all(np.isfinite(embedding)):
                print(f"⚠️  Embedding contient des valeurs invalides pour {image_path}")
                return None
        
        return embedding
        
    except Exception as e:
        print(f"⚠️  Erreur lors du traitement de {image_path}: {e}")
        return None


def process_video(video_path: str, embedder: CLIPEmbedder, frame_interval: float = 2.0, use_quality_selection: bool = True) -> List[np.ndarray]:
    """
    Traite une vidéo et retourne les embeddings de ses frames.
    Utilise la sélection intelligente par qualité si use_quality_selection=True.
    
    Args:
        video_path: Chemin vers la vidéo
        embedder: Instance de CLIPEmbedder
        frame_interval: Intervalle en secondes entre chaque frame (si use_quality_selection=False)
        use_quality_selection: Si True, utilise la sélection par qualité
        
    Returns:
        Liste d'embeddings numpy
    """
    try:
        frames = extract_frames_from_video(video_path, frame_interval, use_quality_selection=use_quality_selection)
        if not frames:
            return []
        
        embeddings = []
        for frame in frames:
            try:
                embedding = embedder.encode_image(frame)
                if embedding is not None:
                    # Nettoyage : s'assurer que c'est bien float32 et valide
                    embedding = embedding.astype('float32')
                    if np.all(np.isfinite(embedding)):
                        embeddings.append(embedding)
                    else:
                        print(f"⚠️  Embedding invalide pour une frame de {video_path}")
            except Exception as e:
                print(f"⚠️  Erreur lors de l'encodage d'une frame: {e}")
                continue
        
        return embeddings
        
    except Exception as e:
        print(f"⚠️  Erreur lors du traitement de {video_path}: {e}")
        return []


def extract_and_index(data_dir: str = "data/", 
                      output_index: str = "index.faiss",
                      output_metadata: str = "metadata.json",
                      frame_interval: float = 2.0,
                      model_name: str = "openai/clip-vit-large-patch14",
                      embedder: CLIPEmbedder = None,
                      generate_captions: bool = True,
                      captioner: BLIPCaptioner = None):
    """
    Extrait les embeddings de tous les médias et crée l'index FAISS.
    
    Args:
        data_dir: Dossier contenant les médias
        output_index: Chemin vers le fichier d'index FAISS
        output_metadata: Chemin vers le fichier de métadonnées JSON
        frame_interval: Intervalle en secondes entre chaque frame vidéo
        model_name: Nom du modèle CLIP à utiliser
        embedder: Instance de CLIPEmbedder (optionnel, sera créé si None)
        generate_captions: Si True, génère des légendes automatiques avec BLIP
        captioner: Instance de BLIPCaptioner (optionnel, sera créé si None et generate_captions=True)
    """
    print("🚀 Démarrage de l'extraction des embeddings...")
    
    # Charger l'embedder si nécessaire
    if embedder is None:
        try:
            from .clip_utils import get_embedder
            embedder = get_embedder(model_name=model_name)
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Charger le captioner si nécessaire
    if generate_captions and captioner is None:
        try:
            captioner = get_captioner()
            print("✅ Captioner BLIP initialisé pour génération de légendes")
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement du captioner: {e}")
            print("   Continuation sans génération de légendes...")
            generate_captions = False
    
    # Rechercher les fichiers média
    print(f"📁 Recherche des fichiers dans {data_dir}...")
    try:
        images, videos = get_media_files(data_dir)
    except Exception as e:
        print(f"❌ Erreur lors de la recherche des fichiers: {e}")
        return
    
    total_media = len(images) + len(videos)
    print(f"✅ Trouvé {len(images)} image(s) et {len(videos)} vidéo(s)")
    
    if total_media == 0:
        print("❌ Aucun fichier média trouvé. Arrêt.")
        return
    
    all_embeddings = []
    metadata = []
    
    # Traiter les images
    if images:
        print(f"\n🖼️  Traitement des images ({len(images)} fichier(s))...")
        
        for idx, image_path in enumerate(images, 1):
            print(f"  [{idx}/{len(images)}] {os.path.basename(image_path)}")
            try:
                embedding = process_image(image_path, embedder, use_multi_scale=True)
                if embedding is not None and embedding.size > 0:
                    all_embeddings.append(embedding)
                    
                    # Générer la légende si demandé
                    caption = ""
                    if generate_captions:
                        try:
                            image = Image.open(image_path)
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            # Redimensionner pour accélérer BLIP et stabiliser sur CPU
                            max_side = 768
                            if max(image.size) > max_side:
                                ratio = max_side / float(max(image.size))
                                new_size = (int(image.size[0]*ratio), int(image.size[1]*ratio))
                                image = image.resize(new_size)
                            # Timeout plus long (30 secondes) pour éviter les "unknown"
                            caption = captioner.generate_caption(image, timeout=30.0)
                            image.close()
                            
                            # Si BLIP retourne "unknown" ou vide, utiliser le nom de fichier
                            if not caption or caption.strip().lower() == "unknown":
                                cleaned_name = os.path.splitext(os.path.basename(image_path))[0].replace('_',' ').replace('-',' ')
                                caption = cleaned_name
                                print(f"      📝 Caption (fallback): {caption}")
                            else:
                                print(f"      📝 Caption: {caption}")
                        except Exception as e:
                            print(f"      ⚠️  Erreur lors de la génération de la légende: {e}")
                            # Fallback: nom de fichier nettoyé
                            cleaned_name = os.path.splitext(os.path.basename(image_path))[0].replace('_',' ').replace('-',' ')
                            caption = cleaned_name
                            print(f"      📝 Caption (fallback après erreur): {caption}")
                    else:
                        # Même sans generate_captions, utiliser le nom de fichier
                        cleaned_name = os.path.splitext(os.path.basename(image_path))[0].replace('_',' ').replace('-',' ')
                        caption = cleaned_name
                    
                    metadata.append({
                        "file_path": os.path.abspath(image_path),
                        "media_type": "image",
                        "frame_index": None,
                        "caption": caption
                    })
                else:
                    print(f"⚠️  Embedding vide pour {image_path}, ignoré")
            except Exception as e:
                print(f"⚠️  Exception lors du traitement de {image_path}: {e}")
                continue
    
    # Traiter les vidéos
    if videos:
        print(f"\n🎬 Traitement des vidéos ({len(videos)} fichier(s))...")
        
        for idx, video_path in enumerate(videos, 1):
            print(f"  [{idx}/{len(videos)}] {os.path.basename(video_path)}")
            try:
                embeddings = process_video(video_path, embedder, frame_interval, use_quality_selection=True)
                for frame_idx, embedding in enumerate(embeddings):
                    if embedding is not None and embedding.size > 0:
                        all_embeddings.append(embedding)
                        
                        # Pour les vidéos, on ne génère pas de légende par frame (trop long)
                        # On peut ajouter une légende générale pour la vidéo si nécessaire
                        # Caption par défaut pour les vidéos: nom de fichier nettoyé
                        video_name = os.path.splitext(os.path.basename(video_path))[0].replace('_',' ').replace('-',' ')
                        default_video_caption = f"video: {video_name}"
                        metadata.append({
                            "file_path": os.path.abspath(video_path),
                            "media_type": "video",
                            "frame_index": frame_idx,
                            "caption": default_video_caption
                        })
            except Exception as e:
                print(f"⚠️  Exception lors du traitement de {video_path}: {e}")
                continue
    
    # Vérifier qu'on a des embeddings
    if not all_embeddings:
        print("❌ Aucun embedding extrait. Arrêt.")
        return
    
    # Créer l'index FAISS
    print(f"\n📊 Création de l'index FAISS avec {len(all_embeddings)} embedding(s)...")
    try:
        embeddings_array = np.array(all_embeddings).astype('float32')
        embedding_dim = embeddings_array.shape[1]
        
        # Normaliser les embeddings pour cosine similarity (L2 normalisation)
        print("   🔄 Normalisation L2 des embeddings pour cosine similarity...")
        faiss.normalize_L2(embeddings_array)
        
        # Utiliser IndexFlatIP pour cosine similarity (Inner Product = Cosine quand normalisé)
        # IndexFlatIP est plus approprié que IndexFlatL2 pour les embeddings CLIP normalisés
        index = faiss.IndexFlatIP(embedding_dim)
        index.add(embeddings_array)
        
        print(f"💾 Sauvegarde de l'index dans {output_index}...")
        faiss.write_index(index, output_index)
        
        print(f"💾 Sauvegarde des métadonnées dans {output_metadata}...")
        with open(output_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Indexation terminée!")
        print(f"   - {len(all_embeddings)} embedding(s) indexé(s)")
        print(f"   - Dimension: {embedding_dim}")
        print(f"   - Index sauvegardé: {output_index}")
        print(f"   - Métadonnées sauvegardées: {output_metadata}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'index: {e}")
        import traceback
        traceback.print_exc()


def save_index_backup(index_path: str = "index.faiss",
                      metadata_path: str = "metadata.json",
                      backup_dir: str = "backups"):
    """
    Sauvegarde l'index et les métadonnées dans un dossier de backup.
    
    Args:
        index_path: Chemin vers le fichier d'index FAISS
        metadata_path: Chemin vers le fichier de métadonnées
        backup_dir: Dossier de backup (sera créé si nécessaire)
    """
    import shutil
    from datetime import datetime
    
    if not os.path.exists(index_path):
        print(f"❌ L'index {index_path} n'existe pas")
        return False
    
    if not os.path.exists(metadata_path):
        print(f"❌ Les métadonnées {metadata_path} n'existent pas")
        return False
    
    # Créer le dossier de backup
    os.makedirs(backup_dir, exist_ok=True)
    
    # Créer un nom de fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_index = os.path.join(backup_dir, f"index_{timestamp}.faiss")
    backup_metadata = os.path.join(backup_dir, f"metadata_{timestamp}.json")
    
    try:
        # Copier les fichiers
        shutil.copy2(index_path, backup_index)
        shutil.copy2(metadata_path, backup_metadata)
        
        print(f"✅ Backup créé avec succès:")
        print(f"   - Index: {backup_index}")
        print(f"   - Métadonnées: {backup_metadata}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False


def restore_index_backup(backup_index_path: str,
                         backup_metadata_path: str,
                         index_path: str = "index.faiss",
                         metadata_path: str = "metadata.json"):
    """
    Restaure l'index et les métadonnées depuis un backup.
    
    Args:
        backup_index_path: Chemin vers le fichier d'index de backup
        backup_metadata_path: Chemin vers le fichier de métadonnées de backup
        index_path: Chemin de destination pour l'index
        metadata_path: Chemin de destination pour les métadonnées
    """
    import shutil
    
    if not os.path.exists(backup_index_path):
        print(f"❌ Le backup d'index {backup_index_path} n'existe pas")
        return False
    
    if not os.path.exists(backup_metadata_path):
        print(f"❌ Le backup de métadonnées {backup_metadata_path} n'existe pas")
        return False
    
    try:
        # Sauvegarder les fichiers existants si nécessaire
        if os.path.exists(index_path):
            save_index_backup(index_path, metadata_path)
        
        # Restaurer les fichiers
        shutil.copy2(backup_index_path, index_path)
        shutil.copy2(backup_metadata_path, metadata_path)
        
        print(f"✅ Index restauré avec succès:")
        print(f"   - Index: {index_path}")
        print(f"   - Métadonnées: {metadata_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {e}")
        return False


def extract_and_index_multiple_dirs(data_dirs: List[str],
                                     output_index: str = "index.faiss",
                                     output_metadata: str = "metadata.json",
                                     frame_interval: float = 2.0,
                                     max_frames_per_video: int = 10,
                                     use_quality_selection: bool = True,
                                     use_multi_scale: bool = True,
                                     generate_captions: bool = True,
                                     batch_size: int = 32,
                                     model_name: str = "openai/clip-vit-large-patch14",
                                     embedder: CLIPEmbedder = None,
                                     captioner: BLIPCaptioner = None):
    """
    Extrait les embeddings de plusieurs dossiers et crée l'index FAISS.
    
    Args:
        data_dirs: Liste de dossiers contenant les médias
        output_index: Chemin vers le fichier d'index FAISS
        output_metadata: Chemin vers le fichier de métadonnées JSON
        frame_interval: Intervalle en secondes entre chaque frame vidéo
        max_frames_per_video: Nombre maximum de frames par vidéo
        use_quality_selection: Si True, utilise la sélection intelligente des frames
        use_multi_scale: Si True, utilise l'augmentation multi-échelle pour les images
        generate_captions: Si True, génère des légendes automatiques avec BLIP
        batch_size: Taille du batch pour le traitement des images
        model_name: Nom du modèle CLIP à utiliser
        embedder: Instance de CLIPEmbedder (optionnel, sera créé si None)
        captioner: Instance de BLIPCaptioner (optionnel, sera créé si None et generate_captions=True)
    """
    print("🚀 Démarrage de l'extraction des embeddings depuis plusieurs dossiers...")
    
    # Charger l'embedder si nécessaire
    if embedder is None:
        try:
            from .clip_utils import get_embedder
            embedder = get_embedder(model_name=model_name)
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Charger le captioner si nécessaire
    if generate_captions and captioner is None:
        try:
            captioner = get_captioner()
            print("✅ Captioner BLIP initialisé pour génération de légendes")
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement du captioner: {e}")
            print("   Continuation sans génération de légendes...")
            generate_captions = False
    
    # Collecter tous les fichiers média de tous les dossiers
    all_images = []
    all_videos = []
    
    for data_dir in data_dirs:
        print(f"📁 Recherche des fichiers dans {data_dir}...")
        try:
            images, videos = get_media_files(data_dir)
            all_images.extend(images)
            all_videos.extend(videos)
            print(f"   ✅ Trouvé {len(images)} image(s) et {len(videos)} vidéo(s)")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la recherche dans {data_dir}: {e}")
            continue
    
    total_media = len(all_images) + len(all_videos)
    print(f"\n✅ Total: {len(all_images)} image(s) et {len(all_videos)} vidéo(s)")
    
    if total_media == 0:
        print("❌ Aucun fichier média trouvé. Arrêt.")
        return
    
    all_embeddings = []
    metadata = []
    
    # Traiter les images par batch
    if all_images:
        print(f"\n🖼️  Traitement des images ({len(all_images)} fichier(s))...")
        
        for batch_start in range(0, len(all_images), batch_size):
            batch_images = all_images[batch_start:batch_start + batch_size]
            batch_embeddings = []
            batch_metadata = []
            
            for idx, image_path in enumerate(batch_images, batch_start + 1):
                print(f"  [{idx}/{len(all_images)}] {os.path.basename(image_path)}")
                try:
                    embedding = process_image(image_path, embedder, use_multi_scale=use_multi_scale)
                    if embedding is not None and embedding.size > 0:
                        batch_embeddings.append(embedding)
                        
                        # Générer la légende si demandé
                        caption = ""
                        if generate_captions:
                            try:
                                image = Image.open(image_path)
                                if image.mode != 'RGB':
                                    image = image.convert('RGB')
                                # Redimensionner pour accélérer BLIP et stabiliser sur CPU
                                max_side = 768
                                if max(image.size) > max_side:
                                    ratio = max_side / float(max(image.size))
                                    new_size = (int(image.size[0]*ratio), int(image.size[1]*ratio))
                                    image = image.resize(new_size)
                                # Timeout plus long (30 secondes) pour éviter les "unknown"
                                caption = captioner.generate_caption(image, timeout=30.0)
                                image.close()
                                
                                # Si BLIP retourne "unknown" ou vide, utiliser le nom de fichier
                                if not caption or caption.strip().lower() == "unknown":
                                    cleaned_name = os.path.splitext(os.path.basename(image_path))[0].replace('_',' ').replace('-',' ')
                                    caption = cleaned_name
                                    print(f"      📝 Caption (fallback): {caption}")
                                else:
                                    print(f"      📝 Caption: {caption}")
                            except Exception as e:
                                print(f"      ⚠️  Erreur lors de la génération de la légende: {e}")
                                # Fallback: nom de fichier nettoyé
                                cleaned_name = os.path.splitext(os.path.basename(image_path))[0].replace('_',' ').replace('-',' ')
                                caption = cleaned_name
                                print(f"      📝 Caption (fallback après erreur): {caption}")
                        else:
                            # Même sans generate_captions, utiliser le nom de fichier
                            cleaned_name = os.path.splitext(os.path.basename(image_path))[0].replace('_',' ').replace('-',' ')
                            caption = cleaned_name
                        
                        batch_metadata.append({
                            "file_path": os.path.abspath(image_path),
                            "media_type": "image",
                            "frame_index": None,
                            "caption": caption
                        })
                    else:
                        print(f"⚠️  Embedding vide pour {image_path}, ignoré")
                except Exception as e:
                    print(f"⚠️  Exception lors du traitement de {image_path}: {e}")
                    continue
            
            all_embeddings.extend(batch_embeddings)
            metadata.extend(batch_metadata)
    
    # Traiter les vidéos
    if all_videos:
        print(f"\n🎬 Traitement des vidéos ({len(all_videos)} fichier(s))...")
        
        for idx, video_path in enumerate(all_videos, 1):
            print(f"  [{idx}/{len(all_videos)}] {os.path.basename(video_path)}")
            try:
                # Extraire les frames
                if use_quality_selection:
                    # Utiliser la sélection intelligente avec max_frames_per_video
                    frames = select_quality_frames(video_path, n_frames=max_frames_per_video)
                else:
                    # Méthode classique : échantillonnage régulier
                    frames = extract_frames_from_video(video_path, frame_interval, use_quality_selection=False)
                    # Limiter à max_frames_per_video
                    if len(frames) > max_frames_per_video:
                        frames = frames[:max_frames_per_video]
                
                # Encoder les frames
                for frame_idx, frame in enumerate(frames):
                    try:
                        embedding = embedder.encode_image(frame)
                        if embedding is not None:
                            embedding = embedding.astype('float32')
                            if np.all(np.isfinite(embedding)):
                                all_embeddings.append(embedding)
                                # Caption par défaut pour les vidéos: nom de fichier nettoyé
                                video_name = os.path.splitext(os.path.basename(video_path))[0].replace('_',' ').replace('-',' ')
                                default_video_caption = f"video: {video_name}"
                                metadata.append({
                                    "file_path": os.path.abspath(video_path),
                                    "media_type": "video",
                                    "frame_index": frame_idx,
                                    "caption": default_video_caption
                                })
                    except Exception as e:
                        print(f"      ⚠️  Erreur lors de l'encodage d'une frame: {e}")
                        continue
            except Exception as e:
                print(f"⚠️  Exception lors du traitement de {video_path}: {e}")
                continue
    
    # Vérifier qu'on a des embeddings
    if not all_embeddings:
        print("❌ Aucun embedding extrait. Arrêt.")
        return
    
    # Créer l'index FAISS
    print(f"\n📊 Création de l'index FAISS avec {len(all_embeddings)} embedding(s)...")
    try:
        embeddings_array = np.array(all_embeddings).astype('float32')
        embedding_dim = embeddings_array.shape[1]
        
        # Normaliser les embeddings pour cosine similarity (L2 normalisation)
        print("   🔄 Normalisation L2 des embeddings pour cosine similarity...")
        faiss.normalize_L2(embeddings_array)
        
        # Utiliser IndexFlatIP pour cosine similarity
        index = faiss.IndexFlatIP(embedding_dim)
        index.add(embeddings_array)
        
        print(f"💾 Sauvegarde de l'index dans {output_index}...")
        faiss.write_index(index, output_index)
        
        print(f"💾 Sauvegarde des métadonnées dans {output_metadata}...")
        with open(output_metadata, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Indexation terminée!")
        print(f"   - {len(all_embeddings)} embedding(s) indexé(s)")
        print(f"   - Dimension: {embedding_dim}")
        print(f"   - Index sauvegardé: {output_index}")
        print(f"   - Métadonnées sauvegardées: {output_metadata}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'index: {e}")
        import traceback
        traceback.print_exc()

