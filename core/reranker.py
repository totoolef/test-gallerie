"""
Module de re-ranking avec Cross-Encoder pour améliorer la précision des résultats.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

from typing import List, Tuple, Dict, Optional
import warnings

# Désactiver les warnings pour éviter le bruit
warnings.filterwarnings("ignore", category=UserWarning)

# Import sentence_transformers APRÈS torch
from sentence_transformers import CrossEncoder


# Singleton global pour le reranker
_reranker_instance = None

class CrossEncoderReranker:
    """Classe pour re-scorer les résultats avec un Cross-Encoder."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = None):
        """
        Initialise le modèle Cross-Encoder pour le re-ranking.
        
        Args:
            model_name: Nom du modèle Cross-Encoder à utiliser
            device: Device à utiliser ('cuda', 'cpu', ou None pour auto-détection)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.model_name = model_name
        self._model = None
        
    def _load_model(self):
        """Charge le modèle Cross-Encoder de manière lazy (seulement quand nécessaire)."""
        if self._model is None:
            print(f"📦 Chargement du modèle Cross-Encoder: {self.model_name}")
            print(f"🔧 Device: {self.device}")
            
            try:
                self._model = CrossEncoder(model_name=self.model_name, device=self.device)
                print(f"✅ Modèle Cross-Encoder chargé avec succès")
                    
            except Exception as e:
                raise RuntimeError(f"❌ Erreur lors du chargement du modèle Cross-Encoder: {e}")
    
    def rerank_results(self, 
                       query_text: str, 
                       candidates: List[Dict], 
                       top_rerank: int = 10,
                       use_captions: bool = True) -> List[Dict]:
        """
        Re-score les résultats candidats en comparant la requête avec le contenu de l'image.
        
        Args:
            query_text: Requête texte originale
            candidates: Liste de dictionnaires avec "path", "score", "meta"
            top_rerank: Nombre de candidats à re-scorer (défaut: 10)
            use_captions: Si True, utilise les captions en priorité (défaut: True)
            
        Returns:
            Liste de dictionnaires re-scorés avec "path", "score" (cross-encoder), "cosine_score" (original), "meta"
        """
        if not candidates:
            return []
        
        # Charger le modèle si nécessaire
        self._load_model()
        
        # Limiter aux top_rerank premiers candidats
        candidates_to_rerank = candidates[:top_rerank]
        
        try:
            # Préparer les paires (query_text, context) pour chaque candidat
            pairs = []
            valid_candidates = []
            
            for candidate in candidates_to_rerank:
                # Extraire le contexte (caption ou nom de fichier)
                context = ""
                
                if use_captions:
                    # Priorité: caption généré > nom de fichier propre
                    caption = candidate.get("meta", {}).get("caption", "")
                    if caption and caption.strip() and caption.strip().lower() != "unknown":
                        context = caption.strip()
                    else:
                        # Fallback: nom de fichier nettoyé
                        import os
                        filename = os.path.basename(candidate.get("path", ""))
                        context = filename.replace("_", " ").replace("-", " ").replace(".jpg", "").replace(".png", "").replace(".jpeg", "").replace(".mp4", "").replace(".mov", "")
                else:
                    # Utiliser uniquement le nom de fichier
                    import os
                    filename = os.path.basename(candidate.get("path", ""))
                    context = filename.replace("_", " ").replace("-", " ").replace(".jpg", "").replace(".png", "").replace(".jpeg", "").replace(".mp4", "").replace(".mov", "")
                
                if not context:
                    context = "image"
                
                # Créer la paire (query, context)
                pairs.append([query_text, context])
                valid_candidates.append(candidate)
            
            if not pairs:
                return []
            
            # Calculer les scores avec le Cross-Encoder
            with torch.inference_mode():
                scores = self._model.predict(pairs)
            
            # Convertir en liste de scores et gérer les NaN/Inf
            import numpy as np
            if isinstance(scores, np.ndarray):
                # Remplacer NaN/Inf par 0.0
                scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)
            cross_scores = [float(s) if np.isfinite(s) else 0.0 for s in scores]
            
            # Construire les résultats re-scorés
            # On conserve le score cosinus original pour affichage
            reranked_results = []
            for i, candidate in enumerate(valid_candidates):
                cross_score = cross_scores[i] if i < len(cross_scores) else 0.0
                
                reranked_results.append({
                    "path": candidate.get("path"),
                    "score": cross_score,  # Score cross-encoder (pour tri)
                    "cosine_score": candidate.get("score", 0.0),  # Score FAISS original (pour affichage)
                    "meta": candidate.get("meta", {})
                })
            
            # Trier par score cross-encoder décroissant
            reranked_results.sort(key=lambda x: x["score"], reverse=True)
            
            return reranked_results
            
        except Exception as e:
            # En cas d'erreur, retourner les résultats originaux avec structure Dict
            print(f"⚠️  Erreur lors du re-ranking: {e}")
            print("   Retour des résultats originaux (sans re-ranking)")
            # Convertir les candidats en format Dict
            fallback_results = []
            for candidate in candidates_to_rerank:
                fallback_results.append({
                    "path": candidate.get("path"),
                    "score": candidate.get("score", 0.0),
                    "cosine_score": candidate.get("score", 0.0),
                    "meta": candidate.get("meta", {})
                })
            return sorted(fallback_results, key=lambda x: x["score"], reverse=True)


def get_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = None) -> CrossEncoderReranker:
    """
    Factory function pour obtenir un CrossEncoderReranker (singleton).
    
    Args:
        model_name: Nom du modèle Cross-Encoder
        device: Device à utiliser
    
    Returns:
        Instance de CrossEncoderReranker (singleton)
    """
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker(model_name=model_name, device=device)
    return _reranker_instance


def rerank_results(query_text: str, 
                   candidates: List[Dict], 
                   top_rerank: int = 10,
                   use_captions: bool = True,
                   reranker: Optional[CrossEncoderReranker] = None) -> List[Dict]:
    """
    Fonction utilitaire pour re-scorer les résultats.
    
    Args:
        query_text: Requête texte originale
        candidates: Liste de dictionnaires avec "path", "score", "meta"
        top_rerank: Nombre de candidats à re-scorer (défaut: 10)
        use_captions: Si True, utilise les captions en priorité (défaut: True)
        reranker: Instance de CrossEncoderReranker (optionnel, sera créé si None)
        
    Returns:
        Liste de dictionnaires re-scorés avec "path", "score", "cosine_score", "meta"
    """
    if reranker is None:
        reranker = get_reranker()
    
    return reranker.rerank_results(query_text, candidates, top_rerank, use_captions)

