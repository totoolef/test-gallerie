"""
Module de recherche pour rechercher dans les médias indexés via une requête texte.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

import json
import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional

from .clip_utils import CLIPEmbedder
from .reranker import CrossEncoderReranker, get_reranker, rerank_results
from .filters import filter_metadata


def load_index_and_metadata(index_path: str = "index.faiss", 
                            metadata_path: str = "metadata.json") -> Tuple[faiss.Index, List[Dict]]:
    """
    Charge l'index FAISS et les métadonnées.
    
    Args:
        index_path: Chemin vers le fichier d'index FAISS
        metadata_path: Chemin vers le fichier de métadonnées JSON
        
    Returns:
        Tuple (index FAISS, liste de métadonnées)
    """
    if not os.path.exists(index_path):
        print("\n" + "="*80)
        print("❌ ERREUR: L'index FAISS n'existe pas encore")
        print("="*80)
        print(f"\n📁 Fichier manquant: {os.path.abspath(index_path)}")
        print("\n💡 SOLUTION:")
        print("   1. Créez un dossier 'data/' contenant vos images et vidéos")
        print("   2. Exécutez: python extract_embeddings.py")
        print("   3. Puis réessayez votre recherche")
        print("\n" + "="*80)
        raise FileNotFoundError(f"L'index {index_path} n'existe pas. Exécutez d'abord extract_embeddings.py")
    
    if not os.path.exists(metadata_path):
        print("\n" + "="*80)
        print("❌ ERREUR: Les métadonnées n'existent pas encore")
        print("="*80)
        print(f"\n📁 Fichier manquant: {os.path.abspath(metadata_path)}")
        print("\n💡 SOLUTION:")
        print("   1. Créez un dossier 'data/' contenant vos images et vidéos")
        print("   2. Exécutez: python extract_embeddings.py")
        print("   3. Puis réessayez votre recherche")
        print("\n" + "="*80)
        raise FileNotFoundError(f"Les métadonnées {metadata_path} n'existent pas. Exécutez d'abord extract_embeddings.py")
    
    print(f"📂 Chargement de l'index: {index_path}")
    try:
        index = faiss.read_index(index_path)
    except Exception as e:
        print(f"❌ Erreur lors du chargement de l'index: {e}")
        raise
    
    print(f"📂 Chargement des métadonnées: {metadata_path}")
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors du chargement des métadonnées: {e}")
        raise
    
    print(f"✅ Index chargé: {index.ntotal} embedding(s)")
    return index, metadata


def translate_fr2en(query_fr: str) -> str:
    """
    Traduit une requête française en anglais (implémentation locale avec transformers).
    
    Args:
        query_fr: Requête en français
        
    Returns:
        Requête traduite en anglais
    """
    try:
        from transformers import MarianMTModel, MarianTokenizer
        
        # Modèle Helsinki-NLP FR→EN
        model_name = "Helsinki-NLP/opus-mt-fr-en"
        
        # Charger le modèle et tokenizer (lazy loading avec cache)
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        
        # Traduire
        with torch.inference_mode():
            inputs = tokenizer(query_fr, return_tensors="pt", padding=True, truncation=True)
            translated = model.generate(**inputs, max_length=512)
            translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        
        return translated_text.strip()
        
    except Exception as e:
        # En cas d'erreur, retourner la requête originale
        print(f"⚠️  Erreur lors de la traduction: {e}")
        return query_fr


def expand_query(query_fr: str, enable_fr: bool = True, enable_en: bool = True, auto_translate: bool = False) -> List[str]:
    """
    Enrichit la requête avec des variations bilingues (FR/EN) pour améliorer la précision.
    
    Args:
        query_fr: Requête texte originale (français)
        enable_fr: Si True, génère des variantes françaises
        enable_en: Si True, génère des variantes anglaises
        auto_translate: Si True, traduit automatiquement la requête en anglais
        
    Returns:
        Liste de variantes de la requête
    """
    variations = []
    
    # Variantes françaises
    if enable_fr:
        variations.append(query_fr)
        variations.append(f"photo de {query_fr}")
        variations.append(f"image de {query_fr}")
        variations.append(f"vue d'ensemble de {query_fr}")
        variations.append(f"gros plan de {query_fr}")
        variations.append(f"plan large de {query_fr}")
    
    # Variantes anglaises (si traduction activée)
    if enable_en and auto_translate:
        try:
            query_en = translate_fr2en(query_fr)
            if query_en and query_en != query_fr:
                variations.append(query_en)
                variations.append(f"a photo of {query_en}")
                variations.append(f"an image showing {query_en}")
                variations.append(f"a close-up of {query_en}")
                variations.append(f"a wide shot of {query_en}")
        except Exception as e:
            print(f"⚠️  Erreur lors de la traduction pour query expansion: {e}")
    
    # Si aucune variation n'a été générée, retourner au moins la requête originale
    if not variations:
        variations.append(query_fr)
    
    return variations


def compute_dynamic_threshold(cosine_scores: np.ndarray, 
                              k: int = 10, 
                              min_floor: float = 0.25, 
                              max_ceil: float = 0.45) -> float:
    """
    Calcule un seuil dynamique basé sur la distribution des scores.
    
    Args:
        cosine_scores: Array numpy des scores de similarité cosinus
        k: Nombre de meilleurs scores à considérer (défaut: 10)
        min_floor: Seuil minimum (défaut: 0.25)
        max_ceil: Seuil maximum (défaut: 0.45)
        
    Returns:
        Seuil dynamique calculé (clampé entre min_floor et max_ceil)
    """
    if len(cosine_scores) == 0:
        return min_floor
    
    # Prendre les k meilleurs scores (ou tous si moins de k)
    top_k_scores = np.sort(cosine_scores)[::-1][:min(k, len(cosine_scores))]
    
    if len(top_k_scores) == 0:
        return min_floor
    
    # Calculer moyenne et écart-type
    mean_score = np.mean(top_k_scores)
    std_score = np.std(top_k_scores)
    
    # Seuil = mean - std (on veut être un peu en dessous de la moyenne)
    threshold = mean_score - std_score
    
    # Clamper entre min_floor et max_ceil
    threshold = np.clip(threshold, min_floor, max_ceil)
    
    return float(threshold)


def search(query_text: str, 
           index: faiss.Index,
           metadata: List[Dict],
           embedder: CLIPEmbedder,
           top_k: int = 5,
           use_query_expansion: bool = True,
           auto_translate: bool = False,
           use_dynamic_threshold: bool = False,
           fixed_threshold: float = 0.3,
           always_rerank: bool = False,
           rerank_if_below: Optional[float] = None,
           reranker: Optional[CrossEncoderReranker] = None,
           use_captions: bool = True,
           filtered_indices: Optional[List[int]] = None,
           media_type: Optional[str] = None,
           date_range: Optional[Tuple] = None,
           include_dirs: Optional[List[str]] = None) -> List[Dict]:
    """
    Recherche les médias les plus pertinents pour une requête texte.
    
    Args:
        query_text: Requête texte (français)
        index: Index FAISS
        metadata: Liste des métadonnées
        embedder: Instance de CLIPEmbedder
        top_k: Nombre de résultats à retourner
        use_query_expansion: Si True, utilise la query expansion bilingue
        auto_translate: Si True, traduit automatiquement la requête en anglais pour expansion
        use_dynamic_threshold: Si True, utilise un seuil dynamique
        fixed_threshold: Seuil fixe si use_dynamic_threshold=False
        always_rerank: Si True, applique toujours le rerank
        rerank_if_below: Si non-None et best_cosine < rerank_if_below, applique rerank
        reranker: Instance de CrossEncoderReranker (optionnel)
        use_captions: Si True, utilise les captions pour le rerank
        filtered_indices: Liste d'indices à considérer (pour filtres pré-FAISS)
        media_type: Type de média à filtrer ('image', 'video', ou None)
        date_range: Tuple (date_debut, date_fin) pour filtrer par date
        include_dirs: Liste de dossiers à inclure
        
    Returns:
        Liste de dictionnaires avec "path", "score", "cosine_score", "meta"
    """
    print(f"🔍 Recherche: \"{query_text}\"")
    
    # Encoder la requête texte (avec ou sans expansion)
    print("📝 Encodage de la requête...")
    try:
        if use_query_expansion:
            # Générer des variantes bilingues de la requête
            query_variations = expand_query(
                query_fr=query_text,
                enable_fr=True,
                enable_en=auto_translate,
                auto_translate=auto_translate
            )
            print(f"   🔄 Génération de {len(query_variations)} variantes de la requête...")
            
            # Encoder chaque variante
            query_embeddings = []
            for variation in query_variations:
                try:
                    embedding = embedder.encode_text(variation)
                    query_embeddings.append(embedding)
                except Exception as e:
                    # Si une variante échoue, continuer avec les autres
                    continue
            
            if not query_embeddings:
                # Fallback : utiliser la requête originale
                query_embedding = embedder.encode_text(query_text)
            else:
                # Moyenne des embeddings des variantes (agrégation)
                query_embeddings_array = np.array(query_embeddings)
                mean_embedding = np.mean(query_embeddings_array, axis=0)
                
                # Re-normaliser (important pour cosine similarity)
                norm = np.linalg.norm(mean_embedding)
                if norm > 0:
                    mean_embedding = mean_embedding / norm
                
                query_embedding = mean_embedding
        else:
            # Encoder uniquement la requête originale
            query_embedding = embedder.encode_text(query_text)
        
        # Nettoyage : s'assurer que c'est bien float32 et bien reshapé
        query_embedding = query_embedding.astype('float32')
        query_embedding = query_embedding.reshape(1, -1)
        
        # Vérifier qu'il n'y a pas de NaN ou Inf
        if not np.all(np.isfinite(query_embedding)):
            raise ValueError("L'embedding de la requête contient des valeurs invalides")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'encodage de la requête: {e}")
        raise
    
    # Normaliser la requête pour cosine similarity (si nécessaire)
    faiss.normalize_L2(query_embedding)
    
    # Appliquer les filtres si disponibles
    if filtered_indices is None:
        # Si filtered_indices n'est pas fourni, calculer depuis les filtres
        if media_type is not None or date_range is not None or include_dirs is not None:
            filtered_indices = filter_metadata(
                metadata=metadata,
                media_type=media_type,
                date_range=date_range,
                include_dirs=include_dirs
            )
            print(f"📊 Filtres appliqués: {len(filtered_indices)}/{len(metadata)} indices valides")
    
    # Rechercher dans l'index
    # Si rerank activé, chercher plus de candidats
    search_k = top_k * 3 if (always_rerank or rerank_if_below is not None) else top_k
    print(f"🔎 Recherche des {search_k} résultats les plus pertinents...")
    
    try:
        # Si filtres actifs avec beaucoup d'indices valides, on peut chercher plus
        # Pour l'instant, on fait post-filtrage
        distances, indices = index.search(query_embedding, min(search_k * 2, index.ntotal))
    except Exception as e:
        print(f"❌ Erreur lors de la recherche dans l'index: {e}")
        raise
    
    # Construire les résultats
    candidates = []
    cosine_scores = []
    
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
        # Filtrer les valeurs invalides (NaN, Inf, ou indices hors limites)
        if not np.isfinite(distance) or distance < 0:
            continue
        if idx < 0 or idx >= len(metadata):
            continue
        
        # Appliquer filtres pré-FAISS si disponibles
        if filtered_indices is not None and idx not in filtered_indices:
            continue
        
        meta = metadata[idx]
        file_path = meta.get("file_path", "")
        cosine_score = float(distance)
        
        candidates.append({
            "path": file_path,
            "score": cosine_score,
            "meta": meta
        })
        cosine_scores.append(cosine_score)
    
    # Calculer le seuil (dynamique ou fixe)
    if use_dynamic_threshold and len(cosine_scores) > 0:
        threshold = compute_dynamic_threshold(np.array(cosine_scores))
        print(f"📊 Seuil dynamique calculé: {threshold:.4f}")
        # Si le seuil dynamique est trop élevé, utiliser un minimum plus bas
        if threshold > 0.25:
            threshold = max(0.12, threshold * 0.6)  # Réduire de 40% mais minimum 0.12
            print(f"   🔧 Seuil ajusté à: {threshold:.4f} (trop élevé)")
    else:
        threshold = fixed_threshold
        print(f"📊 Seuil fixe utilisé: {threshold:.4f}")
    
    # Afficher les scores pour debug
    if len(cosine_scores) > 0:
        top_scores = sorted(cosine_scores, reverse=True)[:5]
        print(f"📊 Top 5 scores bruts: {[f'{s:.4f}' for s in top_scores]}")
    
    # Filtrer par seuil
    filtered_candidates = [c for c in candidates if c["score"] >= threshold]
    
    # Si aucun résultat après filtrage, prendre au moins le top 5 même si sous le seuil
    if not filtered_candidates and len(candidates) > 0:
        print(f"⚠️  Aucun résultat au-dessus du seuil {threshold:.4f}, affichage du top 5 quand même")
        filtered_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:5]
    
    # Déterminer si on doit appliquer le rerank
    should_rerank = False
    if always_rerank:
        should_rerank = True
        print("🔄 Rerank forcé (always_rerank=True)")
    elif rerank_if_below is not None and len(filtered_candidates) > 0:
        best_cosine = max(c["score"] for c in filtered_candidates)
        if best_cosine < rerank_if_below:
            should_rerank = True
            print(f"🔄 Rerank activé (best_cosine={best_cosine:.4f} < rerank_if_below={rerank_if_below:.4f})")
    
    # Appliquer le rerank si nécessaire
    if should_rerank and len(filtered_candidates) > 0:
        print("🔄 Re-ranking des résultats avec Cross-Encoder...")
        try:
            if reranker is None:
                reranker = get_reranker()
            
            # Re-scorer les top candidats
            top_rerank = min(10, len(filtered_candidates))
            reranked_results = rerank_results(
                query_text=query_text,
                candidates=filtered_candidates[:top_rerank],
                top_rerank=top_rerank,
                use_captions=use_captions,
                reranker=reranker
            )
            
            # Convertir les résultats rerankés en format Dict avec cosine_score
            results = []
            for r in reranked_results:
                results.append({
                    "path": r["path"],
                    "score": r["score"],  # Score cross-encoder
                    "cosine_score": r.get("cosine_score", 0.0),  # Score FAISS original
                    "meta": r["meta"]
                })
            
            # Trier par score cross-encoder décroissant
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Limiter aux top_k
            results = results[:top_k]
            
            print("✅ Re-ranking terminé")
        except Exception as e:
            print(f"⚠️  Erreur lors du re-ranking: {e}")
            print("   Continuation avec les résultats FAISS originaux")
            # Garder les résultats FAISS originaux
            results = filtered_candidates[:top_k]
    else:
        # Pas de rerank, utiliser les résultats FAISS directement
        results = filtered_candidates[:top_k]
        # Ajouter cosine_score pour compatibilité
        for r in results:
            r["cosine_score"] = r["score"]
    
    return results


def display_results(results: List[Dict]):
    """
    Affiche les résultats de recherche de manière formatée.
    Pour les vidéos, regroupe les frames par fichier et n'affiche chaque vidéo qu'une seule fois
    (avec le meilleur score).
    
    Args:
        results: Liste de dictionnaires avec "path", "score", "cosine_score", "meta"
    """
    if not results:
        print("❌ Aucun résultat trouvé.")
        return
    
    # Grouper les résultats par fichier (pour éviter les doublons de vidéos)
    unique_results = {}
    
    for result in results:
        file_path = result.get("path", "")
        score = result.get("score", 0.0)  # Score principal (rerank ou cosine)
        meta = result.get("meta", {})
        
        # Pour les vidéos, on groupe par fichier et on garde le meilleur score
        # Pour les images, on garde chaque résultat unique
        if meta.get('media_type') == 'video':
            # Si cette vidéo n'a pas encore été vue, ou si ce score est meilleur
            if file_path not in unique_results or score > unique_results[file_path]["score"]:
                unique_results[file_path] = result
        else:
            # Pour les images, on peut avoir le même fichier plusieurs fois (avec multi-scale)
            # On garde le meilleur score pour chaque fichier
            if file_path not in unique_results or score > unique_results[file_path]["score"]:
                unique_results[file_path] = result
    
    # Convertir en liste et trier par score décroissant
    unique_results_list = list(unique_results.values())
    unique_results_list.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    
    print("\n" + "="*80)
    print("📊 RÉSULTATS DE LA RECHERCHE")
    print("="*80)
    
    for i, result in enumerate(unique_results_list, 1):
        file_path = result.get("path", "")
        score = result.get("score", 0.0)
        cosine_score = result.get("cosine_score", score)
        meta = result.get("meta", {})
        
        print(f"\n{i}. {os.path.basename(file_path)}")
        print(f"   📍 Chemin: {file_path}")
        # Afficher les deux scores si rerank activé
        if abs(score - cosine_score) > 0.001:
            print(f"   📊 Score Cross-Encoder: {score:.4f} | Score FAISS: {cosine_score:.4f}")
        else:
            print(f"   📊 Score de similarité: {score:.4f} (cosine similarity)")
        print(f"   🎬 Type: {meta.get('media_type', 'unknown')}")
        if meta.get('media_type') == 'video':
            print(f"   🎞️  Vidéo (meilleure frame sélectionnée)")
    
    print("\n" + "="*80)


def search_by_text(query_text: str,
                   index_path: str = "index.faiss",
                   metadata_path: str = "metadata.json",
                   top_k: int = 5,
                   model_name: str = "openai/clip-vit-large-patch14",
                   embedder: CLIPEmbedder = None,
                   use_query_expansion: bool = True,
                   auto_translate: bool = False,
                   use_dynamic_threshold: bool = False,
                   fixed_threshold: float = 0.3,
                   always_rerank: bool = False,
                   rerank_if_below: Optional[float] = None,
                   use_reranking: bool = True,
                   use_captions: bool = True) -> List[Dict]:
    """
    Fonction principale pour rechercher dans les médias.
    
    Args:
        query_text: Requête texte (français)
        index_path: Chemin vers l'index FAISS
        metadata_path: Chemin vers les métadonnées
        top_k: Nombre de résultats à retourner
        model_name: Nom du modèle CLIP
        embedder: Instance de CLIPEmbedder (optionnel, sera créé si None)
        use_query_expansion: Si True, utilise la query expansion bilingue
        auto_translate: Si True, traduit automatiquement la requête en anglais
        use_dynamic_threshold: Si True, utilise un seuil dynamique
        fixed_threshold: Seuil fixe si use_dynamic_threshold=False
        always_rerank: Si True, applique toujours le rerank
        rerank_if_below: Si non-None et best_cosine < rerank_if_below, applique rerank
        use_reranking: Si True, active le rerank (déprécié, utiliser always_rerank ou rerank_if_below)
        use_captions: Si True, utilise les captions pour le rerank
        
    Returns:
        Liste de dictionnaires avec "path", "score", "cosine_score", "meta"
    """
    # Charger l'index et les métadonnées
    index, metadata = load_index_and_metadata(index_path, metadata_path)
    
    # Initialiser l'embedder si nécessaire
    if embedder is None:
        try:
            from .clip_utils import get_embedder
            embedder = get_embedder(model_name=model_name)
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            raise
    
    # Compatibilité avec ancienne API
    if use_reranking and not always_rerank and rerank_if_below is None:
        always_rerank = True
    
    # Effectuer la recherche
    results = search(
        query_text=query_text,
        index=index,
        metadata=metadata,
        embedder=embedder,
        top_k=top_k,
        use_query_expansion=use_query_expansion,
        auto_translate=auto_translate,
        use_dynamic_threshold=use_dynamic_threshold,
        fixed_threshold=fixed_threshold,
        always_rerank=always_rerank,
        rerank_if_below=rerank_if_below,
        use_captions=use_captions
    )
    
    # Vérifier si aucun résultat après filtrage
    if not results:
        print("\n" + "="*80)
        print("⚠️  AUCUN RÉSULTAT PERTINENT")
        print("="*80)
        print(f"Aucun résultat pertinent trouvé pour cette requête.")
        print("Essayez de reformuler votre requête ou de réduire le seuil de similarité.")
        print("="*80 + "\n")
    else:
        # Afficher les résultats
        display_results(results)
    
    return results
