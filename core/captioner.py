"""
Module de génération de légendes automatiques pour les images avec BLIP.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

from typing import Optional
from PIL import Image
import warnings

# Désactiver les warnings pour éviter le bruit
warnings.filterwarnings("ignore", category=UserWarning)

# Import transformers APRÈS torch
from transformers import BlipProcessor, BlipForConditionalGeneration


# Singleton global pour le captioner
_captioner_instance = None


class BLIPCaptioner:
    """Classe pour générer des légendes automatiques avec BLIP."""
    
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base", device: str = None):
        """
        Initialise le modèle BLIP pour la génération de légendes.
        
        Args:
            model_name: Nom du modèle BLIP à utiliser
            device: Device à utiliser ('cuda', 'cpu', ou None pour auto-détection)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.model_name = model_name
        self._processor = None
        self._model = None
        
    def _load_model(self):
        """Charge le modèle BLIP de manière lazy (seulement quand nécessaire)."""
        if self._model is None:
            print(f"📦 Chargement du modèle BLIP: {self.model_name}")
            print(f"🔧 Device: {self.device}")
            
            try:
                self._processor = BlipProcessor.from_pretrained(self.model_name)
                self._model = BlipForConditionalGeneration.from_pretrained(
                    self.model_name,
                    dtype=torch.float32,
                    low_cpu_mem_usage=True
                ).to(self.device)
                self._model.eval()
                
                # Désactiver le gradient pour éviter les problèmes
                for param in self._model.parameters():
                    param.requires_grad = False
                    
                print(f"✅ Modèle BLIP chargé avec succès")
                    
            except Exception as e:
                raise RuntimeError(f"❌ Erreur lors du chargement du modèle BLIP: {e}")
    
    def generate_caption(self, image: Image.Image, timeout: float = 15.0) -> str:
        """
        Génère une légende automatique pour une image.
        
        Args:
            image: Image PIL à décrire
            timeout: Timeout en secondes (défaut: 5.0)
            
        Returns:
            Légende générée (texte) ou "unknown" si erreur/timeout
        """
        # Charger le modèle si nécessaire
        self._load_model()
        
        try:
            # S'assurer que l'image est valide
            if image is None or image.size[0] == 0 or image.size[1] == 0:
                return "unknown"
            
            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Générer la légende avec gestion de timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Timeout lors de la génération de la légende")
            
            # Sur macOS/Linux, utiliser signal pour timeout
            old_handler = None
            try:
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(timeout))
                
                with torch.inference_mode():
                    inputs = self._processor(image, return_tensors="pt").to(self.device)
                    # Augmenter légèrement les paramètres pour de meilleures légendes sur CPU
                    out = self._model.generate(**inputs, max_length=60, min_length=5, num_beams=4, no_repeat_ngram_size=2)
                    caption = self._processor.decode(out[0], skip_special_tokens=True)
                    
                    result = caption.strip()
                    
                    # Annuler l'alarme si succès
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
                    
                    # Si BLIP renvoie quelque chose de non vide et valide, on le garde
                    if result and result.strip() and len(result.strip()) >= 3:
                        # Vérifier que ce n'est pas juste "unknown" ou des mots vides
                        result_lower = result.strip().lower()
                        if result_lower not in ['unknown', 'error', '']:
                            return result.strip()
                    return "unknown"
            except (TimeoutError, Exception) as e:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                return "unknown"
                
        except Exception as e:
            # En cas d'erreur, retourner "unknown"
            return "unknown"


def get_captioner(model_name: str = "Salesforce/blip-image-captioning-base", device: str = None) -> BLIPCaptioner:
    """
    Factory function pour obtenir un BLIPCaptioner (singleton).
    
    Args:
        model_name: Nom du modèle BLIP
        device: Device à utiliser
    
    Returns:
        Instance de BLIPCaptioner (singleton)
    """
    global _captioner_instance
    if _captioner_instance is None:
        _captioner_instance = BLIPCaptioner(model_name=model_name, device=device)
    return _captioner_instance

