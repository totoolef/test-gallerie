"""
Fonctions utilitaires pour l'interface Streamlit.
"""

import os
import subprocess
import hashlib
from pathlib import Path
from typing import Optional
from PIL import Image
import streamlit as st


def pick_directory() -> Optional[str]:
    """
    Ouvre un sélecteur de dossier macOS et renvoie le chemin sélectionné.
    Utilise osascript pour utiliser le sélecteur natif macOS.
    
    Returns:
        Chemin du dossier sélectionné, ou None si annulé
    """
    try:
        # Méthode 1: Utiliser osascript (plus fiable sur macOS)
        import platform
        if platform.system() == "Darwin":  # macOS
            script = '''
                tell application "System Events"
                    activate
                    set folderPath to choose folder with prompt "Sélectionnez un dossier à indexer"
                    return POSIX path of folderPath
                end tell
            '''
            try:
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60
                )
                directory = result.stdout.strip()
                if directory:
                    return directory
            except subprocess.TimeoutExpired:
                st.warning("⏱️ Sélection de dossier annulée (timeout)")
                return None
            except subprocess.CalledProcessError:
                # L'utilisateur a peut-être annulé
                return None
            except Exception as e:
                # Si osascript échoue, essayer tkinter
                pass
        
        # Méthode 2: Fallback sur tkinter
        import tkinter as tk
        from tkinter import filedialog
        
        # Créer une fenêtre racine cachée
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale
        root.attributes('-topmost', True)  # Mettre au premier plan
        
        # Ouvrir le dialogue de sélection de dossier
        directory = filedialog.askdirectory(title="Sélectionner un dossier")
        
        root.destroy()
        
        return directory if directory else None
        
    except ImportError:
        # tkinter n'est pas disponible
        st.warning("⚠️ tkinter n'est pas disponible. Utilisez le champ de saisie ci-dessous.")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lors de la sélection du dossier: {e}")
        import traceback
        st.error(f"Détails: {traceback.format_exc()}")
        return None


def pick_directory_osascript() -> Optional[str]:
    """
    Ouvre un sélecteur de dossier macOS en utilisant osascript (plus fiable).
    
    Returns:
        Chemin du dossier sélectionné, ou None si annulé
    """
    try:
        script = '''
            tell application "System Events"
                activate
                set folderPath to choose folder with prompt "Sélectionnez un dossier à indexer"
                return POSIX path of folderPath
            end tell
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        directory = result.stdout.strip()
        return directory if directory else None
    except subprocess.TimeoutExpired:
        return None
    except subprocess.CalledProcessError:
        # L'utilisateur a annulé
        return None
    except Exception as e:
        return None


def get_file_hash(file_path: str) -> str:
    """
    Calcule un hash du fichier basé sur le chemin et le mtime.
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Hash du fichier
    """
    try:
        stat = os.stat(file_path)
        # Combiner chemin et mtime pour le hash
        content = f"{file_path}:{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()
    except Exception:
        # Fallback: utiliser juste le chemin
        return hashlib.md5(file_path.encode()).hexdigest()


def make_thumbnail(image_path: str, max_size: int = 512, cache_dir: str = ".cache/thumbnails") -> Optional[Image.Image]:
    """
    Crée ou charge une vignette depuis le cache.
    
    Args:
        image_path: Chemin vers l'image
        max_size: Taille maximale de la vignette (défaut: 512)
        cache_dir: Dossier de cache pour les vignettes
        
    Returns:
        Image PIL (vignette) ou None en cas d'erreur
    """
    try:
        # Créer le dossier de cache si nécessaire
        os.makedirs(cache_dir, exist_ok=True)
        
        # Générer le nom de fichier de cache
        file_hash = get_file_hash(image_path)
        cache_path = os.path.join(cache_dir, f"{file_hash}.jpg")
        
        # Vérifier si la vignette existe déjà dans le cache
        if os.path.exists(cache_path):
            try:
                return Image.open(cache_path)
            except Exception:
                # Si le fichier est corrompu, le recréer
                pass
        
        # Créer la vignette
        if not os.path.exists(image_path):
            return None
        
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Redimensionner en gardant le ratio
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Sauvegarder dans le cache
        try:
            image.save(cache_path, 'JPEG', quality=85)
        except Exception:
            pass  # Si la sauvegarde échoue, continuer quand même
        
        return image
        
    except Exception as e:
        # En cas d'erreur, retourner None
        return None


def get_video_preview(video_path: str, cache_dir: str = ".cache/thumbnails") -> Optional[Image.Image]:
    """
    Extrait une frame de prévisualisation d'une vidéo.
    
    Args:
        video_path: Chemin vers la vidéo
        cache_dir: Dossier de cache pour les previews
        
    Returns:
        Image PIL (première frame) ou None en cas d'erreur
    """
    try:
        import cv2
        
        # Créer le dossier de cache si nécessaire
        os.makedirs(cache_dir, exist_ok=True)
        
        # Générer le nom de fichier de cache
        file_hash = get_file_hash(video_path)
        cache_path = os.path.join(cache_dir, f"{file_hash}_video.jpg")
        
        # Vérifier si la preview existe déjà dans le cache
        if os.path.exists(cache_path):
            try:
                return Image.open(cache_path)
            except Exception:
                pass
        
        # Extraire la première frame
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        # Convertir en RGB pour PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        
        # Redimensionner pour la preview
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        
        # Sauvegarder dans le cache
        try:
            image.save(cache_path, 'JPEG', quality=85)
        except Exception:
            pass
        
        return image
        
    except Exception as e:
        return None


def open_in_finder(file_path: str) -> bool:
    """
    Ouvre le fichier dans Finder (macOS).
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        True si succès, False sinon
    """
    try:
        if not os.path.exists(file_path):
            return False
        
        # Utiliser 'open -R' pour révéler le fichier dans Finder
        subprocess.run(["open", "-R", file_path], check=True)
        return True
    except Exception as e:
        return False


def human_readable_score(score: float) -> str:
    """
    Formate le score cosinus de manière lisible.
    
    Args:
        score: Score cosinus (0-1)
        
    Returns:
        Score formaté en pourcentage avec barre de progression visuelle
    """
    percentage = int(score * 100)
    # Barre de progression simple
    filled = "█" * (percentage // 5)
    empty = "░" * (20 - len(filled))
    return f"{percentage}% {filled}{empty}"


def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier en format lisible.
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        Taille formatée (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

