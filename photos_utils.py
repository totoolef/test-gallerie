"""
Utilitaires pour accéder aux photos et vidéos depuis l'app Photos du Mac.
"""

import os
import subprocess
import json
from typing import List, Tuple
from pathlib import Path


def get_photos_library_path() -> str:
    """
    Retourne le chemin vers la bibliothèque Photos par défaut.
    
    Returns:
        Chemin vers la bibliothèque Photos
    """
    # Chemin par défaut de Photos sur macOS
    photos_lib = os.path.expanduser("~/Pictures/Photos Library.photoslibrary")
    
    if os.path.exists(photos_lib):
        return photos_lib
    
    # Essayer d'autres emplacements possibles
    possible_paths = [
        os.path.expanduser("~/Pictures/Photos Library.photoslibrary"),
        os.path.expanduser("~/Desktop/Photos Library.photoslibrary"),
        "/Users/Shared/Photos Library.photoslibrary"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def get_photos_from_applescript() -> List[str]:
    """
    Récupère les chemins des photos et vidéos depuis l'app Photos via AppleScript.
    
    Returns:
        Liste des chemins vers les fichiers média
    """
    script = """
    tell application "Photos"
        activate
        set mediaItems to every media item
        set filePaths to {}
        
        repeat with aMediaItem in mediaItems
            try
                set hfsPath to (path of aMediaItem)
                set posixPath to POSIX path of hfsPath
                copy posixPath to end of filePaths
            end try
        end repeat
        
        return filePaths
    end tell
    """
    
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            # Les chemins sont retournés ligne par ligne
            paths = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            # Filtrer les chemins valides
            valid_paths = [p for p in paths if os.path.exists(p)]
            return valid_paths
        else:
            print(f"⚠️  Erreur AppleScript: {result.stderr}")
            return []
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout lors de l'accès à Photos")
        return []
    except Exception as e:
        print(f"⚠️  Erreur lors de l'accès à Photos: {e}")
        return []


def get_photos_from_library() -> List[str]:
    """
    Récupère les photos et vidéos depuis la bibliothèque Photos en accédant directement aux fichiers.
    
    Note: La bibliothèque Photos est un "package" qui contient des fichiers organisés.
    Sur macOS, on peut accéder aux originaux via le package.
    
    Returns:
        Liste des chemins vers les fichiers média
    """
    photos_lib = get_photos_library_path()
    
    if not photos_lib:
        print("⚠️  Bibliothèque Photos non trouvée")
        return []
    
    media_files = []
    
    # Dans Photos Library, les fichiers sont organisés dans:
    # - originals/ (pour les originaux)
    # - masters/ (ancien format)
    
    # Chemin vers le package Photos
    originals_path = os.path.join(photos_lib, "originals")
    masters_path = os.path.join(photos_lib, "Masters")
    
    # Extensions supportées
    image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif', '.gif', '.webp'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.3gp', '.flv', '.wmv', '.webm'}
    
    all_extensions = image_extensions | video_extensions
    
    # Parcourir les originaux
    if os.path.exists(originals_path):
        for root, dirs, files in os.walk(originals_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                if ext in all_extensions:
                    media_files.append(file_path)
    
    # Parcourir les masters (ancien format)
    if os.path.exists(masters_path):
        for root, dirs, files in os.walk(masters_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                if ext in all_extensions:
                    if file_path not in media_files:  # Éviter les doublons
                        media_files.append(file_path)
    
    return media_files


def get_photos_via_export() -> List[str]:
    """
    Exporte temporairement les photos depuis Photos via AppleScript pour obtenir les chemins.
    
    Returns:
        Liste des chemins vers les fichiers média exportés temporairement
    """
    # Créer un dossier temporaire pour l'export
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix="photos_export_")
    
    script = f"""
    tell application "Photos"
        activate
        set mediaItems to every media item
        try
            export mediaItems to POSIX file "{temp_dir}" with using originals
            return (count of mediaItems)
        on error errMsg number errNum
            return "ERROR:" & errNum & ":" & errMsg
        end try
    end tell
    """
    
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        if result.returncode == 0 and not result.stdout.strip().startswith("ERROR:"):
            media_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    media_files.append(file_path)
            return media_files, temp_dir
        else:
            if result.stdout.strip().startswith("ERROR:"):
                print(f"⚠️  Erreur AppleScript: {result.stdout.strip()}")
            else:
                print(f"⚠️  Erreur AppleScript: {result.stderr}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return [], None
    except Exception as e:
        print(f"⚠️  Erreur lors de l'export: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return [], None


def get_photos_from_photos_app() -> Tuple[List[str], int, int]:
    """
    Récupère les photos et vidéos depuis l'app Photos du Mac.
    Essaie plusieurs méthodes.
    
    Returns:
        Tuple (liste des chemins, nombre d'images, nombre de vidéos)
    """
    print("📸 Récupération des médias depuis l'app Photos...")
    
    # Méthode 1: Accès direct à la bibliothèque (plus rapide)
    media_files = get_photos_from_library()
    
    # Méthode 2: AppleScript (chemins) si l'accès direct ne retourne rien
    if not media_files:
        print("   ⚠️  Méthode 1 échouée, essai avec AppleScript (chemins)...")
        media_files = get_photos_from_applescript()

    # Méthode 3: Export AppleScript (robuste) si toujours vide
    if not media_files:
        print("   ⚠️  Chemins introuvables, tentative d'export temporaire depuis Photos...")
        exported_files, temp_dir = get_photos_via_export()
        if exported_files:
            media_files = exported_files
            print(f"   ✅ Export temporaire réussi vers {temp_dir} ({len(media_files)} fichiers)")
        else:
            print("   ⚠️  Aucun média trouvé. Vérifiez les permissions d'accès.")
            return [], 0, 0
    
    # Séparer images et vidéos
    image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif', '.gif', '.webp'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.3gp', '.flv', '.wmv', '.webm'}
    
    images = []
    videos = []
    
    for file_path in media_files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in image_extensions:
            images.append(file_path)
        elif ext in video_extensions:
            videos.append(file_path)
    
    print(f"   ✅ Trouvé {len(images)} image(s) et {len(videos)} vidéo(s)")
    
    return media_files, len(images), len(videos)


def diagnose_photos_access() -> dict:
    """
    Diagnostique les différentes méthodes d'accès à Photos et retourne un rapport.
    """
    report = {
        "library_path": get_photos_library_path(),
        "direct_count": 0,
        "applescript_count": 0,
        "export_count": 0,
        "export_dir": None,
        "errors": []
    }
    try:
        direct = get_photos_from_library()
        report["direct_count"] = len(direct)
    except Exception as e:
        report["errors"].append(f"direct: {e}")
    try:
        aps = get_photos_from_applescript()
        report["applescript_count"] = len(aps)
    except Exception as e:
        report["errors"].append(f"applescript: {e}")
    try:
        exp, tmp = get_photos_via_export()
        report["export_count"] = len(exp)
        report["export_dir"] = tmp
    except Exception as e:
        report["errors"].append(f"export: {e}")
    return report

