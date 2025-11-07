"""
Module utilitaire pour l'extraction d'embeddings avec CLIP.
Fournit des fonctions réutilisables pour encoder des images et du texte.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

import numpy as np
from PIL import Image
from typing import Union, List
import warnings

# Désactiver les warnings pour éviter le bruit
warnings.filterwarnings("ignore", category=UserWarning)

# Import transformers APRÈS torch
from transformers import CLIPProcessor, CLIPModel


class CLIPEmbedder:
    """Classe pour gérer l'extraction d'embeddings CLIP."""
    
    def __init__(self, model_name: str = "openai/clip-vit-large-patch14", device: str = None):
        """
        Initialise le modèle CLIP.
        
        Args:
            model_name: Nom du modèle CLIP à utiliser
            device: Device à utiliser ('cuda', 'cpu', ou None pour auto-détection)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.model_name = model_name
        
        print(f"📦 Chargement du modèle CLIP: {model_name}")
        print(f"🔧 Device: {device}")
        
        try:
            # Charger le modèle avec des paramètres sécurisés
            self.model = CLIPModel.from_pretrained(
                model_name,
                dtype=torch.float32,  # Forcer float32 pour compatibilité CoreML
                low_cpu_mem_usage=True
            ).to(device)
            self.processor = CLIPProcessor.from_pretrained(model_name, use_fast=False)
            
            # Mode évaluation
            self.model.eval()
            
            # Désactiver le gradient pour éviter les problèmes
            for param in self.model.parameters():
                param.requires_grad = False
                
            print(f"✅ Modèle CLIP chargé avec succès")
                
        except Exception as e:
            raise RuntimeError(f"❌ Erreur lors du chargement du modèle CLIP: {e}")
        
    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode une image PIL en embedding.
        
        Args:
            image: Image PIL à encoder
            
        Returns:
            Array numpy de l'embedding (normalisé, float32, shape plat)
        """
        try:
            # Utiliser inference_mode pour meilleure performance et stabilité
            with torch.inference_mode():
                # S'assurer que l'image est valide
                if image is None or image.size[0] == 0 or image.size[1] == 0:
                    raise ValueError("Image invalide")
                
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                image_features = self.model.get_image_features(**inputs)
                # Normalisation L2
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                # Convertir en numpy avant de retourner (float32, forme plate)
                result = image_features.cpu().numpy().flatten().astype('float32')
                # S'assurer que le résultat est valide
                if result is None or len(result) == 0:
                    raise ValueError("Embedding vide")
                return result
        except Exception as e:
            # Si erreur, essayer avec no_grad comme fallback
            try:
                with torch.no_grad():
                    inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                    image_features = self.model.get_image_features(**inputs)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    result = image_features.cpu().numpy().flatten().astype('float32')
                    if result is None or len(result) == 0:
                        raise ValueError("Embedding vide")
                    return result
            except Exception as e2:
                raise RuntimeError(f"Erreur lors de l'encodage de l'image: {e2}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode un texte en embedding.
        
        Args:
            text: Texte à encoder
            
        Returns:
            Array numpy de l'embedding (normalisé, float32, shape plat)
        """
        with torch.inference_mode():
            inputs = self.processor(text=text, return_tensors="pt", padding=True, truncation=True).to(self.device)
            text_features = self.model.get_text_features(**inputs)
            # Normalisation L2
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            # Convertir en float32, forme plate pour compatibilité
            return text_features.cpu().numpy().flatten().astype('float32')
    
    def encode_images_batch(self, images: List[Image.Image]) -> np.ndarray:
        """
        Encode un batch d'images en embeddings.
        
        Args:
            images: Liste d'images PIL à encoder
            
        Returns:
            Array numpy de shape (n_images, embedding_dim) en float32
        """
        with torch.inference_mode():
            inputs = self.processor(images=images, return_tensors="pt").to(self.device)
            image_features = self.model.get_image_features(**inputs)
            # Normalisation L2
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().numpy().astype('float32')


def get_embedder(model_name: str = "openai/clip-vit-large-patch14", device: str = None) -> CLIPEmbedder:
    """
    Factory function pour obtenir un CLIPEmbedder.
    
    Args:
        model_name: Nom du modèle CLIP
        device: Device à utiliser
        
    Returns:
        Instance de CLIPEmbedder
    """
    return CLIPEmbedder(model_name=model_name, device=device)

